#!/usr/bin/env python3
"""Compute the FORMAT-2 H2H comparison card for one fixture.

Reads data/teams/<A>.matches.csv and <B>.matches.csv, emits the split-card stat block
(attended / highest finish / avg finish / P-W-D-L / GF-GA / head-to-head meetings).
Works on match-level OR edition-summary rows.

Usage: python3 scripts/wc26/compute_h2h.py MEX RSA
"""
import csv
import os
import sys

HERE = os.path.dirname(__file__)
TEAMS = os.path.join(HERE, "data", "teams")

# finish ranking: lower number = better, for "highest" and "avg"
STAGE_RANK = {
    "final": 1, "third": 3, "sf": 4, "qf": 6, "r16": 12, "r32": 24,
    "group": 28, "EDITION-SUMMARY": None,  # summary rows carry finish in note
}
# map common note finishes → a representative rank for avg
FINISH_HINT = {
    "quarter-final": 6, "quarter": 6, "round of 16": 12,
    "group stage": 28, "group": 28, "semi": 4, "final": 1, "third": 3,
}


def load(code):
    p = os.path.join(TEAMS, f"{code}.matches.csv")
    if not os.path.exists(p):
        sys.exit(f"no data file: {p}")
    return list(csv.DictReader(open(p)))


def finish_rank_for_year(rows_for_year):
    """Best (lowest) stage rank reached in a tournament."""
    best = None
    for r in rows_for_year:
        st = r["stage"]
        rk = STAGE_RANK.get(st)
        # Distinguish champion (won the final) from runner-up (lost it).
        if st == "final":
            rk = 0 if r.get("result") == "W" else 2  # 0=WINNERS, 2=Runners-up
        elif rk is None:  # summary row: read finish from note
            note = (r.get("note") or "").lower()
            for k, v in FINISH_HINT.items():
                if k in note:
                    rk = v; break
        if rk is not None and (best is None or rk < best):
            best = rk
    return best


def summarize(code):
    rows = load(code)
    name = rows[0]["team"]
    years = sorted({r["year"] for r in rows})
    # P-W-D-L and goals: match-level uses result; summary rows have blank result but real gf/ga
    P = W = D = L = gf = ga = 0
    has_results = False
    for r in rows:
        if r["gf"] != "": gf += int(r["gf"])
        if r["ga"] != "": ga += int(r["ga"])
        res = r["result"]
        if res in ("W", "D", "L"):
            has_results = True; P += 1
            W += res == "W"; D += res == "D"; L += res == "L"
    # finishes per year for highest + avg rank
    by_year = {}
    for r in rows:
        by_year.setdefault(r["year"], []).append(r)
    ranks = [finish_rank_for_year(rs) for rs in by_year.values()]
    ranks = [x for x in ranks if x is not None]
    highest = min(ranks) if ranks else None
    avg = round(sum(ranks) / len(ranks), 1) if ranks else None
    return {
        "code": code, "name": name, "attended": len(years),
        "P": P if has_results else f"~{sum(1 for _ in rows)}*",  # summary: matches unknown
        "W": W, "D": D, "L": L, "gf": gf, "ga": ga,
        "highest_rank": highest, "avg_rank": avg, "_summary_only": not has_results,
    }


def meetings(a, b):
    """Recover past WC meetings from whichever side has match-level opponent rows."""
    out = []
    for code, other in ((a, b), (b, a)):
        for r in load(code):
            if r.get("opponent_code") == other:
                out.append((r["year"], r["stage"], r["team"], r["opponent"],
                            r["gf"], r["ga"], r["result"], r.get("note", "")))
    # dedupe by (year, stage)
    seen, uniq = set(), []
    for m in out:
        k = (m[0], m[1])
        if k not in seen:
            seen.add(k); uniq.append(m)
    return uniq


def rank_label(r):
    return {0: "WINNERS", 2: "Runners-up", 3: "3rd", 4: "Semi-final",
            6: "Quarter-final", 12: "Round of 16", 24: "Round of 32",
            28: "Group stage"}.get(r, f"~{r}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: compute_h2h.py <CODE_A> <CODE_B>")
    A, B = sys.argv[1].upper(), sys.argv[2].upper()
    sa, sb = summarize(A), summarize(B)
    print(f"\n  H2H CARD — {sa['name']} (top) vs {sb['name']} (bottom)\n")
    rows = [
        ("World Cups attended", sa["attended"], sb["attended"]),
        ("Highest finish",      rank_label(sa["highest_rank"]), rank_label(sb["highest_rank"])),
        ("Avg finish (rank)",   sa["avg_rank"], sb["avg_rank"]),
        ("Matches P-W-D-L",     f"{sa['P']}  {sa['W']}-{sa['D']}-{sa['L']}",
                                f"{sb['P']}  {sb['W']}-{sb['D']}-{sb['L']}"),
        ("Goals F-A",           f"{sa['gf']}-{sa['ga']}", f"{sb['gf']}-{sb['ga']}"),
    ]
    for label, va, vb in rows:
        print(f"  {label:22} {str(va):>14}  |  {vb}")
    ms = meetings(A, B)
    print(f"\n  Head-to-head meetings: {len(ms)}")
    for y, st, t, opp, gf, ga, res, note in ms:
        print(f"    {y} {st}: {t} {gf}-{ga} {opp}  ({note})")
    if sa["_summary_only"] or sb["_summary_only"]:
        print("\n  * = edition-summary team: match count approximate, W-D-L not per-match.")
    print()
