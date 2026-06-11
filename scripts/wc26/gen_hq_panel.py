#!/usr/bin/env python3
"""
Regenerate the WC26 Shorts section in ~/Calynix/calynix-overview.html.
Called by daemon.py after every upload. Also safe to run manually.

Usage:
  python3 scripts/wc26/gen_hq_panel.py
"""

import csv, json, re
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE     = Path(__file__).parent
ROOT     = HERE.parent.parent
FIXTURES = HERE / 'fixtures.csv'
RESULTS  = HERE / 'data' / 'results.csv'
PRE_CSV  = HERE / 'data' / 'yt_upload_pre_m01-m16.csv'
DONE     = HERE / 'data' / 'yt_upload_done.json'
OVERVIEW = Path('/Users/bml/Calynix/calynix-overview.html')

MARKER_START = '<!-- WC26_PANEL_START -->'
MARKER_END   = '<!-- WC26_PANEL_END -->'

def load_done():
    return json.loads(DONE.read_text()) if DONE.exists() else {}

def parse_fixtures():
    return list(csv.DictReader(open(FIXTURES)))

def parse_results():
    if not RESULTS.exists():
        return {}
    return {r['slug']: r for r in csv.DictReader(open(RESULTS)) if r.get('score_a')}

def parse_pre_csv():
    if not PRE_CSV.exists():
        return {}
    return {r['slug']: r for r in csv.DictReader(open(PRE_CSV))}

def kickoff_utc(fx):
    date_str = fx['date']
    time_str = fx.get('time', '')
    if not time_str:
        return None
    t = time_str.split()[0]
    try:
        local_dt = datetime.strptime(f'{date_str} {t}', '%Y-%m-%d %H:%M')
        return local_dt.replace(tzinfo=timezone(timedelta(hours=1)))
    except ValueError:
        return None

def fmt_utc(dt):
    if dt is None:
        return '—'
    return dt.strftime('%b %d %H:%M UTC')

def yt_link(video_id):
    return f'<a href="https://youtube.com/shorts/{video_id}" target="_blank" style="color:var(--accent)">↗</a>'

def build_panel(fixtures, done, results, pre_by_slug):
    now = datetime.now(timezone.utc)
    rows_html = []

    for fx in fixtures:
        slug     = fx['slug']
        match_no = fx['match_no'].zfill(3)
        team_a   = fx['team_a']
        team_b   = fx['team_b']
        group    = fx['group']
        ko       = kickoff_utc(fx)
        ko_str   = fmt_utc(ko)

        # --- PRE ---
        pre_key  = f'{slug}:pre'
        pre_done = pre_key in done
        pre_id   = done.get(pre_key, {}).get('video_id', '')

        if pre_done:
            pre_cell = f'<span class="pill done">pre live {yt_link(pre_id)}</span>'
        elif ko and now >= ko - timedelta(hours=3):
            pre_cell = '<span class="pill pending">pre queued</span>'
        elif slug in pre_by_slug:
            pre_cell = f'<span class="pill">pre ready · kicks {ko_str}</span>'
        else:
            pre_cell = '<span class="pill blocked">pre not built</span>'

        # --- POST ---
        post_key  = f'{slug}:post'
        post_done = post_key in done
        post_id   = done.get(post_key, {}).get('video_id', '')
        has_result = slug in results

        if post_done:
            res = results.get(slug, {})
            score = f'{res.get("score_a","?")}–{res.get("score_b","?")}' if res else ''
            post_cell = f'<span class="pill done">post live {score} {yt_link(post_id)}</span>'
        elif has_result:
            post_cell = '<span class="pill pending">post rendering/uploading</span>'
        elif ko and now > ko + timedelta(hours=2):
            post_cell = '<span class="pill blocked">awaiting result data</span>'
        elif ko:
            post_cell = f'<span style="color:#666">kicks {ko_str}</span>'
        else:
            post_cell = '<span style="color:#666">TBD</span>'

        rows_html.append(
            f'<tr>'
            f'<td style="color:#aaa;font-size:10px">m{match_no}</td>'
            f'<td><b>{team_a}</b> vs <b>{team_b}</b> <span style="color:#888;font-size:10px">Gr {group}</span></td>'
            f'<td>{pre_cell}</td>'
            f'<td>{post_cell}</td>'
            f'</tr>'
        )

    # summary counts
    pre_live  = sum(1 for k in done if k.endswith(':pre'))
    post_live = sum(1 for k in done if k.endswith(':post'))
    total     = len(fixtures)

    panel = f'''{MARKER_START}
<div class="subpanel bml-wc26">
  <div class="csrow"><div class="hd">
    <span class="ttl">WC26 Shorts</span>
    <span class="st">
      <span class="pill done">{pre_live} pre live</span>
      <span class="pill done">{post_live} post live</span>
      <span style="color:#888;font-size:10px">of {total} matches</span>
    </span>
  </div></div>
  <div style="overflow-x:auto;margin-top:6px">
  <table style="width:100%;border-collapse:collapse;font-size:11px">
    <thead>
      <tr style="color:#888;border-bottom:1px solid #333">
        <th style="text-align:left;padding:3px 6px">#</th>
        <th style="text-align:left;padding:3px 6px">Match</th>
        <th style="text-align:left;padding:3px 6px">Pre</th>
        <th style="text-align:left;padding:3px 6px">Post</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows_html)}
    </tbody>
  </table>
  </div>
  <div class="csrow" style="margin-top:8px"><div class="hd">
    <span class="ttl">BML knockout cards</span>
    <span class="st"><span class="when">after group stage</span></span>
  </div>
    <details><summary>details</summary>m073–104 once WC26 bracket resolves.</details>
  </div>
</div>
{MARKER_END}'''

    return panel

def patch_overview(panel_html):
    html = OVERVIEW.read_text()
    if MARKER_START in html and MARKER_END in html:
        html = re.sub(
            re.escape(MARKER_START) + r'.*?' + re.escape(MARKER_END),
            panel_html,
            html,
            flags=re.DOTALL,
        )
    else:
        # first time — replace the old static subpanel block
        html = html.replace(
            '<div class="subpanel bml-wc26">',
            panel_html + '\n<div class="subpanel bml-wc26-OLD" style="display:none">',
        )
    OVERVIEW.write_text(html)
    print(f'Updated {OVERVIEW}')

def main():
    fixtures  = parse_fixtures()
    done      = load_done()
    results   = parse_results()
    pre_by_slug = parse_pre_csv()
    panel     = build_panel(fixtures, done, results, pre_by_slug)
    patch_overview(panel)

if __name__ == '__main__':
    main()
