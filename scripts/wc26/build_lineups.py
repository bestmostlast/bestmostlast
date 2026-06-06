#!/usr/bin/env python3
"""Editable starting-XI data for the S5 screen.

Creates (if missing) and reads scripts/wc26/lineups.csv — a blank, USER-EDITABLE
template with one row per match holding each team's coach + 11 players (number+name).
Then injects those fields into data/h2h_short.csv so the renderer can draw S5.

We have NO squad/lineup source yet (squads aren't finalized in early June 2026), so
this is filled by hand — your placeholder/expected XI now, refresh closer to kickoff.

Run AFTER build_render_input.py:
  python3 scripts/wc26/build_lineups.py
"""
import csv
import os
import re

HERE = os.path.dirname(__file__)
SHORT = os.path.join(HERE, "data", "h2h_short.csv")
LINEUPS = os.path.join(HERE, "lineups.csv")
TEAMS = os.path.join(HERE, "data", "teams")

# name → WC goals, across ALL team player files (best-effort surname match too).
GOALS_BY_NAME = {}
GOALS_BY_SURNAME = {}
if os.path.isdir(TEAMS):
    for fn in os.listdir(TEAMS):
        if fn.endswith(".players.csv"):
            for r in csv.DictReader(open(os.path.join(TEAMS, fn))):
                try:
                    g = int(r.get("wc_goals") or 0)
                except ValueError:
                    g = 0
                nm = (r.get("player") or "").strip()
                if nm:
                    GOALS_BY_NAME[nm] = max(GOALS_BY_NAME.get(nm, 0), g)
                    sur = nm.split()[-1]
                    GOALS_BY_SURNAME[sur] = max(GOALS_BY_SURNAME.get(sur, 0), g)


def player_goals(name):
    """Look up a player's WC goals by full name, else surname; 0 if unknown."""
    name = (name or "").strip()
    if name in GOALS_BY_NAME:
        return GOALS_BY_NAME[name]
    return GOALS_BY_SURNAME.get(name.split()[-1] if name else "", 0)

# per team: coach + 11 (number, name). columns suffixed _a / _b.
def team_fields(suf):
    cols = [f"Coach_{suf}"]
    for i in range(1, 12):
        cols += [f"P{i}num_{suf}", f"P{i}name_{suf}"]
    return cols

LINEUP_COLS = team_fields("a") + team_fields("b")


def ensure_template(rows):
    if os.path.exists(LINEUPS):
        return
    with open(LINEUPS, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["match_no", "team_a", "team_b"] + LINEUP_COLS)
        w.writeheader()
        for r in rows:
            w.writerow({"match_no": r["match_no"], "team_a": r["team_a"],
                        "team_b": r["team_b"]})
    print(f"  created editable lineups.csv (blank — fill in expected XIs)")


def main():
    rows = list(csv.DictReader(open(SHORT)))
    ensure_template(rows)
    # read whatever the user has filled
    lu = {r["match_no"]: r for r in csv.DictReader(open(LINEUPS))}
    by_no = {r["match_no"]: r for r in rows}
    for mn, r in by_no.items():
        src = lu.get(mn, {})
        for c in LINEUP_COLS:
            r[c] = (src.get(c) or "").strip()
        # PLAYERS TO WATCH (S3) = the TOP 2 SCORERS among the starting XI (ranked by
        # WC goals). Falls back to existing Star/recent values when no XI is filled.
        for suf in ("a", "b"):
            xi = [r.get(f"P{i}name_{suf}", "").strip() for i in range(1, 12)]
            xi = [n for n in xi if n]
            ranked = sorted(xi, key=player_goals, reverse=True)
            r[f"Best1_{suf}"] = ranked[0] if len(ranked) >= 1 else ""
            r[f"Best2_{suf}"] = ranked[1] if len(ranked) >= 2 else ""
    cols = list(rows[0].keys())
    for c in LINEUP_COLS + ["Best1_a", "Best2_a", "Best1_b", "Best2_b"]:
        if c not in cols:
            cols.append(c)
    with open(SHORT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader(); w.writerows(rows)
    filled = sum(1 for r in rows if r.get("P1name_a"))
    print(f"  merged lineups into h2h_short.csv  ({filled}/{len(rows)} matches have XIs)")


if __name__ == "__main__":
    main()
