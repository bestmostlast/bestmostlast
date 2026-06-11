#!/usr/bin/env python3
"""
Generate voiceover for a WC26 match short using edge-tts (free, no API key).

Each sentence is rendered separately then joined with 2.5s silence gaps via ffmpeg,
so pauses are actual silence — not narrated XML tags.

Usage:
  python3 scripts/wc26/gen_narration.py --slug m001-mexico-vs-south-africa [--post]

Writes: scripts/wc26/shorts/<slug>/export/narration.mp3
"""

import argparse, csv, json, os, sys, asyncio, subprocess, tempfile
from pathlib import Path

HERE    = Path(__file__).parent
RESULTS = HERE / 'data' / 'results.csv'
SHORTS  = HERE / 'shorts'

EDGE_VOICE  = 'en-US-GuyNeural'
PAUSE_SECS  = 2.5   # silence between sentences
SPEECH_RATE = '+5%' # slightly faster than default

# Load .env.wc26
_env = HERE / '.env.wc26'
if _env.exists():
    for line in _env.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, _, v = line.partition('=')
            os.environ.setdefault(k.strip(), v.strip())

def load_results():
    if not RESULTS.exists():
        return {}
    return {r['slug']: r for r in csv.DictReader(open(RESULTS))}

def deepseek_sentences(prompt):
    api_key = os.environ.get('DEEPSEEK_API_KEY')
    if not api_key:
        return None
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url='https://api.deepseek.com')
    resp = client.chat.completions.create(
        model='deepseek-chat',
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=400,
        response_format={'type': 'json_object'},
    )
    try:
        data = json.loads(resp.choices[0].message.content.strip())
        return data.get('sentences', [])
    except Exception:
        return None

def build_post_sentences(row):
    team_a    = row['team_a']
    team_b    = row['team_b']
    score_a   = row['score_a']
    score_b   = row['score_b']
    group     = row.get('group', '')
    scorers_a = row.get('scorers_a', '').strip()
    scorers_b = row.get('scorers_b', '').strip()
    shots_a   = row.get('shots_a', '')
    shots_b   = row.get('shots_b', '')
    poss_a    = row.get('poss_a', '')
    yellow_a  = row.get('yellow_a', '0')
    yellow_b  = row.get('yellow_b', '0')
    red_a     = row.get('red_a', '0')
    red_b     = row.get('red_b', '0')

    try:
        poss_b = round(100 - float(poss_a)) if poss_a else ''
    except Exception:
        poss_b = ''

    prompt = f"""You write spoken narration for 25-second YouTube Shorts about football matches.

Match data:
- {team_a} {score_a}–{score_b} {team_b} | Group {group} | WC2026
- Scorers: {team_a}: {scorers_a or 'none'} | {team_b}: {scorers_b or 'none'}
- Shots: {shots_a}–{shots_b} | Possession: {poss_a}%–{poss_b}%
- Cards: {team_a} Y{yellow_a} R{red_a} | {team_b} Y{yellow_b} R{red_b}

Write EXACTLY 6 sentences for a sports broadcaster to read aloud:
1. Competition context — group, tournament name
2. The final result — announce it naturally like a commentator
3. First goal — scorer full name, minute, any drama
4. Second goal or key moment — if no second goal, describe the best chance or turning point
5. Stats — shots and possession as a punchy one-liner
6. Editorial close — what this result means for the group standings

Rules:
- Natural spoken English only — no abbreviations, no slash notation
- Say "scored in the 67th minute" not "67'"
- Each sentence 10–18 words — long enough to fill time but punchy
- No sentence should start with "And"

Respond ONLY in this exact JSON:
{{"sentences": ["s1","s2","s3","s4","s5","s6"]}}"""

    sentences = deepseek_sentences(prompt)
    if sentences and len(sentences) >= 4:
        return sentences

    # fallback
    winner = team_a if int(score_a) > int(score_b) else (team_b if int(score_b) > int(score_a) else None)
    return [s for s in [
        f"Group {group}, World Cup 2026.",
        f"{team_a} {score_a}, {team_b} {score_b} — full time.",
        f"Goals from {scorers_a.replace('/',' and ')}." if scorers_a else f"{team_a} were clinical in front of goal.",
        f"{scorers_b.replace('/',' and ')} replied for {team_b}." if scorers_b else f"{team_b} struggled to create clear chances.",
        f"{shots_a} shots to {shots_b}, with {team_a} controlling {poss_a} percent of possession." if shots_a else "The stats told the story of the match.",
        f"{winner} take three points and move to the top of Group {group}." if winner else f"A point each — honours even in Group {group}.",
    ] if s]

def build_pre_sentences(slug):
    parts = slug.split('-vs-')
    if len(parts) == 2:
        team_a = parts[0].split('-', 1)[1].replace('-', ' ').title()
        team_b = parts[1].replace('-', ' ').title()

        prompt = f"""You write spoken narration for 25-second YouTube Shorts previewing football matches.

Write EXACTLY 6 sentences previewing {team_a} versus {team_b} at World Cup 2026:
1. Tournament context — group stage, World Cup 2026
2. The fixture — who plays who and why it matters
3. {team_a}'s key strength or danger man to watch
4. {team_b}'s key strength or danger man to watch
5. A head-to-head fact or historical note between these two nations
6. A punchy prediction or hype line to close

Rules:
- Natural spoken English, 10–18 words per sentence
- No jargon, no stats abbreviations
- No sentence starts with "And"

Respond ONLY in this exact JSON:
{{"sentences": ["s1","s2","s3","s4","s5","s6"]}}"""

        sentences = deepseek_sentences(prompt)
        if sentences and len(sentences) >= 4:
            return sentences

    return [
        "World Cup 2026 group stage action is here.",
        f"{team_a if len(parts)==2 else 'The home side'} bring quality and momentum into this fixture.",
        "Their opponents will be looking to cause an upset.",
        "Head to head, these two nations have had some classic encounters.",
        "Watch the midfield battle — that is where this game will be won.",
        "Do not miss this one — it could define the group.",
    ]

async def _tts_sentence(text, out_path):
    import edge_tts
    comm = edge_tts.Communicate(text, EDGE_VOICE, rate=SPEECH_RATE)
    await comm.save(str(out_path))

def render_sentences_with_pauses(sentences, out_path):
    """Render each sentence separately, join with silence via ffmpeg."""
    import edge_tts  # confirm installed

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        parts = []

        for i, sentence in enumerate(sentences):
            mp3 = tmp / f's{i}.mp3'
            asyncio.run(_tts_sentence(sentence, mp3))
            parts.append(str(mp3))

            # add silence file after each sentence except the last
            if i < len(sentences) - 1:
                silence = tmp / f'silence{i}.mp3'
                subprocess.run([
                    'ffmpeg', '-y',
                    '-f', 'lavfi', '-i', f'anullsrc=r=24000:cl=mono',
                    '-t', str(PAUSE_SECS),
                    '-c:a', 'libmp3lame', '-q:a', '4',
                    str(silence)
                ], capture_output=True, check=True)
                parts.append(str(silence))

        # concat all parts
        concat_list = tmp / 'concat.txt'
        concat_list.write_text('\n'.join(f"file '{p}'" for p in parts))
        out_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([
            'ffmpeg', '-y',
            '-f', 'concat', '-safe', '0',
            '-i', str(concat_list),
            '-c:a', 'libmp3lame', '-q:a', '3',
            str(out_path)
        ], capture_output=True, check=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--slug', required=True)
    parser.add_argument('--post', action='store_true')
    args = parser.parse_args()

    slug     = args.slug
    out_path = SHORTS / slug / 'export' / 'narration.mp3'

    if args.post:
        results = load_results()
        row = results.get(slug)
        if not row:
            print(f'No result row for {slug}')
            sys.exit(1)
        sentences = build_post_sentences(row)
    else:
        sentences = build_pre_sentences(slug)

    print('Script:')
    for i, s in enumerate(sentences, 1):
        print(f'  {i}. {s}')

    try:
        render_sentences_with_pauses(sentences, out_path)
        print(f'Narration → {out_path}')
    except Exception as e:
        print(f'Error: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main()
