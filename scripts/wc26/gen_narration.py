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

    prompt = f"""You write spoken narration for a 30-second YouTube Short showing a football match result.
The video shows 4 screens after a splash. Write ONE sentence per screen matching what viewers see.

Match data:
- {team_a} {score_a}–{score_b} {team_b} | Group {group} | WC2026
- Scorers: {team_a}: {scorers_a or 'none'} | {team_b}: {scorers_b or 'none'}
- Shots: {shots_a}–{shots_b} | Possession: {poss_a}%–{poss_b}%
- Cards: {team_a} Y{yellow_a} R{red_a} | {team_b} Y{yellow_b} R{red_b}

Write EXACTLY 4 sentences, one per screen:
S1 (Result screen — score and scorers): Announce the result and name every scorer with their minute naturally.
S2 (Stats screen — shots, possession, cards): Describe who dominated the stats — shots on goal, possession, any cards drama.
S3 (Man of the match / headline screen): Deliver the headline and name the standout player — why they were decisive.
S4 (Group standings screen): What does this result mean for the group — who goes top, who is in trouble.

Rules:
- Natural spoken English, commentator tone, 12–18 words per sentence
- Say "scored in the 67th minute" not "67'" — never raw notation
- No sentence starts with "And"

Respond ONLY in this exact JSON:
{{"sentences": ["s1","s2","s3","s4"]}}"""

    sentences = deepseek_sentences(prompt)
    if sentences and len(sentences) >= 4:
        return sentences

    # fallback — one sentence per screen
    winner = team_a if int(score_a) > int(score_b) else (team_b if int(score_b) > int(score_a) else None)
    scorers_text = f"{scorers_a.replace('/', ' and ')} for {team_a}" if scorers_a else f"{team_a} were clinical"
    if scorers_b:
        scorers_text += f", {scorers_b.replace('/', ' and ')} for {team_b}"
    return [
        f"{team_a} beat {team_b} {score_a} nil at the 2026 World Cup — {scorers_text}." if score_b == '0' else f"Full time in Group {group} — {team_a} {score_a}, {team_b} {score_b}, with {scorers_text}.",
        f"{team_a} dominated the stats with {shots_a} shots to {shots_b} and {poss_a} percent possession." if shots_a else f"The stats reflected {team_a}'s control throughout the ninety minutes.",
        f"A commanding performance from {team_a} — their key man was the difference on the night.",
        f"{winner} move to the top of Group {group} with three points from their opening fixture." if winner else f"Honours even in Group {group} — both sides share the spoils.",
    ]

def build_pre_sentences(slug):
    parts = slug.split('-vs-')
    team_a = parts[0].split('-', 1)[1].replace('-', ' ').title() if len(parts) == 2 else 'Team A'
    team_b = parts[1].replace('-', ' ').title() if len(parts) == 2 else 'Team B'

    # Pull H2H data from CSV to give DeepSeek real numbers
    h2h_context = ''
    try:
        import csv as _csv
        h2h_file = HERE / 'data' / 'h2h_short.csv'
        if h2h_file.exists():
            for r in _csv.DictReader(open(h2h_file)):
                if r.get('slug', '') == slug:
                    h2h_context = (
                        f"WC appearances: {team_a} {r.get('wc_a','')}x, {team_b} {r.get('wc_b','')}x. "
                        f"H2H: played {r.get('h2h_played','?')}, {team_a} won {r.get('h2h_w_a','?')}, "
                        f"{team_b} won {r.get('h2h_w_b','?')}, drawn {r.get('h2h_d','?')}. "
                        f"Top scorer {team_a}: {r.get('top_scorer_a','')}. Top scorer {team_b}: {r.get('top_scorer_b','')}. "
                        f"Player to watch {team_a}: {r.get('watch_a','')}. Player to watch {team_b}: {r.get('watch_b','')}."
                    )
                    break
    except Exception:
        pass

    prompt = f"""You write spoken narration for a 35-second YouTube Short previewing a World Cup match.
The video shows 5 screens in order. Write ONE sentence per screen that matches what viewers see.

Match: {team_a} vs {team_b} | World Cup 2026
{h2h_context}

Write EXACTLY 5 sentences, one per screen:
S1 (World Cup records): Introduce both nations — World Cup history and pedigree in one sentence.
S2 (Head-to-head stats): Describe the H2H record — wins, draws, and one standout H2H fact.
S3 (Key players): Name the most dangerous historical and current players for each side.
S4 (Storyline): Build the narrative — what is at stake, the tactical battle, any rivalry angle.
S5 (Lineups): Close with a lineup intro — "here are the expected starting elevens" or similar.

Rules:
- 12–20 words per sentence to fill each screen's display time
- Natural spoken English, commentator tone, no jargon
- No sentence starts with "And"
- S5 must end with "here are the expected starting elevens" or "let's see the lineups"

Respond ONLY in this exact JSON:
{{"sentences": ["s1","s2","s3","s4","s5"]}}"""

    sentences = deepseek_sentences(prompt)
    if sentences and len(sentences) >= 4:
        return sentences

    return [
        f"World Cup 2026 — {team_a} and {team_b} meet in what promises to be a fierce group stage battle.",
        f"Head to head, these nations have produced tight encounters with no side dominating.",
        f"Watch the key men on both sides — pace, experience, and quality will be decisive.",
        f"Both teams need points badly — this one could define who progresses from the group.",
        "Here are the expected starting elevens for this World Cup clash.",
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
