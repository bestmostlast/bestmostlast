#!/usr/bin/env python3
"""
Generate ElevenLabs voiceover for a WC26 match short.

Usage:
  python3 scripts/wc26/gen_narration.py --slug m001-mexico-vs-south-africa [--post]

Writes audio to: scripts/wc26/shorts/<slug>/export/narration.mp3
"""

import argparse, csv, json, os, re, sys, asyncio
from pathlib import Path

HERE    = Path(__file__).parent
RESULTS = HERE / 'data' / 'results.csv'
SHORTS  = HERE / 'shorts'

EDGE_VOICE = 'en-US-GuyNeural'  # Microsoft Edge TTS — free, no API key, sports broadcaster tone

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

def deepseek_narration(prompt):
    """Ask DeepSeek to write a spoken narration script, returned as a list of sentences."""
    api_key = os.environ.get('DEEPSEEK_API_KEY')
    if not api_key:
        return None
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url='https://api.deepseek.com')
    resp = client.chat.completions.create(
        model='deepseek-chat',
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=300,
        response_format={'type': 'json_object'},
    )
    try:
        data = json.loads(resp.choices[0].message.content.strip())
        return data.get('sentences', [])
    except Exception:
        return None

def build_post_script(row):
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

    prompt = f"""You write spoken narration scripts for 30-second YouTube Shorts about football matches.

Match data:
- {team_a} {score_a}–{score_b} {team_b} | Group {group} | WC2026
- Scorers: {team_a}: {scorers_a or 'none'} | {team_b}: {scorers_b or 'none'}
- Shots: {shots_a}–{shots_b} | Possession: {poss_a}%–{poss_b}%
- Cards: {team_a} Y{yellow_a} R{red_a} | {team_b} Y{yellow_b} R{red_b}

Write a sports-broadcast narration in EXACTLY 4 punchy sentences read aloud over a video:
1. Result: group, teams, score
2. Scorers with minutes, natural commentator language
3. One stat — shots or possession as a sharp comparison
4. One editorial line — what this result means for the group

Rules: natural spoken English, no abbreviations, no raw notation. Max 10 words per sentence. Say "Jiménez scored in the 67th" not "R. Jiménez 67'".

Respond in this exact JSON:
{{"sentences": ["sentence1", "sentence2", "sentence3", "sentence4"]}}"""

    sentences = deepseek_narration(prompt)
    if not sentences:
        # fallback
        sentences = [
            f"Group {group}, World Cup 2026.",
            f"{team_a} {score_a}, {team_b} {score_b}.",
            f"Goals from {scorers_a or team_a}." if scorers_a else f"{team_a} were clinical.",
            f"{shots_a} shots to {shots_b}." if shots_a else "A tight contest.",
            f"Possession split {poss_a} to {poss_b} percent." if poss_a else "",
            f"Three points for {team_a}." if int(score_a) > int(score_b) else (f"Three points for {team_b}." if int(score_b) > int(score_a) else "Honours even."),
        ]
        sentences = [s for s in sentences if s]

    PAUSE = '<break time="2.5s"/>'
    return f'<speak>{PAUSE.join(sentences)}</speak>'

def build_pre_script(slug):
    parts = slug.split('-vs-')
    if len(parts) == 2:
        team_a = parts[0].split('-', 1)[1].replace('-', ' ').title()
        team_b = parts[1].replace('-', ' ').title()

        prompt = f"""You write spoken narration scripts for 30-second YouTube Shorts about football matches.

Write a pre-match narration for {team_a} versus {team_b} at World Cup 2026 in EXACTLY 4 punchy sentences:
1. Tournament context and fixture
2. One team's key strength or danger man
3. The other team's key strength or danger man
4. One sharp prediction or hype line

Rules: natural spoken English, max 10 words per sentence, no jargon.

Respond in this exact JSON:
{{"sentences": ["sentence1", "sentence2", "sentence3", "sentence4"]}}"""

        sentences = deepseek_narration(prompt)
        if not sentences:
            sentences = [
                "World Cup 2026.",
                f"{team_a} versus {team_b}.",
                "Head to head history, stats, and players to watch.",
                "Let's break it down.",
            ]

        PAUSE = '<break time="2.5s"/>'
        return f'<speak>{PAUSE.join(sentences)}</speak>'
    return '<speak>World Cup 2026. Pre-match analysis.</speak>'

def strip_ssml(text):
    """Convert SSML to plain text with pauses as silence markers for edge-tts."""
    # edge-tts supports SSML natively — pass as-is
    return text

async def _generate_audio_async(text, out_path):
    import edge_tts
    # edge-tts supports SSML <break> tags natively
    communicate = edge_tts.Communicate(text, EDGE_VOICE, rate='+10%')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    await communicate.save(str(out_path))

def generate_audio(text, out_path):
    try:
        asyncio.run(_generate_audio_async(text, out_path))
        print(f'Narration → {out_path}')
        return True
    except Exception as e:
        print(f'edge-tts error: {e}')
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--slug', required=True)
    parser.add_argument('--post', action='store_true')
    args = parser.parse_args()

    slug = args.slug
    out_path = SHORTS / slug / 'export' / 'narration.mp3'

    if args.post:
        results = load_results()
        row = results.get(slug)
        if not row:
            print(f'No result row for {slug}')
            sys.exit(1)
        script = build_post_script(row)
    else:
        script = build_pre_script(slug)

    print(f'Script: {script}')
    ok = generate_audio(script, out_path)
    sys.exit(0 if ok else 1)

if __name__ == '__main__':
    main()
