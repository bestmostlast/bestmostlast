#!/usr/bin/env python3
"""
1. Pulls all WC26 kickoff times from ESPN.
2. Updates fixtures.csv with UTC times.
3. Schedules macOS pmset wakeups:
   - kickoff - 3h10m  → wake, run daemon (uploads pre short), sleep after 20min
   - kickoff + 2h20m  → wake, run daemon (fetches result + uploads post), sleep after 20min
   - kickoff + 3h20m  → safety retry wake

Run once (needs sudo for pmset):
  python3 scripts/wc26/schedule_wakeups.py

Also installs a launchd agent that runs the daemon on every wake.
"""

import csv, json, subprocess, sys, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE     = Path(__file__).parent
ROOT     = HERE.parent.parent
FIXTURES = HERE / 'fixtures.csv'
HEADERS  = {'User-Agent': 'Mozilla/5.0'}
PLIST    = Path.home() / 'Library/LaunchAgents/com.bml.wc26daemon.plist'

def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def normalise(name):
    aliases = {
        'czechia':            'Czech Republic',
        'united states':      'USA',
        'bosnia-herzegovina': 'Bosnia & Herzegovina',
        "côte d'ivoire":      'Ivory Coast',
        'korea republic':     'South Korea',
        'ir iran':            'Iran',
        'dr congo':           'DR Congo',
    }
    return aliases.get(name.lower(), name)

def pmset_fmt(dt):
    return dt.astimezone().strftime('%m/%d/%y %H:%M:%S')

def schedule_wake(dt, label):
    fmt = pmset_fmt(dt)
    print(f'  wake  {fmt}  ({label})')
    r = subprocess.run(['sudo', 'pmset', 'schedule', 'wake', fmt],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f'    WARNING: {r.stderr.strip()}')

def schedule_sleep(dt, label):
    fmt = pmset_fmt(dt)
    print(f'  sleep {fmt}  ({label})')
    r = subprocess.run(['sudo', 'pmset', 'schedule', 'sleep', fmt],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f'    WARNING: {r.stderr.strip()}')

# ── 1. Pull ESPN schedule ──────────────────────────────────────────────────────

print('Fetching WC26 schedule from ESPN...')
data   = fetch('https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?limit=200&dates=20260611-20260720')
events = data.get('events', [])
print(f'Got {len(events)} events')

espn_times = {}
for e in events:
    comp  = e['competitions'][0]
    dt_str = comp.get('date', '')
    teams  = comp.get('competitors', [])
    if len(teams) < 2 or not dt_str:
        continue
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except ValueError:
        continue
    n_a = normalise(teams[0]['team']['displayName'])
    n_b = normalise(teams[1]['team']['displayName'])
    espn_times[f'{n_a}|{n_b}'] = dt
    espn_times[f'{n_b}|{n_a}'] = dt

# ── 2. Update fixtures.csv ─────────────────────────────────────────────────────

rows = list(csv.DictReader(open(FIXTURES)))
fieldnames = list(rows[0].keys())
now = datetime.now(timezone.utc)
kickoffs = {}
updated  = 0

for row in rows:
    key = f'{row["team_a"]}|{row["team_b"]}'
    dt  = espn_times.get(key)
    if dt:
        cet = dt + timedelta(hours=1)
        est = dt - timedelta(hours=5)
        row['time'] = f'{cet.strftime("%H:%M")} CET · {est.strftime("%H:%M")} EST'
        kickoffs[row['slug']] = dt
        updated += 1
    else:
        t = row.get('time', '')
        if t:
            try:
                cet_str = t.split('·')[0].strip().replace(' CET', '')
                cet_dt  = datetime.strptime(f'{row["date"]} {cet_str}', '%Y-%m-%d %H:%M')
                kickoffs[row['slug']] = cet_dt.replace(tzinfo=timezone(timedelta(hours=1)))
            except Exception:
                pass

with open(FIXTURES, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)

print(f'Updated {updated}/{len(rows)} kickoff times in fixtures.csv')

# ── 3. Install launchd agent ───────────────────────────────────────────────────

python_bin = sys.executable
daemon_py  = str(ROOT / 'scripts' / 'wc26' / 'daemon.py')
log_out    = str(ROOT / 'scripts' / 'wc26' / 'data' / 'daemon.log')
log_err    = str(ROOT / 'scripts' / 'wc26' / 'data' / 'daemon_err.log')
work_dir   = str(ROOT)

# Runs daemon for 25 min on every wake (enough to upload + return to sleep)
plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.bml.wc26daemon</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_bin}</string>
        <string>{daemon_py}</string>
        <string>--once</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{work_dir}</string>
    <key>StandardOutPath</key>
    <string>{log_out}</string>
    <key>StandardErrorPath</key>
    <string>{log_err}</string>
    <key>RunAtLoad</key>
    <false/>
    <key>StartOnMount</key>
    <false/>
</dict>
</plist>"""

PLIST.write_text(plist_content)
subprocess.run(['launchctl', 'unload', str(PLIST)], capture_output=True)
subprocess.run(['launchctl', 'load',   str(PLIST)], capture_output=True)
print(f'launchd agent installed → {PLIST}')

# ── 4. Schedule pmset wakes + sleeps ──────────────────────────────────────────

future = {slug: dt for slug, dt in kickoffs.items() if dt > now + timedelta(minutes=5)}
print(f'\nScheduling {len(future)} matches × 3 wakes = {len(future)*3} wake events...')
print('(sudo required — enter your password if prompted)\n')

# Clear existing BML-scheduled wakes (can't filter by owner easily, so we list first)
existing = subprocess.run(['pmset', '-g', 'sched'], capture_output=True, text=True).stdout
bml_count = existing.count('bml')
if bml_count:
    print(f'Found {bml_count} existing BML wake events — clearing all scheduled events first')
    subprocess.run(['sudo', 'pmset', 'schedule', 'cancelall'], capture_output=True)

for slug, ko in sorted(future.items(), key=lambda x: x[1]):
    short = slug[5:].replace('-vs-', ' v ')[:30]

    # PRE window: wake 3h10m before KO, sleep 25min later
    pre_wake  = ko - timedelta(hours=3, minutes=10)
    pre_sleep = pre_wake + timedelta(minutes=25)
    if pre_wake > now:
        schedule_wake(pre_wake,   f'PRE {short}')
        schedule_sleep(pre_sleep, f'PRE done {short}')

    # POST window: wake 2h20m after KO (game ~90min + buffer), sleep 25min later
    post_wake  = ko + timedelta(hours=2, minutes=20)
    post_sleep = post_wake + timedelta(minutes=25)
    schedule_wake(post_wake,   f'POST {short}')
    schedule_sleep(post_sleep, f'POST done {short}')

    # Safety retry: wake 3h20m after KO
    retry_wake  = ko + timedelta(hours=3, minutes=20)
    retry_sleep = retry_wake + timedelta(minutes=25)
    schedule_wake(retry_wake,   f'RETRY {short}')
    schedule_sleep(retry_sleep, f'RETRY done {short}')

print('\nAll wakes scheduled.')
print('Run `pmset -g sched` to verify.')
print(f'\nDaemon runs automatically on each wake via launchd.')
print(f'Logs → {log_out}')
