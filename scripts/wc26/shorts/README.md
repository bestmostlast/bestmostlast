# WC26 Preview Shorts — production root

All 104 match-preview Shorts live here, **one folder per game** + one **`_shared/`**
folder for everything common. Structure mirrors `fixtures.csv` slugs.

```
shorts/
├── _shared/                     ← reused by EVERY short (build once)
│   ├── brand/                   logo, end-card, lower-third templates, color tokens
│   ├── music/                   licensed beds (one default loop + a few moods)
│   ├── fonts/                   Barlow Semi Condensed (matches chart.html) + display font
│   ├── flags/                   national flag PNGs, reused across matches  (TODO)
│   └── CONVENTIONS.md           the locked format spec all shorts follow
│
├── m001-mexico-vs-south-africa/ ← one game
│   ├── preview.json             storyboard (the script; 5 beats)
│   ├── chart/chart.csv          2-team cumulative WC goals → chart.html
│   ├── assets/                  ONLY match-specific art (player cutouts; match flags if not shared)
│   ├── export/                  duel.webm (chart beat) + m001-final.mp4
│   └── PRODUCTION.md            part-by-part build guide for this match
│
├── m002-.../  …  m104-final/    (generated from fixtures.csv as data fills)
```

## Folder rules
- **`_shared/` = build once, reuse 104×.** Logo, fonts, music, end-card, flags, the format spec.
- **Per-game folder = only what's unique:** the storyboard, the 2-team chart CSV, player cutouts.
- **Slug = the key** everywhere (folder name, `fixtures.csv`, web page `/wc26/<slug>`, JSON `slug`).

## What ONE short needs (material manifest)
| Material | Where it comes from | Per-game or shared |
|---|---|---|
| Storyboard / script | `generate_previews.py` (from WC.csv + fixtures.csv) | per-game `preview.json` |
| 2-team chart CSV | generator | per-game `chart/chart.csv` |
| Chart beat clip | `public/data/chart.html` render | per-game `export/duel.webm` |
| Team flags | flag set | shared `_shared/flags/` |
| Player cutouts (2) | sourced per match | per-game `assets/` |
| Logo / end-card | brand | shared `_shared/brand/` |
| Music bed | licensed | shared `_shared/music/` |
| Fonts | Barlow + display | shared `_shared/fonts/` |
| Final video | assembler | per-game `export/m<NN>-final.mp4` |

## The 5 parts of every short (locked)
1. **Hook** (3s) — flags + title + teaser
2. **H2H** (7s) — past WC meetings / appearances (fallback: "first meeting")
3. **BML duel** (11s) — chart.html mini-race, the signature beat
4. **Players** (8s) — one player/side + one stat
5. **Expect + CTA** (9s) — honours + prediction + bestmostlast.com

Full per-match detail lives in each game's `PRODUCTION.md`.
See `_shared/CONVENTIONS.md` for the cross-short spec (sizes, fonts, timing, naming).
```
```
