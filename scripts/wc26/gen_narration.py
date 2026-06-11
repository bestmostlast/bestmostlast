#!/usr/bin/env python3
"""
Generate ElevenLabs voiceover for a WC26 match short.

Usage:
  python3 scripts/wc26/gen_narration.py --slug m001-mexico-vs-south-africa [--post]

Writes audio to: scripts/wc26/shorts/<slug>/export/narration.mp3
"""

import argparse, csv, json, os, sys, urllib.request, urllib.error
from pathlib import Path

HERE    = Path(__file__).parent
RESULTS = HERE / 'data' / 'results.csv'
SHORTS  = HERE / 'shorts'

VOICE_ID = 'TABZn6CDfjMNGrsnGzzD'  # WikiBrad — fast informative narrator
MODEL_ID = 'eleven_turbo_v2'        # fastest + cheapest ElevenLabs model

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

Write a sports-broadcast narration in EXACTLY 6 short sentences that will be read aloud over a 30-second video:
1. Open with the competition context (group, tournament)
2. Announce the result naturally — say full scorer names and minutes naturally, like a commentator would
3. Describe the key goal moment or turning point
4. Give the stats (shots, possession) as a punchy comparison
5. Mention cards or drama if notable, otherwise group standing impact
6. Close with one sharp editorial line — what this result means

Rules: natural spoken English only, no abbreviations, no raw CSV notation, no slash separators. Say "Jiménez scored in the 67th minute" not "R. Jiménez 67'". Keep each sentence under 15 words.

Respond in this exact JSON:
{{"sentences": ["sentence1", "sentence2", "sentence3", "sentence4", "sentence5", "sentence6"]}}"""

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

Write a pre-match narration for {team_a} versus {team_b} at World Cup 2026 in EXACTLY 6 short sentences:
1. Open: tournament context and fixture
2. One sentence on {team_a}'s strength or recent form
3. One sentence on {team_b}'s strength or recent form
4. A head-to-head fact or historical note between these teams
5. The key player or tactical matchup to watch
6. Close with a punchy prediction or hype line

Rules: natural spoken English, under 15 words per sentence, no stats jargon.

Respond in this exact JSON:
{{"sentences": ["sentence1", "sentence2", "sentence3", "sentence4", "sentence5", "sentence6"]}}"""

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

def generate_audio(text, out_path):
    api_key = os.environ.get('ELEVENLABS_API_KEY')
    if not api_key:
        print('ELEVENLABS_API_KEY not set — skipping narration')
        return False

    url = f'https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}'
    payload = json.dumps({
        'text': text,
        'model_id': MODEL_ID,
        'apply_text_normalization': 'off',  # preserve SSML <break> tags
        'voice_settings': {
            'stability': 0.35,
            'similarity_boost': 0.75,
            'style': 0.4,
            'use_speaker_boost': True,
        },
    }).encode()

    req = urllib.request.Request(url, data=payload, headers={
        'xi-api-key': api_key,
        'Content-Type': 'application/json',
        'Accept': 'audio/mpeg',
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(r.read())
        print(f'Narration → {out_path}')
        return True
    except urllib.error.HTTPError as e:
        print(f'ElevenLabs error {e.code}: {e.read().decode()[:200]}')
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
