# Short m001 — Mexico vs South Africa (WC26 Opener)

**Format:** vertical 1080×1920 · 38s · YouTube Short
**Air:** ~12–24h before kickoff (June 10–11)
**Page funnel:** bestmostlast.com/wc26/m001-mexico-vs-south-africa

The video is assembled from 5 parts (= the 5 beats in `preview.json`).
Each part below = one screen segment. Build top to bottom.

---

## PART 1 — HOOK  (0:00–0:03, 3s)
**What:** Grab attention. Both flags slam in, title, one teaser line.
**On screen:** "MEXICO 🇲🇽 vs 🇿🇦 SOUTH AFRICA" / sub: "The World Cup begins · Estadio Azteca · June 11"
**Voice/caption:** "The World Cup starts HERE."
**Material needed:** flag-mex.png, flag-rsa.png, BML logo (corner), title font, whoosh SFX.
**Source:** `preview.json` → beats[0].

## PART 2 — H2H / CONTEXT  (0:03–0:10, 7s)
**What:** The record. These two have never met at a WC → "first meeting" framing.
**On screen:** "AT THE WORLD CUP" — Mexico 17th finals vs South Africa 4th.
**Voice/caption:** "Mexico — a World Cup mainstay since 1930. South Africa — back after 16 years."
**Material needed:** two stat cards (appearances), small flag icons, count-up number animation.
**Source:** `preview.json` → beats[1]. ⚠ verify appearance counts vs WC.csv.

## PART 3 — BML DUEL  (0:10–0:21, 11s)  ← THE SIGNATURE BEAT
**What:** The chart race. All-time WC goals, the two nations, animated by chart.html.
**On screen:** chart.html render of `chart/chart.csv` → Mexico ~60 vs South Africa ~11.
**Voice/caption:** "All-time World Cup goals. The gap says everything."
**Material needed:** rendered chart clip (see below), music bed, big team photos as overlay.
**Source:** `chart/chart.csv` → chart.html → `export/duel.webm`.
**How to render:** open `public/data/chart.html` → load `chart/chart.csv` → set 1080×1920, 11s, 30fps → Export → save to `export/duel.webm`.

## PART 4 — PLAYERS TO WATCH  (0:21–0:29, 8s)
**What:** One player per side, one headline stat each.
**On screen:** Santiago Giménez (MEX) / Lyle Foster (RSA), photo + one-line stat.
**Voice/caption:** "Eyes on these two."
**Material needed:** player-gimenez.png, player-foster.png (cutouts), name+stat lower-thirds.
**Source:** `preview.json` → beats[3]. ⚠ confirm starting XI players closer to kickoff.

## PART 5 — WHAT TO EXPECT + CTA  (0:29–0:38, 9s)
**What:** Honours line + prediction framing, then the call to action.
**On screen:** best finishes; "Full breakdown → bestmostlast.com".
**Voice/caption:** "Mexico open at home with a point to prove."
**Material needed:** honours cards, end-card with logo + URL + subscribe nudge.
**Source:** `preview.json` → beats[4] + `cta`.

---

## Material checklist for THIS short
- [ ] `assets/flag-mex.png`, `assets/flag-rsa.png`
- [ ] `assets/player-gimenez.png`, `assets/player-foster.png` (transparent cutouts)
- [ ] `chart/chart.csv` (done) → `export/duel.webm` (render step)
- [ ] Shared: logo, font, music, end-card (from `../_shared/`)
- [ ] Verify all `verify:true` stats against WC.csv (BLOCKED until WC.csv exists)
- [ ] Final assembled `export/m001-final.mp4`

## Output files (this folder)
```
preview.json          storyboard (source of truth for the script)
chart/chart.csv       2-team cumulative WC goals → chart.html
assets/               flags + player cutouts for THIS match
export/duel.webm      rendered chart beat (part 3)
export/m001-final.mp4 finished short
```
