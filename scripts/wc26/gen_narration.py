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

def build_post_script(row):
    team_a  = row['team_a']
    team_b  = row['team_b']
    score_a = row['score_a']
    score_b = row['score_b']
    group   = row.get('group', '')
    scorers_a = row.get('scorers_a', '').strip()
    scorers_b = row.get('scorers_b', '').strip()
    shots_a = row.get('shots_a', '')
    shots_b = row.get('shots_b', '')
    poss_a  = row.get('poss_a', '')
    headline = row.get('headline', '')
    comment  = row.get('comment', '')

    # Score line
    if int(score_a) > int(score_b):
        result_line = f"{team_a} win {score_a} nil." if score_b == '0' else f"{team_a} win {score_a} {score_b}."
    elif int(score_b) > int(score_a):
        result_line = f"{team_b} win {score_b} nil." if score_a == '0' else f"{team_b} win {score_b} {score_a}."
    else:
        result_line = f"It ends {score_a} {score_b}. A point each."

    # Scorers
    scorer_line = ''
    if scorers_a:
        scorer_line += f"{team_a}: {scorers_a.replace('/', ',')}. "
    if scorers_b:
        scorer_line += f"{team_b}: {scorers_b.replace('/', ',')}."

    # Stats
    stats_line = ''
    if shots_a and shots_b:
        stats_line = f"{shots_a} shots to {shots_b}."
    if poss_a:
        try:
            poss_b = round(100 - float(poss_a))
            stats_line += f" Possession: {round(float(poss_a))} {poss_b}."
        except Exception:
            pass

    # Headline/comment from DeepSeek
    editorial = ''
    if headline:
        editorial = headline + '. '
    if comment:
        editorial += comment

    parts = [
        f"Group {group}. World Cup 2026.",
        result_line,
        scorer_line,
        stats_line,
        editorial,
    ]
    return ' '.join(p for p in parts if p.strip())

def build_pre_script(slug):
    # Pre-match: minimal — just team names and group from slug
    # e.g. m002-south-korea-vs-czech-republic
    parts = slug.split('-vs-')
    if len(parts) == 2:
        team_a = parts[0].split('-', 1)[1].replace('-', ' ').title()
        team_b = parts[1].replace('-', ' ').title()
        return f"World Cup 2026. {team_a} versus {team_b}. Head to head history, stats, and players to watch. Let's break it down."
    return "World Cup 2026. Pre-match analysis."

def generate_audio(text, out_path):
    api_key = os.environ.get('ELEVENLABS_API_KEY')
    if not api_key:
        print('ELEVENLABS_API_KEY not set — skipping narration')
        return False

    url = f'https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}'
    payload = json.dumps({
        'text': text,
        'model_id': MODEL_ID,
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
