#!/usr/bin/env python3
"""Build data/h2h_short.csv — the render input for shorts/render_all.js.

Joins the stats (data/h2h_flat.csv, produced by build_h2h_cards.py) with the
schedule (fixtures.csv) to add the per-game render metadata the card needs:
venue, city, stadium, datetime ("June 11, 2026").

Run after build_h2h_cards.py whenever the stat columns change.
Usage: python3 scripts/wc26/build_render_input.py
"""
import csv
import os
from datetime import date

HERE = os.path.dirname(__file__)
FLAT = os.path.join(HERE, "data", "h2h_flat.csv")
FIXTURES = os.path.join(HERE, "fixtures.csv")
OUT = os.path.join(HERE, "data", "h2h_short.csv")

MONTHS = ["", "January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


def nice_date(iso, time=""):
    try:
        y, m, d = (int(x) for x in iso.split("-"))
        base = f"{MONTHS[m]} {d} {y}"   # no comma — renderer CSV parser is comma-split
    except Exception:
        base = iso
    return f"{base} · {time}" if time else base


def main():
    fx = {r["match_no"]: r for r in csv.DictReader(open(FIXTURES))}
    flat = list(csv.DictReader(open(FLAT)))
    stat_cols = [c for c in flat[0].keys()]
    extra = ["venue", "city", "stadium", "datetime"]
    out_rows = []
    for r in flat:
        f = fx.get(r["match_no"], {})
        r = dict(r)
        r["venue"] = f.get("venue", "")
        r["city"] = f.get("city", "")
        r["stadium"] = f.get("venue", "")          # card shows venue as stadium name
        # optional kickoff time, e.g. "19:00 CET" — empty until a 2026 source exists
        r["datetime"] = nice_date(f.get("date", ""), f.get("time", ""))
        out_rows.append(r)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=stat_cols + extra)
        w.writeheader()
        w.writerows(out_rows)
    print(f"Wrote {len(out_rows)} rows -> data/h2h_short.csv  ({len(stat_cols)+len(extra)} cols)")


if __name__ == "__main__":
    main()
