---
id: wc26-shorts-csv-contactsheets
scope: bestmostlast
status: partial
reported: 2026-06-06
---
**Input:** Prepare the WC26 Shorts review material — a data CSV + side-by-side S0–S5 contact sheets for all 72 group-stage matches. No video rendering.

**Output:**
- `scripts/wc26/data/master_cards.csv` — 72 rows × 33 cols, human-readable, every on-card text/number grouped by screen (S0 splash · S1 records · S2 H2H · S3 players-to-watch · S4 storyline · S5 lineups). Editable in a spreadsheet.
- All **72 contact sheets** rendered: `scripts/wc26/shorts/<slug>/export/contact.png` — the 6 screens montaged side-by-side per match (review-only, no MP4).
- Card redesigned to the 6-screen timeline; storyline/watch-list logic frames small teams positively and only names curated current stars (no retired-player fallback).

**Open items / blockers:**
- Player photos NOT good enough — wrong faces (e.g. Arda Güler) + many silhouettes. **Deferred by user to 2026-06-10** (fix headshots in `_shared/players/`, re-run contact sheets, then video).
- MP4 batch for the 6-screen design not yet run — awaiting user go-ahead.
- Voiceover deferred to ~June 8-9. Knockouts m073–104 TBD until bracket resolves. No kickoff times sourced (date only).
