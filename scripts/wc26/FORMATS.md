# WC content — the two video formats and their stats

Both read the SAME source: `data/teams/<CODE>.matches.csv` (one row per WC match).
Assists are OUT of scope for WC (free sources unreliable pre-2010). We track only:
**games played, W / D / L, goals for, goals against** → from which points & ranks derive.

---

## FORMAT 1 — All-time LINE RACE (the 20-team chart.html format)

Cumulative line race across EVERY World Cup match, 1930 → 2022. x-axis = match sequence
(chronological). Two flavors:

### 1a. Team POINTS race
- Per match, award 3/1/0 (W/D/L). Cumulative running total per nation.
- Top-N nations (20) race; lines climb and overtake. THIS is where the race format shines.
- Derived from `result` column. (Note: 3-pts-for-win is modern; we apply it uniformly
  across history as a consistent scoring rule, stated on-screen.)

### 1b. Team GOALS race  (or all-time GOALSCORERS race)
- Cumulative goals_for per nation across all matches → team goals race.
- OR cumulative goals per PLAYER across all WCs → all-time top-scorers race
  (needs a players-by-match goals source; bigger fetch — Phase 2).

**Data requirement:** MATCH-BY-MATCH for every team. x-axis tick = one match.
⚠ Edition-summary rows (like current MEX) CANNOT feed this — only give per-tournament dots.

---

## FORMAT 2 — Two-team H2H CARD (the preview-short format)

Split screen, **team A top / team B bottom**, numbers count up. Compares the two
fixture teams on a fixed stat block:

| stat | source | example (MEX vs RSA) |
|---|---|---|
| World Cups attended | count distinct `year` | 17 vs 3 |
| Highest finish (rank) | best `stage` reached ever | QF vs Group |
| Avg finish | mean placing across editions | ~12th vs ~20th |
| WC matches P–W–D–L | count + `result` tally | 60 (17-15-28) vs 9 (2-4-3) |
| Goals F–A | sum `gf` / `ga` | 62–101 vs 11–16 |
| **H2H meetings** | derived: rows where opponent = other team | 1 (2010, 1–1 draw) |

**Data requirement:** Works from EITHER match-level OR edition-summary rows — EXCEPT the
H2H-meetings line, which needs match-level on at least one side to recover the meeting.
(MEX is edition-summary but RSA is match-level and lists MEX as opponent → we still recover
the 2010 meeting. ✓)

---

## So: do we need match-by-match for everyone?
- **FORMAT 2 (previews):** edition-summary is ENOUGH for 5 of 6 stats; H2H recovered if
  at least one side has match rows. → can ship previews on lighter data.
- **FORMAT 1 (line race):** REQUIRES match-by-match for all teams. → the heavier fetch,
  needed before the 20-team points/goals race videos.

Build order implied: previews first (lighter), all-time race second (needs full match data).
```
