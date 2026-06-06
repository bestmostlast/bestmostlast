#!/usr/bin/env python3
"""Fetch player photos from Wikipedia for the top-scorer / star-player callouts.

Reads the player names referenced in data/h2h_short.csv (TopScorer_*, StarPlayer_*),
pulls each one's lead image via the Wikipedia REST/pageimages API, and saves it to
shorts/_shared/players/<Player Name>.jpg.

Best-effort: players without a usable photo are skipped (the card falls back to a
silhouette placeholder). Free, no key. Run after build_render_input.py.

Usage: python3 scripts/wc26/fetch_player_photos.py
"""
import csv
import json
import os
import re
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(__file__)
SHORT = os.path.join(HERE, "data", "h2h_short.csv")
OUT = os.path.join(HERE, "shorts", "_shared", "players")
UA = {"User-Agent": "BestMostLast/1.0 (wc26 cards; contact bestmostlast@gmail.com)"}
API = "https://en.wikipedia.org/w/api.php"


def strip_goals(s):
    """'Javier Hernández (4)' -> 'Javier Hernández'."""
    return re.sub(r"\s*\(\d+\)\s*$", "", (s or "").strip())


def player_names():
    names = set()
    for r in csv.DictReader(open(SHORT)):
        for k in ("Top1_a", "Top2_a", "Top1_b", "Top2_b",
                  "Star1_a", "Star2_a", "Star1_b", "Star2_b"):
            n = strip_goals(r.get(k, ""))
            if n:
                names.add(n)
    return sorted(names)


def _pageimage(title):
    q = urllib.parse.urlencode({
        "action": "query", "format": "json", "prop": "pageimages",
        "piprop": "original", "titles": title, "redirects": 1, "pilicense": "any",
    })
    try:
        req = urllib.request.Request(f"{API}?{q}", headers=UA)
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.load(resp)
    except Exception:
        return None
    for _, pg in data.get("query", {}).get("pages", {}).items():
        src = pg.get("original", {}).get("source")
        if src:
            return src
    return None


def _search_title(query):
    """Find the best Wikipedia page title for an ambiguous name (footballer-biased)."""
    q = urllib.parse.urlencode({
        "action": "query", "format": "json", "list": "search",
        "srsearch": query, "srlimit": 1,
    })
    try:
        req = urllib.request.Request(f"{API}?{q}", headers=UA)
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.load(resp)
    except Exception:
        return None
    hits = data.get("query", {}).get("search", [])
    return hits[0]["title"] if hits else None


def fetch_image_url(name):
    """Try the name directly; if no image, disambiguate via search ('<name> footballer')."""
    url = _pageimage(name)
    if url:
        return url
    title = _search_title(f"{name} footballer")
    if title:
        return _pageimage(title)
    return None


def download(url, path):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        with open(path, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"  ! download failed: {e}")
        return False


def main():
    os.makedirs(OUT, exist_ok=True)
    names = player_names()
    print(f"{len(names)} unique players to fetch.")
    ok = miss = 0
    for n in names:
        dest = os.path.join(OUT, f"{n}.jpg")
        if os.path.exists(dest):
            ok += 1
            continue
        url = fetch_image_url(n)
        if url and download(url, dest):
            print(f"  ✓ {n}")
            ok += 1
        else:
            print(f"  – no photo: {n}")
            miss += 1
        time.sleep(0.4)  # be polite to the API
    print(f"\nDone. {ok} have photos, {miss} missing (will use silhouette).")


if __name__ == "__main__":
    main()
