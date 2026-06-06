#!/usr/bin/env python3
"""Dump the H2H stat block for ALL 104 fixtures into one reviewable table.

Resolves fixtures→team data by NAME (robust to FIFA-vs-ISO code differences).
Reuses the computation in compute_h2h.py. Output:
  data/h2h_all.csv   (one row per fixture, machine-readable)
  + prints a human table to stdout.

Usage: python3 scripts/wc26/dump_all_h2h.py
"""
import csv
import os
import sys

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
import compute_h2h as H  # reuse summarize/meetings/rank_label

TEAMS = os.path.join(HERE, "data", "teams")
FIXTURES = os.path.join(HERE, "fixtures.csv")

# Fixture display name -> data display name, where they differ.
NAME_FIX = {
    "USA": "United States",
    "DR Congo": "Zaire",                 # COD plays as Zaire in historical data
    "Turkey": "Turkey", "Czech Republic": "Czech Republic",
    "Bosnia & Herzegovina": "Bosnia and Herzegovina",
    "South Korea": "South Korea",
}

# Build name -> code index from the data files.
NAME_TO_CODE = {}
for fn in os.listdir(TEAMS):
    if fn.endswith(".matches.csv"):
        with open(os.path.join(TEAMS, fn)) as f:
            r = next(csv.reader(f)); row = next(csv.reader(f))
            NAME_TO_CODE[row[1]] = row[0]


def code_for(fixture_name):
    name = NAME_FIX.get(fixture_name, fixture_name)
    return NAME_TO_CODE.get(name)  # None = debutant / no WC history


def block(code):
    if code is None:
        return None
    return H.summarize(code)


def main():
    fixtures = list(csv.DictReader(open(FIXTURES)))
    out_rows = []
    print(f"{'#':>3}  {'FIXTURE':<34} {'WCs':>7}  {'BEST':>11}  {'P-W-D-L':>16}  {'GF-GA':>9}  H2H")
    print("-" * 110)
    for fx in fixtures:
        a_name, b_name = fx["team_a"], fx["team_b"]
        if a_name == "TBD":  # knockout slot, teams not resolved
            print(f"{fx['match_no']:>3}  {fx['slug']:<34} (knockout — teams TBD)")
            out_rows.append({"match_no": fx["match_no"], "slug": fx["slug"],
                             "phase": fx["phase"], "status": "TBD"})
            continue
        ca, cb = code_for(a_name), code_for(b_name)
        sa, sb = block(ca), block(cb)
        ms = H.meetings(ca, cb) if (ca and cb) else []

        def fmt(s):
            if s is None:
                return ("0", "Debut", "0  0-0-0", "0-0")
            return (str(s["attended"]), H.rank_label(s["highest_rank"]),
                    f"{s['P']}  {s['W']}-{s['D']}-{s['L']}", f"{s['gf']}-{s['ga']}")
        wa, ba, pa, ga = fmt(sa)
        wb, bb, pb, gb = fmt(sb)
        label = f"{a_name} vs {b_name}"
        print(f"{fx['match_no']:>3}  {label:<34} {wa:>3}/{wb:<3}  {ba:>5}/{bb:<5}".ljust(70)
              + f"  {ga:>4}|{gb:<4}  meet:{len(ms)}")
        out_rows.append({
            "match_no": fx["match_no"], "slug": fx["slug"], "phase": fx["phase"],
            "team_a": a_name, "a_wcs": wa, "a_best": ba, "a_pwdl": pa, "a_gfga": ga,
            "team_b": b_name, "b_wcs": wb, "b_best": bb, "b_pwdl": pb, "b_gfga": gb,
            "h2h_meetings": len(ms),
            "h2h_detail": " | ".join(f"{m[0]} {m[1]}: {m[2]} {m[4]}-{m[5]} {m[3]}" for m in ms),
            "status": "ok",
            "a_resolved": "" if sa else "NO-DATA", "b_resolved": "" if sb else "NO-DATA",
        })

    cols = ["match_no", "slug", "phase", "team_a", "a_wcs", "a_best", "a_pwdl", "a_gfga",
            "team_b", "b_wcs", "b_best", "b_pwdl", "b_gfga", "h2h_meetings", "h2h_detail",
            "a_resolved", "b_resolved", "status"]
    out_path = os.path.join(HERE, "data", "h2h_all.csv")
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(out_rows)
    print(f"\nWrote {len(out_rows)} rows → {out_path}")


if __name__ == "__main__":
    main()
