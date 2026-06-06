# WC26 Match Preview Shorts

Auto-generated per-match preview Shorts for World Cup 2026 (104 matches).
A new **compare** content type: "TEAM A vs TEAM B — what to expect", built from WC
history. One template, filled per fixture.

## Format (locked)

Vertical 1080×1920, 35–45s, fixed 5-beat skeleton — content is data-driven:

| # | Beat | ~s | What |
|---|------|----|------|
| 1 | `hook`     | 3  | Both flags, group/matchday/date, one teaser stat |
| 2 | `h2h`      | 7  | Past WC meetings: W-D-L + biggest result (fallback: "first-ever meeting") |
| 3 | `bml_duel` | 11 | chart.html mini-race — all-time WC goals, the two nations (signature beat) |
| 4 | `players`  | 8  | One player/side, one headline WC stat each |
| 5 | `expect`   | 9  | Best finishes/honours + prediction framing + CTA |

## Pipeline

```
fixtures.csv + WC.csv  →  generate_previews.py  →  preview_<slug>.json + charts/chart.<slug>.csv
preview JSON  →  [assembler]  →  preview_<slug>.mp4   (chart.html renders the duel beat)
preview JSON  →  web page /wc26/<slug>               (same data, the 1-video→1-page funnel)
```

## Files here

- `fixtures.csv` — all 104 matches. Group-stage teams are REAL (post-draw); knockouts are bracket placeholders.
- `build_fixtures.py` — regenerates `fixtures.csv` (re-run to fill knockout teams as results resolve).
- `preview.schema.json` — the storyboard contract (every video + page renders from this shape).
- `shorts/` — **the production root**, one folder per game + `_shared/`. See `shorts/README.md`.
  - `shorts/m001-mexico-vs-south-africa/` — the opener, built end-to-end as the reference short.
  - `shorts/_shared/CONVENTIONS.md` — the locked format spec all shorts obey.

## Status / blockers

- ⛔ **WC.csv does not exist yet** — the hard blocker. `generate_previews.py` and the assembler can't produce real videos until the sourced WC fetcher lands history data (FIFA/Wikipedia/RSSSF — source still TBD).
- ⚠ chart.html still parses the OLD 3-col layout (`Team,Player,Color,…`); `charts/*.csv` use it to stay renderable today. Migrate both to the 5-col standard (`Player,Team,Competition,Color,Photo,…`) together later.
- This dir is sample-first: validate the creative on one fixture before building the generator for all 104.
