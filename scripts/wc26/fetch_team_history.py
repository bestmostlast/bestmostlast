#!/usr/bin/env python3
"""Fetch per-team World Cup history for all WC26 nations → data/teams/<CODE>.{matches,players}.csv

Status: SCAFFOLD. Mexico (MEX) + South Africa (RSA) are hand-built and verified.
This automates the remaining ~46 from Wikipedia "<Country> at the FIFA World Cup".

Sourcing reality (see bestmostlast-data-source-strategy memory): Wikipedia tables are
the most reliable free source; FBref is Cloudflare-blocked, TM is a JS app. We parse
the per-tournament "Record" table (per-edition rows) — match-by-match is a later upgrade
where a clean source exists.

Run:
    python3 scripts/wc26/fetch_team_history.py --team MEX     # one team
    python3 scripts/wc26/fetch_team_history.py --all          # every WC26 team
    python3 scripts/wc26/fetch_team_history.py --derive-h2h   # build h2h/ from teams/
"""
import argparse
import csv
import os
import sys

# WC26 nations → (FIFA code, Wikipedia page title). Codes match fixtures.csv / data/teams/.
# Hand-built already: MEX, RSA.
TEAMS = {
    "MEX": "Mexico", "RSA": "South Africa", "CAN": "Canada", "USA": "United States",
    "BRA": "Brazil", "ARG": "Argentina", "FRA": "France", "ENG": "England",
    "ESP": "Spain", "GER": "Germany", "NED": "Netherlands", "POR": "Portugal",
    "CRO": "Croatia", "BEL": "Belgium", "URU": "Uruguay", "JPN": "Japan",
    "KOR": "South Korea", "MAR": "Morocco", "SUI": "Switzerland", "SEN": "Senegal",
    "AUS": "Australia", "SWE": "Sweden", "DEN": "Denmark", "QAT": "Qatar",
    "EGY": "Egypt", "IRN": "Iran", "GHA": "Ghana", "CIV": "Ivory Coast",
    "ECU": "Ecuador", "TUN": "Tunisia", "CMR": "Cameroon", "NGA": "Nigeria",
    "COL": "Colombia", "PAR": "Paraguay", "SCO": "Scotland", "NOR": "Norway",
    "AUT": "Austria", "TUR": "Turkey", "ALG": "Algeria", "JOR": "Jordan",
    "UZB": "Uzbekistan", "CPV": "Cape Verde", "CUW": "Curacao", "HAI": "Haiti",
    "NZL": "New Zealand", "PAN": "Panama", "BIH": "Bosnia and Herzegovina",
    "KSA": "Saudi Arabia", "COD": "DR Congo", "IRQ": "Iraq", "CZE": "Czech Republic",
}

HAND_BUILT = {"MEX", "RSA"}  # do not overwrite

OUT_DIR = os.path.join(os.path.dirname(__file__), "data", "teams")
MATCH_COLS = ["code", "team", "year", "stage", "match_no_wc", "opponent",
              "opponent_code", "gf", "ga", "result", "host", "note"]
PLAYER_COLS = ["code", "player", "wc_goals", "wc_assists", "wc_apps", "years", "note"]


def fetch_team(code):
    """TODO: fetch + parse Wikipedia '<Country> at the FIFA World Cup'.

    Recommended approach (kept out of this scaffold so it stays runnable offline):
      1. GET https://en.wikipedia.org/wiki/<Title>_at_the_FIFA_World_Cup
      2. Parse the 'FIFA World Cup record' wikitable → one EDITION-SUMMARY row per year
         (year, gf, ga, host, finish→stage).
      3. Parse the top-scorers table → players.csv rows.
      4. Match-by-match: only where a clean per-match table exists (small teams like RSA).
    Use requests + a tolerant HTML table parser; respect robots/ratelimit.
    """
    raise NotImplementedError(
        f"fetch_team({code}) not implemented yet — see docstring. "
        f"MEX/RSA are hand-built as the reference shape."
    )


def write_team(code, matches, players):
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, f"{code}.matches.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MATCH_COLS); w.writeheader(); w.writerows(matches)
    with open(os.path.join(OUT_DIR, f"{code}.players.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=PLAYER_COLS); w.writeheader(); w.writerows(players)


def derive_h2h(fixtures_csv):
    """Build data/h2h/<slug>.csv for every fixture, from the two teams' .matches.csv.

    A meeting exists when team A's matches list opponent == team B (and year/stage line up).
    For per-edition-summary teams we can't recover individual H2H — those fixtures get an
    empty h2h file + 'no match-level data' note, and the preview falls back to appearances.
    """
    h2h_dir = os.path.join(os.path.dirname(__file__), "data", "h2h")
    os.makedirs(h2h_dir, exist_ok=True)
    # TODO: implement the join once more teams have match-level rows.
    print("derive_h2h: scaffold — implement join over teams/*.matches.csv")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--team")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--derive-h2h", action="store_true")
    args = ap.parse_args()

    if args.derive_h2h:
        derive_h2h(os.path.join(os.path.dirname(__file__), "fixtures.csv"))
        return

    targets = []
    if args.team:
        targets = [args.team.upper()]
    elif args.all:
        targets = [c for c in TEAMS if c not in HAND_BUILT]
    else:
        ap.print_help(); sys.exit(1)

    for code in targets:
        if code in HAND_BUILT:
            print(f"{code}: hand-built, skipping."); continue
        if code not in TEAMS:
            print(f"{code}: unknown code."); continue
        try:
            matches, players = fetch_team(code)
            write_team(code, matches, players)
            print(f"{code}: wrote {len(matches)} match rows, {len(players)} players.")
        except NotImplementedError as e:
            print(f"{code}: {e}")


if __name__ == "__main__":
    main()
