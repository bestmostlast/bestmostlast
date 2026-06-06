#!/usr/bin/env python3
"""One-shot builder for fixtures.csv — full WC26 schedule (104 matches).

Group-stage teams are real (post-draw). Knockout teams are bracket placeholders
(e.g. '1A' = Group A winner, 'W73' = winner of match 73) until results resolve.
Sources: Sky Sports day-by-day list + Wikipedia knockout-stage table (June 2026).
"""
import csv
import re
import unicodedata

# Host country lookup by city (for the 'country' column).
COUNTRY = {
    "Mexico City": "Mexico", "Zapopan": "Mexico", "Monterrey": "Mexico", "Guadalupe": "Mexico",
    "Toronto": "Canada", "Vancouver": "Canada",
}
def country_of(city):
    return COUNTRY.get(city, "USA")

# Official WC26 stadium name per host city (public).
STADIUM = {
    "Mexico City": "Estadio Azteca", "Zapopan": "Estadio Akron",
    "Monterrey": "Estadio BBVA", "Guadalupe": "Estadio BBVA",
    "Toronto": "BMO Field", "Vancouver": "BC Place",
    "Los Angeles": "SoFi Stadium", "Santa Clara": "Levi's Stadium",
    "New Jersey": "MetLife Stadium", "Foxborough": "Gillette Stadium",
    "Philadelphia": "Lincoln Financial Field", "Miami": "Hard Rock Stadium",
    "Atlanta": "Mercedes-Benz Stadium", "Houston": "NRG Stadium",
    "Kansas City": "Arrowhead Stadium", "Dallas": "AT&T Stadium",
    "Arlington": "AT&T Stadium", "Seattle": "Lumen Field",
    "Boston": "Gillette Stadium", "San Francisco": "Levi's Stadium",
}
def stadium_of(city):
    return STADIUM.get(city, "")

def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s

# (match_no, date 2026, group, team_a, team_b, city)  -- group stage
GROUP = [
    (1,"06-11","A","Mexico","South Africa","Mexico City"),
    (2,"06-12","A","South Korea","Czech Republic","Zapopan"),
    (3,"06-12","B","Canada","Bosnia & Herzegovina","Toronto"),
    (4,"06-13","D","USA","Paraguay","Los Angeles"),
    (5,"06-13","B","Qatar","Switzerland","Santa Clara"),
    (6,"06-13","C","Brazil","Morocco","New Jersey"),
    (7,"06-14","C","Haiti","Scotland","Foxborough"),
    (8,"06-14","D","Australia","Turkey","Vancouver"),
    (9,"06-14","E","Germany","Curacao","Houston"),
    (10,"06-14","F","Netherlands","Japan","Arlington"),
    (11,"06-15","E","Ivory Coast","Ecuador","Philadelphia"),
    (12,"06-15","F","Sweden","Tunisia","Guadalupe"),
    (13,"06-15","H","Spain","Cape Verde","Atlanta"),
    (14,"06-15","G","Belgium","Egypt","Seattle"),
    (15,"06-15","H","Saudi Arabia","Uruguay","Miami"),
    (16,"06-16","G","Iran","New Zealand","Los Angeles"),
    (17,"06-16","I","France","Senegal","New Jersey"),
    (18,"06-16","I","Iraq","Norway","Foxborough"),
    (19,"06-17","J","Argentina","Algeria","Kansas City"),
    (20,"06-17","J","Austria","Jordan","Santa Clara"),
    (21,"06-17","K","Portugal","DR Congo","Houston"),
    (22,"06-17","L","England","Croatia","Arlington"),
    (23,"06-18","L","Ghana","Panama","Toronto"),
    (24,"06-18","K","Uzbekistan","Colombia","Mexico City"),
    (25,"06-18","A","Czech Republic","South Africa","Atlanta"),
    (26,"06-18","B","Switzerland","Bosnia & Herzegovina","Los Angeles"),
    (27,"06-18","B","Canada","Qatar","Vancouver"),
    (28,"06-19","A","Mexico","South Korea","Zapopan"),
    (29,"06-19","D","USA","Australia","Seattle"),
    (30,"06-19","C","Scotland","Morocco","Foxborough"),
    (31,"06-20","C","Brazil","Haiti","Philadelphia"),
    (32,"06-20","D","Turkey","Paraguay","Santa Clara"),
    (33,"06-20","F","Netherlands","Sweden","Houston"),
    (34,"06-20","E","Germany","Ivory Coast","Toronto"),
    (35,"06-21","E","Ecuador","Curacao","Kansas City"),
    (36,"06-21","F","Tunisia","Japan","Guadalupe"),
    (37,"06-21","H","Spain","Saudi Arabia","Atlanta"),
    (38,"06-21","G","Belgium","Iran","Los Angeles"),
    (39,"06-21","H","Uruguay","Cape Verde","Miami"),
    (40,"06-22","G","New Zealand","Egypt","Vancouver"),
    (41,"06-22","J","Argentina","Austria","Arlington"),
    (42,"06-22","I","France","Iraq","Philadelphia"),
    (43,"06-23","I","Norway","Senegal","Toronto"),
    (44,"06-23","J","Jordan","Algeria","Santa Clara"),
    (45,"06-23","K","Portugal","Uzbekistan","Houston"),
    (46,"06-23","L","England","Ghana","Foxborough"),
    (47,"06-24","L","Panama","Croatia","Foxborough"),
    (48,"06-24","K","Colombia","DR Congo","Zapopan"),
    (49,"06-24","B","Switzerland","Canada","Vancouver"),
    (50,"06-24","B","Bosnia & Herzegovina","Qatar","Seattle"),
    (51,"06-24","C","Morocco","Haiti","Atlanta"),
    (52,"06-24","C","Scotland","Brazil","Miami"),
    (53,"06-25","A","South Africa","South Korea","Guadalupe"),
    (54,"06-25","A","Czech Republic","Mexico","Mexico City"),
    (55,"06-25","E","Curacao","Ivory Coast","Philadelphia"),
    (56,"06-25","E","Ecuador","Germany","New Jersey"),
    (57,"06-26","F","Tunisia","Netherlands","Kansas City"),
    (58,"06-26","F","Japan","Sweden","Arlington"),
    (59,"06-26","D","Turkey","USA","Los Angeles"),
    (60,"06-26","D","Paraguay","Australia","Santa Clara"),
    (61,"06-26","I","Norway","France","Foxborough"),
    (62,"06-26","I","Senegal","Iraq","Toronto"),
    (63,"06-27","H","Cape Verde","Saudi Arabia","Houston"),
    (64,"06-27","H","Uruguay","Spain","Zapopan"),
    (65,"06-27","G","New Zealand","Belgium","Vancouver"),
    (66,"06-27","G","Egypt","Iran","Seattle"),
    (67,"06-27","L","Panama","England","New Jersey"),
    (68,"06-27","L","Croatia","Ghana","Philadelphia"),
    (69,"06-28","K","Colombia","Portugal","Miami"),
    (70,"06-28","K","DR Congo","Uzbekistan","Atlanta"),
    (71,"06-28","J","Algeria","Austria","Kansas City"),
    (72,"06-28","J","Jordan","Argentina","Arlington"),
]

# (match_no, phase, date, city) -- knockouts; teams are bracket placeholders.
KO = [
    (73,"r32","06-28","Los Angeles"),(74,"r32","06-29","Foxborough"),
    (75,"r32","06-29","Monterrey"),(76,"r32","06-29","Houston"),
    (77,"r32","06-30","New Jersey"),(78,"r32","06-30","Arlington"),
    (79,"r32","06-30","Mexico City"),(80,"r32","07-01","Atlanta"),
    (81,"r32","07-01","Santa Clara"),(82,"r32","07-01","Seattle"),
    (83,"r32","07-02","Toronto"),(84,"r32","07-02","Los Angeles"),
    (85,"r32","07-02","Vancouver"),(86,"r32","07-03","Miami"),
    (87,"r32","07-03","Kansas City"),(88,"r32","07-03","Arlington"),
    (89,"r16","07-04","Philadelphia"),(90,"r16","07-04","Houston"),
    (91,"r16","07-05","New Jersey"),(92,"r16","07-05","Mexico City"),
    (93,"r16","07-06","Arlington"),(94,"r16","07-06","Seattle"),
    (95,"r16","07-07","Atlanta"),(96,"r16","07-07","Vancouver"),
    (97,"qf","07-09","Foxborough"),(98,"qf","07-10","Los Angeles"),
    (99,"qf","07-11","Miami"),(100,"qf","07-11","Kansas City"),
    (101,"sf","07-14","Arlington"),(102,"sf","07-15","Atlanta"),
    (103,"third","07-18","Miami"),(104,"final","07-19","New Jersey"),
]

rows = []
for mno, md, grp, a, b, city in GROUP:
    matchday = 1 if mno <= 24 else (2 if mno <= 48 else 3)
    slug = f"m{mno:03d}-{slugify(a)}-vs-{slugify(b)}"
    rows.append({
        "match_no": mno, "slug": slug, "phase": "group", "group": grp,
        "matchday": matchday, "date": f"2026-{md}", "venue": stadium_of(city), "city": city,
        "country": country_of(city), "team_a": a, "team_b": b, "status": "drawn",
    })
for mno, phase, md, city in KO:
    slug = f"m{mno:03d}-{phase}"
    rows.append({
        "match_no": mno, "slug": slug, "phase": phase, "group": "",
        "matchday": "", "date": f"2026-{md}", "venue": stadium_of(city), "city": city,
        "country": country_of(city), "team_a": "TBD", "team_b": "TBD",
        "status": "bracket",
    })

cols = ["match_no","slug","phase","group","matchday","date","time","venue","city",
        "country","team_a","team_b","status"]
with open("scripts/wc26/fixtures.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)
print(f"Wrote {len(rows)} fixtures to scripts/wc26/fixtures.csv")
