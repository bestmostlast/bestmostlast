#!/usr/bin/env python3
"""Build the H2H comparison data in the user's Sheet-3 CARD layout, for all 104 fixtures.

Two outputs (both requested):
  data/h2h_cards.csv  — STACKED cards: each fixture = a ~14-row block in the visual
                        split-card layout (left=team_a, center=label, right=team_b).
  data/h2h_flat.csv   — FLAT table: one ROW per fixture, every metric as a column
                        (WCs_a, High_a, Avg_a, GP_a, W_a, D_a, L_a, GF_a, GA_a,
                         P_a, PPG_a, H2h_a, then _b). Easy to scan all 104.

Metrics per team (the user's Sheet-3 rows):
  WCs, High, Avg, GP, W, D, L, GF, GA, P (=3W+D), PPG (=P/GP), H2h (meetings won)
High = best (lowest) final placing ever; Avg = mean placing across all their WCs.
Placing by round reached (FIFA-style band mid-points).

Usage: python3 scripts/wc26/build_h2h_cards.py
"""
import csv
import os
import statistics

HERE = os.path.dirname(__file__)
TEAMS = os.path.join(HERE, "data", "teams")
FIXTURES = os.path.join(HERE, "fixtures.csv")
TOURNAMENTS = os.path.join(HERE, "data", "source", "fjelstul_tournaments.csv")

# round reached -> final placing band mid-point
PLACE = {"sf": 3.5, "qf": 6.5, "r16": 12.5, "group2": 12.5, "group": 24}
NAME_FIX = {"USA": "United States", "DR Congo": "Zaire",
            "Bosnia & Herzegovina": "Bosnia and Herzegovina"}

# name -> code index from data files
NAME_TO_CODE = {}
CODE_TO_NAME = {}
for fn in os.listdir(TEAMS):
    if fn.endswith(".matches.csv"):
        with open(os.path.join(TEAMS, fn)) as f:
            next(f); row = next(csv.reader([f.readline()])) if False else next(csv.reader(f))
            NAME_TO_CODE[row[1]] = row[0]
            CODE_TO_NAME[row[0]] = row[1]

# winner-name aliases → the modern team that should be credited.
# West Germany's 3 titles (1954/74/90) belong to unified Germany (GER), whose
# team data already merges the West-German matches. Without this they'd be lost.
WINNER_ALIAS = {"West Germany": "Germany"}

# code -> number of MEN'S World Cups WON (titles), from the tournaments winner column.
# NOTE: the source file mixes in 8 Women's World Cups (1991+) — exclude them so a
# men's-team card doesn't credit women's titles (e.g. USA men = 0, not 4).
TITLES_BY_CODE = {}
for t in csv.DictReader(open(TOURNAMENTS)):
    if "women" in t.get("tournament_name", "").lower():
        continue
    win_name = t.get("winner", "").strip()
    win_name = WINNER_ALIAS.get(win_name, win_name)
    code = NAME_TO_CODE.get(win_name)
    if code:
        TITLES_BY_CODE[code] = TITLES_BY_CODE.get(code, 0) + 1


def rows_for(code):
    p = os.path.join(TEAMS, f"{code}.matches.csv")
    return list(csv.DictReader(open(p))) if os.path.exists(p) else []


def _players(code):
    p = os.path.join(TEAMS, f"{code}.players.csv")
    return list(csv.DictReader(open(p))) if os.path.exists(p) else []


def _goals(r):
    try:
        return int(r.get("wc_goals") or 0)
    except ValueError:
        return 0


def _fmt(p):
    return f"{p[0]} ({p[1]})"


def top_scorers(code, n=2):
    """Top-n ALL-TIME WC scorers as ['Name (G)', ...] (padded to n with '')."""
    scored = [(r["player"], _goals(r)) for r in _players(code) if _goals(r)]
    scored.sort(key=lambda p: p[1], reverse=True)
    out = [_fmt(p) for p in scored[:n]]
    return out + [""] * (n - len(out))


def recent_scorers(code, n=2):
    """Top-n MOST-RECENT-WC (active-era) scorers — players who featured in 2022/2018,
    ranked by goals. Padded to n. Falls back to all-time if none recent."""
    rec = [(r["player"], _goals(r)) for r in _players(code)
           if ("2022" in (r.get("years") or "") or "2018" in (r.get("years") or ""))]
    rec.sort(key=lambda p: p[1], reverse=True)
    out = [_fmt(p) for p in rec[:n]]
    if not out:
        return top_scorers(code, n)
    return out + [""] * (n - len(out))


def placing_for_year(rows):
    stages = {r["stage"] for r in rows}
    if "final" in stages:
        fr = next(r for r in rows if r["stage"] == "final")
        return 1 if fr["result"] == "W" else 2
    for st in ("sf", "qf", "r16", "group2", "group"):
        if st in stages:
            return PLACE[st]
    return 24


def card_stats(code):
    rows = rows_for(code)
    if not rows:
        return None
    titles = TITLES_BY_CODE.get(code, 0)
    W = sum(r["result"] == "W" for r in rows)
    D = sum(r["result"] == "D" for r in rows)
    L = sum(r["result"] == "L" for r in rows)
    gf = sum(int(r["gf"]) for r in rows)
    ga = sum(int(r["ga"]) for r in rows)
    P = 3 * W + D
    GP = len(rows)
    by_year = {}
    for r in rows:
        by_year.setdefault(r["year"], []).append(r)
    placings = [placing_for_year(rs) for rs in by_year.values()]
    return {
        "WCs": len(by_year), "Won": titles, "High": min(placings),
        "Avg": round(statistics.mean(placings), 1), "GP": GP,
        "W": W, "D": D, "L": L, "GF": gf, "GA": ga, "P": P,
        "PPG": round(P / GP, 2) if GP else 0,
        "GFpg": round(gf / GP, 2) if GP else 0,
        "GApg": round(ga / GP, 2) if GP else 0,
    }


def code_for(name):
    return NAME_TO_CODE.get(NAME_FIX.get(name, name))


# best-placing band → words
PLACE_WORD = {1: "Champions", 2: "Finalists", 3.5: "Semi-finalists",
              6.5: "Quarter-finalists", 12.5: "Round of 16", 24: "Group stage"}


def best_word(high):
    return PLACE_WORD.get(high, "Group stage")


def make_comment(stats, ha, opp):
    """One data-driven line per team: record headline + H2H vs opponent.
    e.g. '17 World Cups · best: Quarter-finals · 1-1 vs South Africa'."""
    if not stats:
        return ""
    titles = stats["Won"]
    record = (f"{titles}x Champions" if titles
              else f"Best: {best_word(stats['High'])}")
    if ha["GP"]:
        h2h = f"{ha['W']}-{ha['D']}-{ha['L']} vs {opp}"
    else:
        h2h = f"1st meeting vs {opp}"
    return f"{stats['WCs']} World Cups · {record} · {h2h}"


# The player to HIGHLIGHT on S4 per nation (the "face" of the team for 2026),
# which is NOT always the all-time/recent top scorer (e.g. Türkiye → Arda Güler).
# These names must have a photo in _shared/highlight/ or _shared/players/.
# Curated CURRENT marquee player per 2026 nation — the "player to watch".
# These are present-day internationals expected in the 2026 squad (verified
# against published WC2026 squads for the less-familiar teams), NEVER historical
# top scorers. Used for S3 watch-list + S4 hook when no starting XI is filled.
STAR_BY_TEAM = {
    # marquee
    "Argentina": "Lionel Messi",
    "Portugal": "Cristiano Ronaldo",
    "Türkiye": "Arda Güler",
    "Turkey": "Arda Güler",
    "England": "Harry Kane",
    "France": "Kylian Mbappé",
    "Brazil": "Vinicius Junior",
    "Norway": "Erling Haaland",
    "Egypt": "Mohamed Salah",
    "Poland": "Robert Lewandowski",
    "Croatia": "Luka Modrić",
    "South Korea": "Heung-min Son",
    # rest of the field (current stars)
    "Spain": "Lamine Yamal",
    "Germany": "Jamal Musiala",
    "Netherlands": "Virgil van Dijk",
    "Belgium": "Kevin De Bruyne",
    "Uruguay": "Federico Valverde",
    "Colombia": "Luis Díaz",
    "Morocco": "Achraf Hakimi",
    "Japan": "Kaoru Mitoma",
    "Senegal": "Sadio Mané",
    "Switzerland": "Granit Xhaka",
    "Austria": "Marcel Sabitzer",
    "Mexico": "Santiago Giménez",
    "USA": "Christian Pulisic",
    "Ecuador": "Moisés Caicedo",
    "Australia": "Jackson Irvine",
    "Algeria": "Riyad Mahrez",
    "Ivory Coast": "Sébastien Haller",
    "Ghana": "Mohammed Kudus",
    "Tunisia": "Hannibal Mejbri",
    "Czech Republic": "Patrik Schick",
    "Sweden": "Alexander Isak",
    "Scotland": "Scott McTominay",
    "Canada": "Alphonso Davies",
    "Iran": "Mehdi Taremi",
    "Saudi Arabia": "Salem Al-Dawsari",
    "Qatar": "Akram Afif",
    "Iraq": "Aymen Hussein",
    "South Africa": "Percy Tau",
    "Paraguay": "Miguel Almirón",
    "Panama": "Aníbal Godoy",
    "New Zealand": "Chris Wood",
    "Bosnia & Herzegovina": "Edin Džeko",
    "Bosnia and Herzegovina": "Edin Džeko",
    "DR Congo": "Cédric Bakambu",
    "Haiti": "Duckens Nazon",
    # 2026 debutants (verified vs published squads)
    "Cape Verde": "Ryan Mendes",
    "Curacao": "Tahith Chong",
    "Curaçao": "Tahith Chong",
    "Jordan": "Mousa Al-Tamari",
    "Uzbekistan": "Abdukodir Khusanov",
}

# Hand-curated newspaper hooks for marquee players (override the template).
# Keyed by the player's name as it appears in the data.
MARQUEE_HOOKS = {
    "Lionel Messi": "MESSI — THE LAST DANCE",
    "Cristiano Ronaldo": "RONALDO — ONE LAST CROWN?",
    "Neymar": "NEYMAR'S REDEMPTION",
    "Kylian Mbappé": "MBAPPÉ — THE HEIR TO THE THRONE",
    "Harry Kane": "KANE HUNTS THE CROWN",
    "Robert Lewandowski": "LEWANDOWSKI'S FINAL CHARGE",
    "Luka Modrić": "MODRIĆ — ONE MORE MIRACLE?",
    "Karim Benzema": "BENZEMA LEADS THE LINE",
    "Heung-min Son": "SON CARRIES KOREA'S HOPES",
    "Mohamed Salah": "SALAH — THE PHARAOH RETURNS",
    "Vinicius Junior": "VINI JR. — THE NEW KING?",
    "Erling Haaland": "HAALAND — THE GOAL MACHINE",
    "Arda Güler": "CAN ARDA SHINE AGAIN?",
    "Hakan Çalhanoğlu": "HAKAN PULLS THE STRINGS",
}


# Varied templated hooks (deterministic per player so they don't change run-to-run).
HOOK_TEMPLATES = [
    "ALL EYES ON {S}",
    "CAN {S} DELIVER?",
    "{S} LEADS THE CHARGE",
    "{S} — THE TALISMAN",
    "{S} CARRIES THE HOPES",
    "{S} OUT TO MAKE HISTORY",
    "{S} — THE ONE TO WATCH",
    "{S} READY FOR THE STAGE",
]


def team_hook(team):
    """Team-focused hook used when NO confirmed 2026 star is set (avoids naming a
    retired/uncertain player). Deterministic per team name."""
    opts = ["EYES ON THE FINAL SQUAD", "WHO STEPS UP?", "READY FOR THE STAGE",
            "OUT TO MAKE THEIR MARK", "THE BIG STAGE AWAITS", "ALL TO PLAY FOR"]
    return opts[sum(ord(c) for c in (team or "")) % len(opts)]


def player_hook(star1):
    """Newspaper hook for a team's star: marquee override, else a VARIED template
    chosen deterministically from the player's name. '' if no star given."""
    name = (star1 or "").split(" (")[0].strip()
    if not name:
        return ""
    if name in MARQUEE_HOOKS:
        return MARQUEE_HOOKS[name]
    surname = name.split()[-1].upper()
    idx = sum(ord(c) for c in name) % len(HOOK_TEMPLATES)
    return HOOK_TEMPLATES[idx].format(S=surname)


def make_headline(stats):
    """A punchy, FACT-BASED headline per team, REALISTIC to its stature.
    'Still no crown' is only for big nations with many attempts; minnows get
    underdog/milestone framing. No commas (renderer CSV parser is comma-split)."""
    if not stats:
        return "FIRST-EVER WORLD CUP"
    wc, won, high = stats["WCs"], stats["Won"], stats["High"]
    if wc == 0:
        return "FIRST-EVER WORLD CUP"
    # champions
    if won >= 4:
        return f"{won}-TIME WORLD CHAMPIONS"
    if won >= 1:
        return f"{won}x CHAMPIONS · CHASING MORE GLORY"
    # non-champions: branch on how deep they've gone AND how often they've tried
    if high == 2:
        return "RUNNERS-UP ONCE · STILL CHASING THE CROWN"
    if high == 3.5:
        return "SEMI-FINALISTS · THE NEARLY MEN"
    if high == 6.5:
        # quarter-finals as ceiling — only "underachiever" framing if MANY tries
        if wc >= 10:
            return f"{wc} TRIES · NEVER PAST THE QUARTERS"
        return "QUARTER-FINALS THEIR FINEST HOUR"
    if high == 12.5:
        return "ROUND OF 16 · OUT TO GO FURTHER"
    # never out of the group → frame as OVERACHIEVING / chasing a best-ever run,
    # NOT as "should-be champions". Small nations aren't underdogs failing — they're
    # punching up.
    if wc <= 1:
        return "ON THE GREATEST STAGE"
    if wc <= 3:
        return f"{wc} WORLD CUPS · OUT TO MAKE THEIR MARK"
    if wc >= 8:
        return f"{wc} TRIES · CHASING A FIRST KNOCKOUT"
    return f"{wc} WORLD CUPS · EYEING A BREAKTHROUGH"


def h2h_tally(ca, cb):
    """Full head-to-head from A's perspective, over the matches between A and B.
    Returns dict for A (GP/W/D/L/GF/GA) and the mirror for B."""
    a = {"GP": 0, "W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0}
    for r in rows_for(ca):
        if r.get("opponent_code") == cb:
            a["GP"] += 1
            a["GF"] += int(r["gf"]); a["GA"] += int(r["ga"])
            a["W"] += r["result"] == "W"
            a["D"] += r["result"] == "D"
            a["L"] += r["result"] == "L"
    # B's view is the mirror of A's
    b = {"GP": a["GP"], "W": a["L"], "D": a["D"], "L": a["W"],
         "GF": a["GA"], "GA": a["GF"]}
    return a, b


# all-time card rows, then the head-to-head sub-block rows (prefixed H2H)
ROWS = ["WCs", "Won", "High", "Avg", "GP", "W", "D", "L",
        "GF", "GFpg", "GA", "GApg", "P", "PPG"]
H2H_ROWS = ["GP", "W", "D", "L", "GF", "GA"]


# Fields the user may override per match in overrides.csv (blank = use auto value).
OVERRIDE_FIELDS = ["Headline_a", "Headline_b", "Hook_a", "Hook_b",
                   "Comment_a", "Comment_b", "Star1_a", "Star1_b"]
OVERRIDES = os.path.join(HERE, "overrides.csv")


def apply_overrides(flat):
    """Read overrides.csv (create a blank template if missing) and apply any
    non-empty cell over the auto-generated value. The user edits this file."""
    if not os.path.exists(OVERRIDES):
        with open(OVERRIDES, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["match_no", "team_a", "team_b"] + OVERRIDE_FIELDS)
            w.writeheader()
            for r in flat:
                w.writerow({"match_no": r["match_no"], "team_a": r["team_a"],
                            "team_b": r["team_b"]})
        print(f"  created editable {os.path.basename(OVERRIDES)} (all blank — edit to taste)")
        return
    by_no = {r["match_no"]: r for r in flat}
    n = 0
    for ov in csv.DictReader(open(OVERRIDES)):
        row = by_no.get(ov.get("match_no"))
        if not row:
            continue
        for k in OVERRIDE_FIELDS:
            v = (ov.get(k) or "").strip()
            if v:
                row[k] = v
                n += 1
    if n:
        print(f"  applied {n} override(s) from {os.path.basename(OVERRIDES)}")


def main():
    fixtures = [f for f in csv.DictReader(open(FIXTURES)) if f["team_a"] != "TBD"]
    stacked, flat = [], []
    for fx in fixtures:
        a, b = fx["team_a"], fx["team_b"]
        ca, cb = code_for(a), code_for(b)
        sa, sb = card_stats(ca) if ca else None, card_stats(cb) if cb else None
        ha, hb = (h2h_tally(ca, cb) if ca and cb
                  else ({k: 0 for k in H2H_ROWS}, {k: 0 for k in H2H_ROWS}))

        # stacked card block: all-time rows, then a H2H sub-block
        stacked.append({"left": a, "label": f"=== MATCH {fx['match_no']} ===", "right": b})
        for k in ROWS:
            stacked.append({"left": sa[k] if sa else 0, "label": k,
                            "right": sb[k] if sb else 0})
        stacked.append({"left": "", "label": "-- H2H --", "right": ""})
        for k in H2H_ROWS:
            stacked.append({"left": ha[k], "label": f"H2H {k}", "right": hb[k]})
        stacked.append({"left": "", "label": "", "right": ""})  # spacer
        # flat row
        ta = top_scorers(ca) if ca else ["", ""]
        tb = top_scorers(cb) if cb else ["", ""]
        ra = recent_scorers(ca) if ca else ["", ""]
        rb = recent_scorers(cb) if cb else ["", ""]
        # HIGHLIGHTED 2026 star (S4): ONLY use a curated current star (STAR_BY_TEAM) or
        # whatever the user fills in overrides.csv. We do NOT auto-use a historical
        # top scorer — that player may be retired / not in the 2026 squad (e.g. Mexico's
        # most-recent-WC scorer is Chicharito, who won't be at WC2026). Blank by default
        # → the hook stays TEAM-focused until real squads are known (fill overrides.csv
        # the day before each match). Star2 keeps the historical scorer for the photo grid.
        star_a = STAR_BY_TEAM.get(a, "")
        star_b = STAR_BY_TEAM.get(b, "")
        fr = {"match_no": fx["match_no"], "slug": fx["slug"],
              "team_a": a, "team_b": b,
              "Top1_a": ta[0], "Top2_a": ta[1], "Top1_b": tb[0], "Top2_b": tb[1],
              "Star1_a": star_a, "Star2_a": ra[0], "Star1_b": star_b, "Star2_b": rb[0],
              "Comment_a": make_comment(sa, ha, b),
              "Comment_b": make_comment(sb, hb, a),
              "Headline_a": make_headline(sa),
              "Headline_b": make_headline(sb),
              "Hook_a": player_hook(star_a) or team_hook(a),
              "Hook_b": player_hook(star_b) or team_hook(b)}
        for k in ROWS:
            fr[f"{k}_a"] = sa[k] if sa else 0
            fr[f"{k}_b"] = sb[k] if sb else 0
        for k in H2H_ROWS:
            fr[f"H2H_{k}_a"] = ha[k]
            fr[f"H2H_{k}_b"] = hb[k]
        flat.append(fr)

    # --- apply user EDITABLE overrides (your edits win, never overwritten) ---
    apply_overrides(flat)

    with open(os.path.join(HERE, "data", "h2h_cards.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["left", "label", "right"])
        w.writeheader(); w.writerows(stacked)
    flat_cols = (["match_no", "slug", "team_a", "team_b",
                  "Top1_a", "Top2_a", "Top1_b", "Top2_b",
                  "Star1_a", "Star2_a", "Star1_b", "Star2_b",
                  "Comment_a", "Comment_b", "Headline_a", "Headline_b",
                  "Hook_a", "Hook_b"]
                 + [f"{k}_a" for k in ROWS] + [f"{k}_b" for k in ROWS]
                 + [f"H2H_{k}_a" for k in H2H_ROWS] + [f"H2H_{k}_b" for k in H2H_ROWS])
    with open(os.path.join(HERE, "data", "h2h_flat.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=flat_cols)
        w.writeheader(); w.writerows(flat)
    print(f"Wrote {len(flat)} fixtures.")
    print("  data/h2h_cards.csv  (stacked Sheet-3 card layout)")
    print("  data/h2h_flat.csv   (one row per fixture)")
    # show a card WITH real meetings (Scotland vs Brazil, 4 meetings)
    print("\nScotland vs Brazil card (m052 — 4 meetings):")
    start = next(i for i, r in enumerate(stacked) if r["label"] == "=== MATCH 52 ===")
    for r in stacked[start:start + 19]:
        print(f"   {str(r['left']):>8}  {r['label']:<8}  {r['right']}")


if __name__ == "__main__":
    main()
