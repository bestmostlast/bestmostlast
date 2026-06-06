#!/usr/bin/env python3
"""Transform the vendored Fjelstul match dataset → per-team data/teams/<CODE>.matches.csv
   AND per-player data/teams/<CODE>.players.csv (goals only; assists out of scope for WC).

Source: github.com/jfjelstul/worldcup (MIT). Men's tournaments only.
One source file → all 48 teams at once. Verified: Mexico = P60 17-15-28 GF62 GA101.

Usage: python3 scripts/wc26/build_team_data.py
"""
import csv
import os
from collections import defaultdict

HERE = os.path.dirname(__file__)
SRC_MATCHES = os.path.join(HERE, "data", "source", "fjelstul_matches.csv")
SRC_GOALS = os.path.join(HERE, "data", "source", "fjelstul_goals.csv")
OUT = os.path.join(HERE, "data", "teams")

# Dataset uses ISO-3 codes; we standardize on FIFA codes used in fixtures.csv where they differ.
ISO_TO_FIFA = {"ZAF": "RSA", "NLD": "NED", "DEU": "GER", "CHE": "SUI", "DNK": "DEN",
               "KOR": "KOR", "PRT": "POR", "HRV": "CRO", "URY": "URU", "SRB": "SRB",
               "IRN": "IRN", "JPN": "JPN", "SAU": "KSA", "POL": "POL"}

STAGE_MAP = {
    "group stage": "group", "second group stage": "group2", "final round": "group",
    "round of 16": "r16", "quarter-final": "qf", "quarter-finals": "qf",
    "semi-final": "sf", "semi-finals": "sf", "third-place match": "third",
    "final": "final",
}


def fifa(code):
    return ISO_TO_FIFA.get(code, code)


def year_of(tournament_name):
    return tournament_name[:4]


def build_matches():
    rows = [r for r in csv.DictReader(open(SRC_MATCHES))
            if "Men's" in r["tournament_name"] and r["replay"] != "1"]
    # group rows per team, ordered by date
    per_team = defaultdict(list)
    for r in rows:
        for side in ("home", "away"):
            code = fifa(r[f"{side}_team_code"])
            opp_side = "away" if side == "home" else "home"
            gf = int(r[f"{side}_team_score"]); ga = int(r[f"{opp_side}_team_score"])
            result = "W" if gf > ga else ("D" if gf == ga else "L")
            # knockout draws resolved by ET/pens still count as D for the W-D-L record (FIFA convention)
            per_team[code].append({
                "code": code, "team": r[f"{side}_team_name"],
                "year": year_of(r["tournament_name"]),
                "stage": STAGE_MAP.get(r["stage_name"], r["stage_name"]),
                "match_no_wc": 0,  # filled after sort
                "opponent": r[f"{opp_side}_team_name"],
                "opponent_code": fifa(r[f"{opp_side}_team_code"]),
                "gf": gf, "ga": ga, "result": result,
                "host": "", "note": "", "_date": r["match_date"],
            })
    cols = ["code", "team", "year", "stage", "match_no_wc", "opponent",
            "opponent_code", "gf", "ga", "result", "host", "note"]
    os.makedirs(OUT, exist_ok=True)
    for code, ms in per_team.items():
        ms.sort(key=lambda x: x["_date"])
        for i, m in enumerate(ms, 1):
            m["match_no_wc"] = i; m.pop("_date")
        with open(os.path.join(OUT, f"{code}.matches.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(ms)
    return per_team


def build_players():
    if not os.path.exists(SRC_GOALS):
        print("  (no goals.csv — skipping players)"); return {}
    rows = [r for r in csv.DictReader(open(SRC_GOALS)) if "Men's" in r["tournament_name"]]
    # own goals are credited to scoring player's team in this dataset; keep simple: count all
    tally = defaultdict(lambda: defaultdict(lambda: {"goals": 0, "years": set()}))
    names = {}
    for r in rows:
        code = fifa(r["player_team_code"])
        pid = r["player_id"]
        given = "" if r["given_name"].strip().lower() == "not applicable" else r["given_name"]
        family = "" if r["family_name"].strip().lower() == "not applicable" else r["family_name"]
        full = f"{given} {family}".strip()
        names[(code, pid)] = full
        tally[code][pid]["goals"] += 1
        tally[code][pid]["years"].add(year_of(r["tournament_name"]))
    cols = ["code", "player", "wc_goals", "wc_assists", "wc_apps", "years", "note"]
    out = {}
    for code, players in tally.items():
        recs = []
        for pid, d in sorted(players.items(), key=lambda kv: -kv[1]["goals"]):
            recs.append({"code": code, "player": names[(code, pid)],
                         "wc_goals": d["goals"], "wc_assists": "", "wc_apps": "",
                         "years": ";".join(sorted(d["years"])), "note": ""})
        with open(os.path.join(OUT, f"{code}.players.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(recs)
        out[code] = recs
    return out


if __name__ == "__main__":
    teams = build_matches()
    players = build_players()
    print(f"Wrote match files for {len(teams)} teams → {OUT}")
    # quick verification
    for code in ("MEX", "RSA", "BRA"):
        ms = list(csv.DictReader(open(os.path.join(OUT, f"{code}.matches.csv"))))
        W = sum(m["result"] == "W" for m in ms); D = sum(m["result"] == "D" for m in ms)
        L = sum(m["result"] == "L" for m in ms)
        gf = sum(int(m["gf"]) for m in ms); ga = sum(int(m["ga"]) for m in ms)
        print(f"  {code}: P{len(ms)} {W}-{D}-{L} GF{gf} GA{ga}")
