#!/usr/bin/env python3
"""
WC26 YouTube Short auto-publisher daemon.

Keeps running on your Mac and:
  • Uploads pre-match shorts 3h before kickoff (scheduled to go public at kickoff)
  • Watches results.csv for new completed rows → auto-generates headline/comment via Claude,
    renders result.mp4, then uploads post-match short immediately.

Usage:
  python3 scripts/wc26/daemon.py

Requirements:
  pip install google-api-python-client google-auth-oauthlib google-auth-httplib2 Pillow anthropic
  npm install puppeteer  (for render_result.js)
  python3 scripts/wc26/yt_upload.py --auth  (first-time OAuth)
"""

import csv, json, os, subprocess, sys, time, hashlib, logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Load .env.wc26 if present (put ANTHROPIC_API_KEY=sk-... there)
_env_file = Path(__file__).parent / '.env.wc26'
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith('#') and '=' in _line:
            _k, _, _v = _line.partition('=')
            os.environ.setdefault(_k.strip(), _v.strip())

HERE     = Path(__file__).parent
ROOT     = HERE.parent.parent
FIXTURES = HERE / 'fixtures.csv'
RESULTS  = HERE / 'data' / 'results.csv'
PRE_CSV  = HERE / 'data' / 'yt_upload_pre_m01-m16.csv'
SHORTS   = HERE / 'shorts'
DONE     = HERE / 'data' / 'yt_upload_done.json'
STATE    = HERE / 'data' / 'daemon_state.json'

POLL_INTERVAL = 300  # seconds between checks (5 min)
PRE_WINDOW_H  = 3    # upload pre-short this many hours before kickoff

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)s  %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(HERE / 'data' / 'daemon.log'),
    ]
)
log = logging.getLogger('wc26.daemon')

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_done():
    return json.loads(DONE.read_text()) if DONE.exists() else {}

def is_done(slug, kind):
    return f'{slug}:{kind}' in load_done()

def load_state():
    return json.loads(STATE.read_text()) if STATE.exists() else {}

def save_state(s):
    STATE.write_text(json.dumps(s, indent=2))

def results_hash():
    return hashlib.md5(RESULTS.read_bytes()).hexdigest() if RESULTS.exists() else ''

def parse_fixtures():
    rows = list(csv.DictReader(open(FIXTURES)))
    return rows

def parse_results():
    if not RESULTS.exists():
        return []
    return list(csv.DictReader(open(RESULTS)))

def parse_pre_csv():
    if not PRE_CSV.exists():
        return []
    return list(csv.DictReader(open(PRE_CSV)))

def kickoff_utc(fixture_row):
    """Parse fixture date+time → UTC datetime. Times in fixtures.csv are CET (UTC+1 during June)."""
    date_str = fixture_row['date']   # '2026-06-11'
    time_str = fixture_row['time']   # '19:00 CET · 13:00 EST' or ''
    if not time_str:
        return None
    # take first token before space
    t = time_str.split()[0]  # '19:00'
    try:
        local_dt = datetime.strptime(f'{date_str} {t}', '%Y-%m-%d %H:%M')
        # CET = UTC+1 in June (no DST in this context)
        return local_dt.replace(tzinfo=timezone(timedelta(hours=1)))
    except ValueError:
        return None

def run(cmd, **kw):
    log.info(f'RUN: {" ".join(str(c) for c in cmd)}')
    result = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if result.returncode != 0:
        log.error(f'STDERR: {result.stderr[-500:]}')
        raise RuntimeError(f'Command failed: {cmd}')
    return result.stdout

# ── DeepSeek headline/comment generation ─────────────────────────────────────

def generate_headline_comment(row):
    api_key = os.environ.get('DEEPSEEK_API_KEY')
    if not api_key:
        log.warning('DEEPSEEK_API_KEY not set — using fallback headline')
        return _fallback_headline(row), _fallback_comment(row)

    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url='https://api.deepseek.com')

    poss_a = row.get('poss_a', '')
    prompt = f"""You write punchy, football-specific match result captions for YouTube Shorts.

Match: {row['team_a']} {row['score_a']}–{row['score_b']} {row['team_b']}
Group {row.get('group','')} | WC2026
Scorers: {row['team_a']}: {row.get('scorers_a','')} | {row['team_b']}: {row.get('scorers_b','')}
Player of the match: {row.get('potm_name','')} ({row.get('potm_team','')})
Stats: Possession {poss_a}%–{round(100-float(poss_a)) if poss_a else '?'}% | Shots {row.get('shots_a','')}–{row.get('shots_b','')}
Cards: {row['team_a']} Y{row.get('yellow_a','0')} R{row.get('red_a','0')} | {row['team_b']} Y{row.get('yellow_b','0')} R{row.get('red_b','0')}

Write two things:
1. HEADLINE: 6 words max. Punchy, specific, name the star or the moment. No generic phrases like "claim victory". Examples: "Giménez Lights Up the Azteca", "Son Brace Sinks the Czechs", "Late Drama Sends USA Through".
2. COMMENT: One sentence, max 20 words. Narrative context — what it means for the group, the player's significance, the drama. No padding.

Respond in this exact JSON format:
{{"headline": "...", "comment": "..."}}"""

    resp = client.chat.completions.create(
        model='deepseek-chat',
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=120,
        response_format={'type': 'json_object'},
    )
    text = resp.choices[0].message.content.strip()
    try:
        data = json.loads(text)
        return data['headline'], data['comment']
    except Exception:
        log.warning(f'DeepSeek JSON parse failed: {text!r} — using fallback')
        return _fallback_headline(row), _fallback_comment(row)

def _fallback_headline(row):
    return f'{row["team_a"]} {row["score_a"]}–{row["score_b"]} {row["team_b"]}'

def _fallback_comment(row):
    winner = row['team_a'] if int(row['score_a']) > int(row['score_b']) else (
             row['team_b'] if int(row['score_b']) > int(row['score_a']) else None)
    if winner:
        return f'{winner} take three points in Group {row["group"]}.'
    return f'A point each in Group {row["group"]}.'

# ── Write headline/comment back into results.csv ──────────────────────────────

def patch_results_row(slug, headline, comment):
    rows = list(csv.DictReader(open(RESULTS)))
    fieldnames = rows[0].keys() if rows else []
    for r in rows:
        if r['slug'] == slug:
            r['headline'] = headline
            r['comment']  = comment
            break
    with open(RESULTS, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    log.info(f'Patched results.csv: {slug} headline="{headline}"')

# ── Render + upload ───────────────────────────────────────────────────────────

def render_post(slug):
    result_mp4 = SHORTS / slug / 'export' / 'result.mp4'
    log.info(f'Rendering post short for {slug}…')
    run(['node', 'scripts/wc26/shorts/render_result.js', '--mp4', slug], cwd=str(ROOT))
    if not result_mp4.exists():
        raise RuntimeError(f'render_result.js finished but {result_mp4} not found')
    log.info(f'Render complete: {result_mp4}')

def upload(slug, kind):
    cmd = ['python3', 'scripts/wc26/yt_upload.py', '--slug', slug]
    if kind == 'post':
        cmd.append('--post')
    run(cmd, cwd=str(ROOT))
    refresh_hq()
    deploy_site(reason=f'{kind} {slug}')

def refresh_hq():
    try:
        run(['python3', 'scripts/wc26/gen_hq_panel.py'], cwd=str(ROOT))
    except Exception as e:
        log.warning(f'HQ panel refresh failed: {e}')

def deploy_site(reason='auto'):
    """Commit updated matches.json + results.csv and push to trigger Vercel deploy."""
    try:
        run(['git', 'add',
             'public/wc26/matches.json',
             'scripts/wc26/data/results.csv'],
            cwd=str(ROOT))
        # only commit if there are staged changes
        diff = subprocess.run(['git', 'diff', '--cached', '--quiet'],
                              cwd=str(ROOT))
        if diff.returncode == 0:
            log.info('deploy_site: nothing to commit')
            return
        run(['git', 'commit', '-m', f'wc26: update video/results data [{reason}]'],
            cwd=str(ROOT))
        run(['git', 'push'], cwd=str(ROOT))
        log.info('Pushed to git — Vercel deploy triggered')
    except Exception as e:
        log.error(f'deploy_site failed: {e}')

# ── Pre-match check ───────────────────────────────────────────────────────────

def check_pre(fixtures, pre_rows_by_slug):
    now = datetime.now(timezone.utc)
    for fx in fixtures:
        slug = fx['slug']
        if is_done(slug, 'pre'):
            continue
        if slug not in pre_rows_by_slug:
            continue  # no pre CSV row yet
        ko = kickoff_utc(fx)
        if ko is None:
            continue
        window_start = ko - timedelta(hours=PRE_WINDOW_H)
        if now >= window_start:
            log.info(f'PRE due: {slug} (kickoff {ko.isoformat()}, window opened {window_start.isoformat()})')
            try:
                upload(slug, 'pre')
                log.info(f'PRE uploaded: {slug}')
            except Exception as e:
                log.error(f'PRE upload failed for {slug}: {e}')

# ── Post-match check ──────────────────────────────────────────────────────────

def check_post(state):
    # Pull fresh results from ESPN for today (and yesterday in case of late games)
    now = datetime.now(timezone.utc)
    for delta in (0, 1):
        date_str = (now - timedelta(days=delta)).strftime('%Y%m%d')
        try:
            from fetch_results import poll_date, update_results
            new_rows = poll_date(date_str)
            if new_rows:
                added = update_results(new_rows)
                if added:
                    log.info(f'ESPN: fetched {added} new result(s) for {date_str}')
        except Exception as e:
            log.warning(f'ESPN fetch failed for {date_str}: {e}')

    rows = parse_results()
    processed = set(state.get('post_processed', []))

    for row in rows:
        slug = row.get('slug', '')
        if not slug or slug in processed:
            continue
        if row.get('espn_verified', '').strip() != '1':
            continue  # never upload from manually-entered placeholder data
        score_a = row.get('score_a', '').strip()
        score_b = row.get('score_b', '').strip()
        if not score_a or not score_b:
            continue  # no score yet

        log.info(f'New result detected: {slug} {score_a}–{score_b}')

        # Generate headline/comment if missing
        if not row.get('headline') or not row.get('comment'):
            log.info(f'Generating headline/comment for {slug}…')
            headline, comment = generate_headline_comment(row)
            patch_results_row(slug, headline, comment)
            row['headline'] = headline
            row['comment']  = comment

        # Render if result.mp4 not already there
        result_mp4 = SHORTS / slug / 'export' / 'result.mp4'
        if not result_mp4.exists():
            try:
                render_post(slug)
            except Exception as e:
                log.error(f'Render failed for {slug}: {e}')
                continue

        # Upload post short
        if not is_done(slug, 'post'):
            try:
                upload(slug, 'post')
                log.info(f'POST uploaded: {slug}')
            except Exception as e:
                log.error(f'POST upload failed for {slug}: {e}')
                continue

        processed.add(slug)

    state['post_processed'] = list(processed)
    return state

# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    once = '--once' in sys.argv  # single-shot mode for launchd / pmset wakes

    log.info(f'WC26 daemon starting ({"once" if once else "loop"} mode)…')
    fixtures = parse_fixtures()
    state    = load_state()
    refresh_hq()

    while True:
        try:
            pre_rows    = parse_pre_csv()
            pre_by_slug = {r['slug']: r for r in pre_rows}
            check_pre(fixtures, pre_by_slug)
            state = check_post(state)
            save_state(state)
        except Exception as e:
            log.error(f'Loop error: {e}', exc_info=True)

        if once:
            log.info('--once mode: exiting after single run')
            break

        time.sleep(POLL_INTERVAL)

if __name__ == '__main__':
    main()
