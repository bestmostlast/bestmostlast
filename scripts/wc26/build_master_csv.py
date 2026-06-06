#!/usr/bin/env python3
"""Build a human-readable MASTER data CSV — every text/number shown on each screen,
grouped by screen (S0 header · S1 records · S2 H2H · S3 scorers · S4 storyline ·
S5 lineups), one row per match. Lets you review/edit the content of all 72 cards
in one spreadsheet without touching the renderer.

Reads data/h2h_short.csv. Writes data/master_cards.csv.
Usage: python3 scripts/wc26/build_master_csv.py
"""
import csv
import os

HERE = os.path.dirname(__file__)
SHORT = os.path.join(HERE, "data", "h2h_short.csv")
OUT = os.path.join(HERE, "data", "master_cards.csv")


def main():
    src = list(csv.DictReader(open(SHORT)))
    out_rows = []
    for r in src:
        g = r.get  # shorthand
        row = {
            "match": r["match_no"],
            "slug": r["slug"],
            # --- S0 / header ---
            "TEAM A": r["team_a"],
            "TEAM B": r["team_b"],
            "S0_stadium": g("stadium", ""),
            "S0_datetime": g("datetime", ""),
            # --- S1 all-time records (a | b) ---
            "S1_WorldCups": f"{g('WCs_a','')} | {g('WCs_b','')}",
            "S1_Won": f"{g('Won_a','')} | {g('Won_b','')}",
            "S1_Best(Avg)": f"{g('High_a','')}({g('Avg_a','')}) | {g('High_b','')}({g('Avg_b','')})",
            "S1_Played": f"{g('GP_a','')} | {g('GP_b','')}",
            "S1_W": f"{g('W_a','')} | {g('W_b','')}",
            "S1_D": f"{g('D_a','')} | {g('D_b','')}",
            "S1_L": f"{g('L_a','')} | {g('L_b','')}",
            "S1_GoalsFor(pg)": f"{g('GF_a','')}({g('GFpg_a','')}) | {g('GF_b','')}({g('GFpg_b','')})",
            "S1_GoalsAgainst(pg)": f"{g('GA_a','')}({g('GApg_a','')}) | {g('GA_b','')}({g('GApg_b','')})",
            "S1_Points(PPG)": f"{g('P_a','')}({g('PPG_a','')}) | {g('P_b','')}({g('PPG_b','')})",
            # --- S2 head-to-head (a | b) ---
            "S2_H2H_W": f"{g('H2H_W_a','')} | {g('H2H_W_b','')}",
            "S2_H2H_D": f"{g('H2H_D_a','')} | {g('H2H_D_b','')}",
            "S2_H2H_L": f"{g('H2H_L_a','')} | {g('H2H_L_b','')}",
            "S2_H2H_GF": f"{g('H2H_GF_a','')} | {g('H2H_GF_b','')}",
            "S2_H2H_GA": f"{g('H2H_GA_a','')} | {g('H2H_GA_b','')}",
            # --- S3 scorers / players to watch ---
            "S3_AllTime_A": f"{g('Top1_a','')}, {g('Top2_a','')}",
            "S3_AllTime_B": f"{g('Top1_b','')}, {g('Top2_b','')}",
            "S3_Watch_A": f"{g('Best1_a','') or g('Star1_a','')}, {g('Best2_a','') or g('Star2_a','')}",
            "S3_Watch_B": f"{g('Best1_b','') or g('Star1_b','')}, {g('Best2_b','') or g('Star2_b','')}",
            # --- S4 storyline (headline + hook per team) ---
            "S4_Headline_A": g("Headline_a", ""),
            "S4_Hook_A": g("Hook_a", ""),
            "S4_Headline_B": g("Headline_b", ""),
            "S4_Hook_B": g("Hook_b", ""),
            # --- S5 lineups ---
            "S5_Coach_A": g("Coach_a", ""),
            "S5_XI_A": " · ".join(
                f"{g(f'P{i}num_a','')} {g(f'P{i}name_a','')}".strip()
                for i in range(1, 12) if g(f"P{i}name_a", "")),
            "S5_Coach_B": g("Coach_b", ""),
            "S5_XI_B": " · ".join(
                f"{g(f'P{i}num_b','')} {g(f'P{i}name_b','')}".strip()
                for i in range(1, 12) if g(f"P{i}name_b", "")),
        }
        out_rows.append(row)

    cols = list(out_rows[0].keys())
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(out_rows)
    print(f"Wrote {len(out_rows)} rows × {len(cols)} cols → data/master_cards.csv")


if __name__ == "__main__":
    main()
