# WC26 H2H Shorts — how the renderer works

Turns the H2H data into finished vertical Shorts (1080×1920), one per game.
**Fully automated** — flags + stadium photos are fetched, not hand-placed.

## Layout (per your Sheet-3 card)
```
        [date]  ·  STADIUM NAME            ← top
   🇦 flag            🇧 flag
   TEAM A             TEAM B               ← names under flags
   17    WORLD CUPS      3                 ← stat stack: A (left) | label | B (right)
   …     (WCs/High/Avg/GP/W/D/L/GF/GA/P/PPG)
   — HEAD TO HEAD —                        ← H2H sub-block (Won/Drawn/Lost/GF/GA)
   [BML logo]  bestmostlast.com            ← bottom
```

## Pipeline
```
data/h2h_flat.csv  +  fixtures.csv  →  data/h2h_short.csv   (merges stadium + date)
                                          ↓
card.html  (canvas renderer, draw(t) animates 0→1 count-up)
                                          ↓
render_all.js  →  <slug>/export/short.png        (still)
render_all.js --mp4  →  <slug>/export/short.mp4  (4s count-up + 1s hold, 30fps, H.264)
```

## Run it
```bash
npm i puppeteer                              # one-time
node scripts/wc26/shorts/render_all.js       # 72 stills
node scripts/wc26/shorts/render_all.js --mp4 # 72 animated MP4s (needs ffmpeg)
```
Single-card design/tuning: open `card.html` in a browser, load `data/h2h_short.csv`, pick a match.

## Assets (auto-fetched — no manual work)
- `_shared/flags/<Team>.png`   — 48 national flags (flagcdn, public domain).
- `_shared/stadiums/<City>.jpg` — 17 venue photos (Wikipedia/Commons).
- `_shared/brand/bml-logo.png`  — the BML "lady" logo (from repo `logo/bml.png`).
Missing asset → graceful fallback (gradient bg / placeholder flag).

## Regenerating data
```bash
python3 scripts/wc26/build_team_data.py    # team stats from Fjelstul dataset
python3 scripts/wc26/build_h2h_cards.py    # h2h_flat.csv (+ stacked cards)
# then re-merge stadium/date into h2h_short.csv (see build step) and re-render
```

## Known gaps / next polish
- **Kickoff times** not shown (only date) — no reliable per-match time source yet.
- **Knockouts (m073–104)** are TBD until the bracket resolves; re-run after results.
- Flags for England/Scotland use sub-region codes (gb-eng/gb-sct).
- Stadium photos are generic venue shots; swap any file in `_shared/stadiums/` to taste.
