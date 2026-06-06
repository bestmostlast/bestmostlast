#!/usr/bin/env python3
"""Check which supplied team/player images are still MISSING.

Reads the players/teams referenced in data/h2h_short.csv and reports, per category,
which expected files don't exist yet in the _shared asset folders. Run any time as
you drop images in to see what's left.

Folders checked:
  _shared/fans/<Team>.jpg       (team jersey OR fan crowd)
  _shared/players/<Player>.jpg  (player photo)
  _shared/highlight/<Player>.jpg (optional S4 jersey override — not required)

Usage: python3 scripts/wc26/check_images.py [--list]
  --list : also print the full have/missing lists (default: just summary + missing)
"""
import csv
import os
import re
import sys

HERE = os.path.dirname(__file__)
SHORT = os.path.join(HERE, "data", "h2h_short.csv")
SHARED = os.path.join(HERE, "shorts", "_shared")
FANS = os.path.join(SHARED, "fans")
PLAYERS = os.path.join(SHARED, "players")
HIGHLIGHT = os.path.join(SHARED, "highlight")

IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")


def clean(v):
    return re.sub(r"\s*\(\d+\)\s*$", "", (v or "")).strip()


def existing(folder):
    """set of basenames (without extension) of image files present."""
    if not os.path.isdir(folder):
        return set()
    out = set()
    for f in os.listdir(folder):
        base, ext = os.path.splitext(f)
        if ext.lower() in IMG_EXT:
            out.add(base)
    return out


def main():
    show_all = "--list" in sys.argv
    rows = list(csv.DictReader(open(SHORT)))

    teams = sorted({r["team_a"] for r in rows} | {r["team_b"] for r in rows})

    slots = [("Top1_a", "team_a"), ("Top2_a", "team_a"),
             ("Star1_a", "team_a"), ("Star2_a", "team_a"),
             ("Top1_b", "team_b"), ("Top2_b", "team_b"),
             ("Star1_b", "team_b"), ("Star2_b", "team_b")]
    players = {}
    for r in rows:
        for slot, team in slots:
            n = clean(r[slot])
            if n:
                players.setdefault(n, set()).add(r[team])
    player_names = sorted(players)

    have_fans = existing(FANS)
    have_players = existing(PLAYERS)
    have_highlight = existing(HIGHLIGHT)

    def report(label, expected, have, folder):
        miss = [x for x in expected if x not in have]
        print(f"\n{label}: {len(expected)-len(miss)}/{len(expected)} present"
              f"  ({len(miss)} missing)  → {os.path.relpath(folder, HERE)}/")
        if miss:
            print("  MISSING:")
            for m in miss:
                print(f"    - {m}")
        if show_all and (len(expected) - len(miss)):
            print("  have:", ", ".join(x for x in expected if x in have))
        return miss

    print("=" * 60)
    print("WC2026 image check")
    print("=" * 60)
    m_fans = report("TEAM images (fans/)", teams, have_fans, FANS)
    m_players = report("PLAYER photos (players/)", player_names, have_players, PLAYERS)
    # highlight is optional — only report how many overrides exist
    n_hl = sum(1 for p in player_names if p in have_highlight)
    print(f"\nHIGHLIGHT overrides (optional): {n_hl} present "
          f"→ {os.path.relpath(HIGHLIGHT, HERE)}/")

    print("\n" + "-" * 60)
    total_need = len(teams) + len(player_names)
    total_have = (len(teams) - len(m_fans)) + (len(player_names) - len(m_players))
    print(f"TOTAL required: {total_have}/{total_need} supplied "
          f"({len(m_fans)+len(m_players)} still missing)")
    # tip: flag any stray files that don't match a needed name
    stray_fans = [f for f in have_fans if f not in teams]
    stray_players = [f for f in have_players if f not in player_names]
    if stray_fans:
        print(f"\n⚠ fans/ has {len(stray_fans)} file(s) not matching any team "
              f"(wrong name?): {', '.join(sorted(stray_fans)[:10])}"
              + (" …" if len(stray_fans) > 10 else ""))
    if stray_players:
        print(f"⚠ players/ has {len(stray_players)} file(s) not matching any needed "
              f"player (fetched extras or wrong name): "
              f"{', '.join(sorted(stray_players)[:8])}"
              + (" …" if len(stray_players) > 8 else ""))


if __name__ == "__main__":
    main()
