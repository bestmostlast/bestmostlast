#!/usr/bin/env python3
"""
Fetch WC26 match results + stats from ESPN and write to results.csv.
Called by daemon.py after each game finishes.

No API key required — uses ESPN's public scoreboard/summary endpoints.
"""

import csv, json, re, time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import urllib.request

HERE     = Path(__file__).parent
FIXTURES = HERE / 'fixtures.csv'
RESULTS  = HERE / 'data' / 'results.csv'

ESPN_SCOREBOARD = 'https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates={date}'
ESPN_SUMMARY    = 'https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/summary?event={event_id}'

HEADERS = {'User-Agent': 'Mozilla/5.0'}

# Name normalisation — ESPN sometimes differs from our fixtures.csv
TEAM_ALIASES = {
    'czechia': 'czech republic',
    'czech republic': 'czech republic',
    'ir iran': 'iran',
    'korea republic': 'south korea',
    'usa': 'usa',
    'united states': 'usa',
    'bosnia and herzegovina': 'bosnia & herzegovina',
    "côte d'ivoire": 'ivory coast',
    "cote d'ivoire": 'ivory coast',
    'ivory coast': 'ivory coast',
    'dr congo': 'dr congo',
    'congo dr': 'dr congo',
    'trinidad and tobago': 'trinidad & tobago',
}

def normalise(name):
    return TEAM_ALIASES.get(name.lower().strip(), name.lower().strip())

def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def load_fixtures():
    return list(csv.DictReader(open(FIXTURES)))

def load_results():
    if not RESULTS.exists():
        return []
    return list(csv.DictReader(open(RESULTS)))

def results_by_slug():
    return {r['slug']: r for r in load_results()}

def save_results(rows):
    fieldnames = [
        'match_no','slug','team_a','team_b','group','phase','date','venue','city',
        'score_a','score_b','penalties_a','penalties_b','scorers_a','scorers_b',
        'poss_a','poss_b','shots_a','shots_b','sot_a','sot_b','xg_a','xg_b',
        'corners_a','corners_b','yellow_a','yellow_b','red_a','red_b',
        'potm_name','potm_team','potm_goals','potm_assists','potm_rating',
        'table_1_name','table_1_pld','table_1_pts','table_1_gd','table_1_gf',
        'table_2_name','table_2_pld','table_2_pts','table_2_gd','table_2_gf',
        'table_3_name','table_3_pld','table_3_pts','table_3_gd','table_3_gf',
        'table_4_name','table_4_pld','table_4_pts','table_4_gd','table_4_gf',
        'ratings_a','ratings_b','cards_a','cards_b','headline','comment',
    ]
    with open(RESULTS, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)

def parse_scorers(details, team_id, home_id):
    """Extract scorer strings like 'Giménez 23 / Jiménez 67' from ESPN details."""
    goals = []
    for d in details:
        if not d.get('scoringPlay'):
            continue
        tid = d.get('team', {}).get('id', '')
        if str(tid) != str(team_id):
            continue
        minute = d.get('clock', {}).get('displayValue', '?')
        athletes = d.get('athletesInvolved', [])
        name = athletes[0].get('shortName', '?') if athletes else '?'
        og = ' (OG)' if d.get('ownGoal') else ''
        pk = ' (P)' if d.get('penaltyKick') else ''
        goals.append(f'{name} {minute}{og}{pk}')
    return ' / '.join(goals)

def parse_cards(details, team_id):
    """Return 'Mokoena Y / Dlamini Y / Smith R' style string."""
    cards = []
    for d in details:
        yellow = d.get('yellowCard') or d.get('type', {}).get('text') == 'Yellow Card'
        red    = d.get('redCard')    or d.get('type', {}).get('text') in ('Red Card', 'Second Yellow Card')
        if not (yellow or red):
            continue
        tid = d.get('team', {}).get('id', '')
        if str(tid) != str(team_id):
            continue
        athletes = d.get('athletesInvolved', [])
        name = athletes[0].get('shortName', '?') if athletes else '?'
        suffix = 'R' if red else 'Y'
        cards.append(f'{name} {suffix}')
    return ' / '.join(cards)

def stat(stats_list, name, default=''):
    for s in stats_list:
        if s.get('name') == name:
            v = s.get('displayValue', default)
            # convert ratio strings like '0.2' → keep as-is; percentages → round
            return v
    return default

def parse_standings(groups, group_letter):
    """Return up to 4 team rows for the matching group."""
    for g in groups:
        header = g.get('header', '')
        if f'Group {group_letter}' in header or header.endswith(f' {group_letter}'):
            entries = g.get('entries', [])
            rows = []
            for e in entries:
                name = e.get('team', {}).get('displayName', '')
                s = {x['name']: x['displayValue'] for x in e.get('stats', [])}
                rows.append({
                    'name': name,
                    'pld':  s.get('gamesPlayed', '0'),
                    'pts':  s.get('points', '0'),
                    'gd':   s.get('pointDifferential', '0'),
                    'gf':   s.get('pointsFor', '0'),
                })
            return rows[:4]
    return []

def fetch_completed_match(espn_event, fixture):
    """Given a completed ESPN event + our fixture row, return a results.csv dict."""
    comp = espn_event['competitions'][0]
    competitors = comp.get('competitors', [])

    # Map ESPN team → home/away order matching our fixture
    fix_a = normalise(fixture['team_a'])
    fix_b = normalise(fixture['team_b'])

    team_map = {}
    for c in competitors:
        n = normalise(c['team']['displayName'])
        team_map[n] = c

    comp_a = team_map.get(fix_a) or competitors[0]
    comp_b = team_map.get(fix_b) or competitors[1]

    score_a = comp_a.get('score', '0')
    score_b = comp_b.get('score', '0')
    id_a    = comp_a['team']['id']
    id_b    = comp_b['team']['id']

    details = comp.get('details', [])
    scorers_a = parse_scorers(details, id_a, id_a)
    scorers_b = parse_scorers(details, id_b, id_a)
    cards_a   = parse_cards(details, id_a)
    cards_b   = parse_cards(details, id_b)

    # Count cards from details (more reliable than stats)
    yellow_a = sum(1 for d in details if d.get('yellowCard') and str(d.get('team',{}).get('id','')) == str(id_a))
    yellow_b = sum(1 for d in details if d.get('yellowCard') and str(d.get('team',{}).get('id','')) == str(id_b))
    red_a    = sum(1 for d in details if d.get('redCard')    and str(d.get('team',{}).get('id','')) == str(id_a))
    red_b    = sum(1 for d in details if d.get('redCard')    and str(d.get('team',{}).get('id','')) == str(id_b))

    # Full stats from summary endpoint
    try:
        summary  = fetch(ESPN_SUMMARY.format(event_id=espn_event['id']))
        bx_teams = summary.get('boxscore', {}).get('teams', [])

        stats_a, stats_b = [], []
        for t in bx_teams:
            n = normalise(t.get('team', {}).get('displayName', ''))
            if n == fix_a:
                stats_a = t.get('statistics', [])
            else:
                stats_b = t.get('statistics', [])

        poss_a   = stat(stats_a, 'possessionPct', '50')
        poss_b   = stat(stats_b, 'possessionPct', '50')
        shots_a  = stat(stats_a, 'totalShots', '')
        shots_b  = stat(stats_b, 'totalShots', '')
        sot_a    = stat(stats_a, 'shotsOnTarget', '')
        sot_b    = stat(stats_b, 'shotsOnTarget', '')
        corners_a = stat(stats_a, 'wonCorners', '')
        corners_b = stat(stats_b, 'wonCorners', '')
        # overwrite card counts with boxscore if available
        yellow_a = stat(stats_a, 'yellowCards', str(yellow_a))
        yellow_b = stat(stats_b, 'yellowCards', str(yellow_b))
        red_a    = stat(stats_a, 'redCards',    str(red_a))
        red_b    = stat(stats_b, 'redCards',    str(red_b))

        # Standings
        groups   = summary.get('standings', {}).get('groups', [])
        table    = parse_standings(groups, fixture['group'])

        # POTM — ESPN doesn't give a clean POTM; use top scorer or most shots
        potm_name, potm_team, potm_goals, potm_assists = '', '', '', ''
        leaders = summary.get('leaders', [])
        for l in leaders:
            for la in l.get('leaders', []):
                ath = la.get('athlete', {})
                if ath.get('displayName'):
                    potm_name = ath['displayName'].split()[-1]  # surname
                    potm_team = normalise(ath.get('team', {}).get('displayName', ''))
                    # map back to our team name
                    potm_team = fixture['team_a'] if normalise(fixture['team_a']) == potm_team else fixture['team_b']
                    break
            if potm_name:
                break

        # Fallback POTM: first scorer
        if not potm_name and details:
            for d in details:
                if d.get('scoringPlay') and d.get('athletesInvolved'):
                    ath = d['athletesInvolved'][0]
                    potm_name = ath.get('displayName', '').split()[-1]
                    tid = str(d.get('team', {}).get('id', ''))
                    potm_team = fixture['team_a'] if str(id_a) == tid else fixture['team_b']
                    potm_goals = '1'
                    break

    except Exception as ex:
        print(f'  summary fetch failed: {ex}')
        poss_a = poss_b = shots_a = shots_b = sot_a = sot_b = corners_a = corners_b = ''
        table  = []
        potm_name = potm_team = potm_goals = potm_assists = ''

    def trow(i):
        if i < len(table):
            t = table[i]
            return t['name'], t['pld'], t['pts'], t['gd'], t['gf']
        return '', '', '', '', ''

    t1 = trow(0); t2 = trow(1); t3 = trow(2); t4 = trow(3)

    return {
        'match_no':    fixture['match_no'],
        'slug':        fixture['slug'],
        'team_a':      fixture['team_a'],
        'team_b':      fixture['team_b'],
        'group':       fixture['group'],
        'phase':       fixture['phase'],
        'date':        datetime.strptime(fixture['date'], '%Y-%m-%d').strftime('%B %-d %Y'),
        'venue':       fixture['venue'],
        'city':        fixture['city'],
        'score_a':     score_a,
        'score_b':     score_b,
        'penalties_a': '', 'penalties_b': '',
        'scorers_a':   scorers_a,
        'scorers_b':   scorers_b,
        'poss_a':      poss_a,   'poss_b':  poss_b,
        'shots_a':     shots_a,  'shots_b': shots_b,
        'sot_a':       sot_a,    'sot_b':   sot_b,
        'xg_a': '', 'xg_b': '',
        'corners_a':   corners_a, 'corners_b': corners_b,
        'yellow_a':    str(yellow_a), 'yellow_b': str(yellow_b),
        'red_a':       str(red_a),    'red_b':    str(red_b),
        'potm_name':   potm_name, 'potm_team': potm_team,
        'potm_goals':  potm_goals, 'potm_assists': potm_assists, 'potm_rating': '',
        'table_1_name': t1[0], 'table_1_pld': t1[1], 'table_1_pts': t1[2], 'table_1_gd': t1[3], 'table_1_gf': t1[4],
        'table_2_name': t2[0], 'table_2_pld': t2[1], 'table_2_pts': t2[2], 'table_2_gd': t2[3], 'table_2_gf': t2[4],
        'table_3_name': t3[0], 'table_3_pld': t3[1], 'table_3_pts': t3[2], 'table_3_gd': t3[3], 'table_3_gf': t3[4],
        'table_4_name': t4[0], 'table_4_pld': t4[1], 'table_4_pts': t4[2], 'table_4_gd': t4[3], 'table_4_gf': t4[4],
        'ratings_a': '', 'ratings_b': '',
        'cards_a':   cards_a,
        'cards_b':   cards_b,
        'headline':  '',
        'comment':   '',
    }

def poll_date(date_str):
    """
    Fetch all completed WC matches on date_str (YYYYMMDD).
    Returns list of (fixture_row, result_dict) for newly finished games.
    """
    try:
        data = fetch(ESPN_SCOREBOARD.format(date=date_str))
    except Exception as e:
        print(f'ESPN scoreboard fetch failed for {date_str}: {e}')
        return []

    events = data.get('events', [])
    fixtures = {normalise(f['team_a']) + '|' + normalise(f['team_b']): f for f in load_fixtures()}
    done = results_by_slug()
    new_results = []

    for event in events:
        comp   = event.get('competitions', [{}])[0]
        status = comp.get('status', {}).get('type', {})
        if not status.get('completed', False):
            continue

        teams = comp.get('competitors', [])
        if len(teams) < 2:
            continue
        n_a = normalise(teams[0]['team']['displayName'])
        n_b = normalise(teams[1]['team']['displayName'])

        # try both orders
        fixture = fixtures.get(f'{n_a}|{n_b}') or fixtures.get(f'{n_b}|{n_a}')
        if not fixture:
            continue
        if fixture['slug'] in done:
            continue  # already have this result

        print(f'  New completed match: {fixture["team_a"]} vs {fixture["team_b"]}')
        try:
            result = fetch_completed_match(event, fixture)
            new_results.append(result)
        except Exception as e:
            print(f'  Failed to parse {fixture["slug"]}: {e}')

    return new_results

def update_results(new_rows):
    """Merge new rows into results.csv."""
    existing = load_results()
    existing_slugs = {r['slug'] for r in existing}
    added = 0
    for row in new_rows:
        if row['slug'] not in existing_slugs:
            existing.append(row)
            added += 1
    if added:
        save_results(existing)
    return added

if __name__ == '__main__':
    import sys
    date = sys.argv[1] if len(sys.argv) > 1 else datetime.now(timezone.utc).strftime('%Y%m%d')
    print(f'Polling ESPN for {date}…')
    new = poll_date(date)
    if new:
        n = update_results(new)
        print(f'Added {n} result(s) to results.csv')
        for r in new:
            print(f'  {r["slug"]}: {r["score_a"]}–{r["score_b"]}')
    else:
        print('No new completed matches.')
