#!/usr/bin/env python3
"""
Upload WC26 Shorts to YouTube.

Usage:
  # First run — opens browser for OAuth:
  python3 scripts/wc26/yt_upload.py --auth

  # Upload pre-match short for a single match:
  python3 scripts/wc26/yt_upload.py --slug m001-mexico-vs-south-africa

  # Upload post-match short for a single match (publishes immediately):
  python3 scripts/wc26/yt_upload.py --slug m001-mexico-vs-south-africa --post

  # Upload all M01-M16 pre shorts:
  python3 scripts/wc26/yt_upload.py --pre

  # Dry-run:
  python3 scripts/wc26/yt_upload.py --slug m001-mexico-vs-south-africa --dry-run

Requires:
  pip install google-api-python-client google-auth-oauthlib google-auth-httplib2 Pillow

OAuth setup:
  1. Go to console.cloud.google.com → create/select project
  2. Enable YouTube Data API v3
  3. Credentials → OAuth 2.0 Client ID → Desktop app
  4. Download JSON → save as scripts/wc26/client_secret.json
  5. Run: python3 scripts/wc26/yt_upload.py --auth
"""

import io, sys, csv, json, argparse, time
from datetime import datetime, timezone
from pathlib import Path

HERE   = Path(__file__).parent
ROOT   = HERE.parent.parent
SHORTS = HERE / 'shorts'
CSV    = HERE / 'data' / 'yt_upload_pre_m01-m16.csv'
RESULTS_CSV = HERE / 'data' / 'results.csv'
SECRET = HERE / 'client_secret.json'
TOKEN  = HERE / 'yt_token.json'
DONE   = HERE / 'data' / 'yt_upload_done.json'

SCOPES = ['https://www.googleapis.com/auth/youtube.upload',
          'https://www.googleapis.com/auth/youtube']

THUMB_MAX = 2 * 1024 * 1024  # 2 MB YouTube API limit

# ── Auth ──────────────────────────────────────────────────────────────────────

def get_credentials():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    creds = None
    if TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not SECRET.exists():
                print(f'\n❌  client_secret.json not found at {SECRET}')
                print('    Steps:')
                print('    1. console.cloud.google.com → your project')
                print('    2. APIs & Services → Enable: YouTube Data API v3')
                print('    3. Credentials → Create OAuth 2.0 Client ID → Desktop app')
                print('    4. Download JSON → save as scripts/wc26/client_secret.json')
                print('    5. Re-run this script\n')
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(str(SECRET), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN.write_text(creds.to_json())
        print(f'✓ Token saved → {TOKEN}')
    return creds

def get_service():
    from googleapiclient.discovery import build
    return build('youtube', 'v3', credentials=get_credentials())

# ── Thumbnail ─────────────────────────────────────────────────────────────────

def compress_thumb(path: Path) -> bytes:
    """Return JPEG bytes under THUMB_MAX, compressing if needed."""
    from PIL import Image
    img = Image.open(path).convert('RGB')
    for quality in (92, 80, 65, 50):
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=quality, optimize=True)
        data = buf.getvalue()
        if len(data) <= THUMB_MAX:
            return data
    raise RuntimeError(f'Cannot compress {path} under 2 MB')

def set_thumbnail(svc, video_id: str, path: Path):
    from googleapiclient.http import MediaInMemoryUpload
    data = compress_thumb(path)
    media = MediaInMemoryUpload(data, mimetype='image/jpeg', resumable=False)
    svc.thumbnails().set(videoId=video_id, media_body=media).execute()
    print(f'  ✓ Thumbnail set ({len(data)//1024}KB)')

# ── Playlist ──────────────────────────────────────────────────────────────────

def get_or_create_playlist(svc, title):
    r = svc.playlists().list(part='id,snippet', mine=True, maxResults=50).execute()
    for item in r.get('items', []):
        if item['snippet']['title'] == title:
            return item['id']
    resp = svc.playlists().insert(
        part='snippet,status',
        body={
            'snippet': {'title': title, 'description': f'WC2026 — {title}'},
            'status':  {'privacyStatus': 'public'},
        }
    ).execute()
    pid = resp['id']
    print(f'  ✓ Created playlist "{title}" → {pid}')
    return pid

def add_to_playlist(svc, video_id, playlist_id):
    svc.playlistItems().insert(
        part='snippet',
        body={'snippet': {'playlistId': playlist_id,
                          'resourceId': {'kind': 'youtube#video', 'videoId': video_id}}}
    ).execute()

# ── Upload ────────────────────────────────────────────────────────────────────

def parse_schedule(s):
    """'2026-06-11 16:00 UTC' → RFC3339"""
    s = s.replace(' UTC', '+00:00').replace(' ', 'T')
    if '+' not in s:
        s += '+00:00'
    if s.count(':') == 1:
        s = s.replace('+', ':00+')
    return s

def _do_upload(svc, video_path, title, description, tags, body_status, dry_run):
    from googleapiclient.http import MediaFileUpload
    print(f'  Title:  {title}')
    print(f'  Video:  {video_path}')
    if dry_run:
        print('  [DRY RUN — no upload]')
        return 'DRY_RUN_ID'

    body = {
        'snippet': {'title': title, 'description': description,
                    'tags': tags, 'categoryId': '17'},
        'status': body_status,
    }
    media = MediaFileUpload(str(video_path), mimetype='video/mp4',
                            resumable=True, chunksize=10 * 1024 * 1024)
    req = svc.videos().insert(part='snippet,status', body=body, media_body=media)
    response = None
    while response is None:
        status, response = req.next_chunk()
        if status:
            pct = int(status.resumable_progress / status.total_size * 100)
            print(f'  Uploading… {pct}%', end='\r')
    vid = response['id']
    print(f'  ✓ Uploaded → https://youtube.com/shorts/{vid}')
    return vid

def upload_pre(svc, row, dry_run=False):
    slug       = row['slug']
    video_path = SHORTS / slug / 'export' / 'short.mp4'
    thumb_path = SHORTS / slug / 'export' / 'thumb_yt.png'

    if not video_path.exists():
        print(f'  ✗ SKIP {slug} — short.mp4 not found')
        return None

    print(f'\n▶ PRE  {row["team_a"]} vs {row["team_b"]}')
    schedule = parse_schedule(row['schedule_utc'])
    print(f'  Schedule: {schedule}')

    tags = [t.strip() for t in row['tags'].split(',') if t.strip()]
    status = {
        'privacyStatus': 'private',
        'publishAt': schedule,
        'selfDeclaredMadeForKids': False,
        'madeForKids': False,
    }
    vid = _do_upload(svc, video_path, row['title'], row['description'], tags, status, dry_run)
    if vid and vid != 'DRY_RUN_ID' and thumb_path.exists():
        set_thumbnail(svc, vid, thumb_path)
    return vid

def _build_post_tags(team_a, team_b, group, venue=''):
    core = [
        'World Cup 2026', 'WC2026', 'FIFA World Cup 2026', 'FIFA WC2026',
        'match result', 'full time', 'football results', 'soccer results',
        'football stats', 'soccer stats', 'match stats', 'player of the match',
        'group standings', 'WC2026 results', 'WC26 group stage',
        'football short', 'soccer short', 'sports short', 'bestmostlast',
    ]
    extras = [
        team_a, team_b,
        f'{team_a} World Cup', f'{team_b} World Cup',
        f'{team_a} vs {team_b}', f'Group {group} WC2026',
    ]
    if venue:
        extras.append(venue)
    seen, result, total = set(), [], 0
    for t in core + extras:
        t = t.strip()
        if not t or t.lower() in seen:
            continue
        seen.add(t.lower())
        addition = len(t) + (2 if result else 0)
        if total + addition > 495:
            break
        result.append(t)
        total += addition
    return result

def upload_post(svc, result_row, dry_run=False):
    slug       = result_row['slug']
    video_path = SHORTS / slug / 'export' / 'result.mp4'
    thumb_path = SHORTS / slug / 'export' / 'thumb_post_yt.png'
    # fallback thumb
    if not thumb_path.exists():
        thumb_path = SHORTS / slug / 'export' / 'thumb_yt.png'

    if not video_path.exists():
        print(f'  ✗ SKIP {slug} — result.mp4 not found')
        return None

    r = result_row
    team_a, team_b = r['team_a'], r['team_b']
    score_a, score_b = r['score_a'], r['score_b']
    group  = r['group']
    date   = r['date']
    venue  = r['venue']
    slug_  = r['slug']

    title = f'{team_a} {score_a}–{score_b} {team_b} | World Cup 2026 Full Time | Match Stats'
    description = (
        f'⚽ FULL TIME: {team_a} {score_a}–{score_b} {team_b}\n'
        f'Group {group} | {date} | {venue}\n\n'
        f'Scorers, match stats, player of the match, and group standings — all in one Short.\n\n'
        f'🏆 World Cup 2026 — every result, decoded.\n'
        f'📊 Full data & analysis → https://bestmostlast.com/wc26/{slug_}\n\n'
        f'#WorldCup2026 #{team_a.replace(" ","")} #{team_b.replace(" ","")} '
        f'#WC2026 #FootballResults #FullTime'
    )
    tags = _build_post_tags(team_a, team_b, group, venue)

    print(f'\n▶ POST {team_a} {score_a}–{score_b} {team_b}')
    print(f'  Publishing immediately (public)')

    status = {
        'privacyStatus': 'public',
        'selfDeclaredMadeForKids': False,
        'madeForKids': False,
    }
    vid = _do_upload(svc, video_path, title, description, tags, status, dry_run)
    if vid and vid != 'DRY_RUN_ID' and thumb_path.exists():
        set_thumbnail(svc, vid, thumb_path)
    return vid

# ── State tracking ─────────────────────────────────────────────────────────────

def load_done():
    if DONE.exists():
        return json.loads(DONE.read_text())
    return {}

def mark_done(slug, kind, video_id, title):
    d = load_done()
    key = f'{slug}:{kind}'
    d[key] = {'video_id': video_id, 'title': title,
               'uploaded_at': datetime.now(timezone.utc).isoformat()}
    DONE.write_text(json.dumps(d, indent=2))

def already_done(done, slug, kind):
    return f'{slug}:{kind}' in done

def get_done_id(done, slug, kind):
    return done.get(f'{slug}:{kind}', {}).get('video_id')

# ── matches.json update ───────────────────────────────────────────────────────

def update_matches_json(slug, pre_id=None, post_id=None):
    mf = ROOT / 'public' / 'wc26' / 'matches.json'
    if not mf.exists():
        return
    data = json.loads(mf.read_text())
    matches = data['matches'] if isinstance(data, dict) and 'matches' in data else data
    for m in matches:
        if m.get('slug') == slug:
            if pre_id:
                m['youtubeId'] = pre_id
                m['videoUrl']  = f'https://www.youtube.com/shorts/{pre_id}'
                m['hasVideo']  = True
            if post_id:
                m['youtubePostId'] = post_id
                m['postVideoUrl']  = f'https://www.youtube.com/shorts/{post_id}'
                m['hasPostVideo']  = True
            break
    mf.write_text(json.dumps(data, indent=2) + '\n')

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--auth',    action='store_true', help='Authorise only')
    ap.add_argument('--pre',     action='store_true', help='Upload M01-M16 pre shorts')
    ap.add_argument('--post',    action='store_true', help='Upload post-match short (use with --slug)')
    ap.add_argument('--slug',    help='Match slug or number, e.g. m001-mexico-vs-south-africa or 1')
    ap.add_argument('--dry-run', action='store_true', dest='dry_run')
    ap.add_argument('--force',   action='store_true', help='Re-upload even if already done')
    args = ap.parse_args()

    if args.auth:
        get_credentials()
        print('✓ Auth complete.')
        return

    svc  = get_service()
    done = load_done()

    # ── POST-MATCH ────────────────────────────────────────────────────────────
    if args.post:
        if not args.slug:
            print('❌  --post requires --slug'); sys.exit(1)

        results = list(csv.DictReader(open(RESULTS_CSV)))
        rows = [r for r in results if r['slug'] == args.slug or r['match_no'] == args.slug]
        if not rows:
            print(f'❌  No result row found for {args.slug}'); sys.exit(1)
        row = rows[0]
        slug = row['slug']

        if not args.force and already_done(done, slug, 'post'):
            vid = get_done_id(done, slug, 'post')
            print(f'  ↩ SKIP {slug} post (already uploaded → {vid})')
            return

        playlist_id = None if args.dry_run else get_or_create_playlist(svc, 'WC2026 Post-Match Shorts')
        vid = upload_post(svc, row, dry_run=args.dry_run)
        if vid and vid != 'DRY_RUN_ID':
            add_to_playlist(svc, vid, playlist_id)
            mark_done(slug, 'post', vid, f'{row["team_a"]} {row["score_a"]}–{row["score_b"]} {row["team_b"]}')
            update_matches_json(slug, post_id=vid)
        print('\nDone.')
        return

    # ── PRE-MATCH ─────────────────────────────────────────────────────────────
    pre_rows = list(csv.DictReader(open(CSV)))
    if args.slug:
        pre_rows = [r for r in pre_rows if r['slug'] == args.slug or r['match_no'] == args.slug]
        if not pre_rows:
            print(f'❌  No row found for {args.slug}'); sys.exit(1)

    playlist_id = None if args.dry_run else get_or_create_playlist(svc, 'WC2026 Pre-Match Shorts')
    uploaded = skipped = 0

    for row in pre_rows:
        slug = row['slug']
        if not args.force and already_done(done, slug, 'pre'):
            vid = get_done_id(done, slug, 'pre')
            print(f'  ↩ SKIP {slug} pre (already uploaded → {vid})')
            skipped += 1
            continue

        vid = upload_pre(svc, row, dry_run=args.dry_run)
        if vid and vid != 'DRY_RUN_ID':
            add_to_playlist(svc, vid, playlist_id)
            mark_done(slug, 'pre', vid, row['title'])
            update_matches_json(slug, pre_id=vid)
            uploaded += 1
            time.sleep(2)
        elif vid == 'DRY_RUN_ID':
            uploaded += 1

    print(f'\nDone. {uploaded} uploaded, {skipped} skipped.')

if __name__ == '__main__':
    main()
