#!/usr/bin/env node
/**
 * WC26 web-asset build step.
 *
 * Reads the source-of-truth CSVs in scripts/wc26/ and the generated shorts in
 * scripts/wc26/shorts/<slug>/export/, then emits web-optimized assets +
 * manifests into public/wc26/ for the Next.js /wc26 pages to consume.
 *
 *   - public/wc26/thumbs/<slug>.jpg   (compressed short.png still, all 72)
 *   - public/wc26/video/<slug>.mp4    (copied where a render exists, ~32)
 *   - public/wc26/flags/<Country>.png (the 48 nation flags)
 *   - public/wc26/matches.json        (per-match card data + asset flags)
 *   - public/wc26/teams.json          (per-country: matches + aggregate record)
 *
 * Originals stay in scripts/ — the repo only commits the optimized derivatives.
 *
 * This is a LOCAL authoring step, not a deploy step: it reads source assets
 * that are gitignored (_shared/flags, the export/short.png stills) and source CSVs, so
 * it cannot run on Vercel. Run it locally after re-rendering shorts or editing
 * the CSVs, then COMMIT the regenerated public/wc26/ — that committed output is
 * what deploys.
 *
 * Run:  npm run wc26:assets   (or: node scripts/wc26/build-web-assets.js)
 */
const fs = require("fs");
const path = require("path");
const sharp = require("sharp");

const ROOT = path.resolve(__dirname, "..", "..");
const WC = path.join(ROOT, "scripts", "wc26");
const SHORTS = path.join(WC, "shorts");
const SHARED = path.join(SHORTS, "_shared");
const OUT = path.join(ROOT, "public", "wc26");

/* ---------- tiny CSV parser (handles quoted fields w/ commas) ---------- */
function parseCSV(text) {
  const rows = [];
  let row = [];
  let field = "";
  let inQ = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQ) {
      if (c === '"') {
        if (text[i + 1] === '"') { field += '"'; i++; }
        else inQ = false;
      } else field += c;
    } else if (c === '"') inQ = true;
    else if (c === ",") { row.push(field); field = ""; }
    else if (c === "\n") { row.push(field); rows.push(row); row = []; field = ""; }
    else if (c === "\r") { /* skip */ }
    else field += c;
  }
  if (field.length || row.length) { row.push(field); rows.push(row); }
  const headers = rows.shift().map((h) => h.trim());
  return rows
    .filter((r) => r.some((v) => v !== ""))
    .map((r) => Object.fromEntries(headers.map((h, i) => [h, (r[i] ?? "").trim()])));
}

function readCSV(p) {
  return parseCSV(fs.readFileSync(p, "utf8"));
}

function ensure(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

/* split a "A | B" master-card cell into [a, b] */
function pair(v) {
  if (!v) return ["", ""];
  const [a, b] = v.split("|").map((s) => s.trim());
  return [a ?? "", b ?? ""];
}

/* fixture-name → team-file-name aliases (where the two datasets disagree) */
const NAME_ALIASES = {
  usa: "unitedstates",
  southkorea: "southkorea",
  ivorycoast: "ivorycoast",
};

/* normalized country key — "&"/"and"/punct/case-insensitive + alias matching */
function nkey(name) {
  const k = (name || "")
    .toLowerCase()
    .replace(/&/g, "and")
    .replace(/[^a-z0-9]+/g, "");
  return NAME_ALIASES[k] || k;
}

/* deepest WC stage → human label + rank (higher = further) */
const STAGE_RANK = { group: 0, group2: 0, r16: 1, qf: 2, third: 3, sf: 3, final: 4 };
const STAGE_LABEL = {
  group: "Group stage",
  group2: "2nd group stage",
  r16: "Round of 16",
  qf: "Quarter-final",
  third: "Third place",
  sf: "Semi-final",
  final: "Final",
};

/**
 * Aggregate one country's all-time WC record from its per-team match log.
 * Returns null if no history file exists for that country.
 */
function teamHistory(teamsDir, name) {
  if (!fs.existsSync(teamsDir)) return null;
  // map every code -> normalized country name once (cached on fn)
  if (!teamHistory._byKey) {
    teamHistory._byKey = {};
    for (const f of fs.readdirSync(teamsDir)) {
      const mm = f.match(/^([A-Z]{3})\.matches\.csv$/);
      if (!mm) continue;
      const rows = readCSV(path.join(teamsDir, f));
      if (!rows.length) continue;
      teamHistory._byKey[nkey(rows[0].team)] = { code: mm[1], rows };
    }
  }
  const entry = teamHistory._byKey[nkey(name)];
  if (!entry) return null;
  const rows = entry.rows;

  let w = 0, d = 0, l = 0, gf = 0, ga = 0, deepest = -1, titles = 0;
  const years = new Set();
  for (const r of rows) {
    years.add(r.year);
    if (r.result === "W") w++;
    else if (r.result === "D") d++;
    else if (r.result === "L") l++;
    gf += Number(r.gf) || 0;
    ga += Number(r.ga) || 0;
    const rank = STAGE_RANK[r.stage];
    if (rank != null && rank > deepest) deepest = rank;
    if (r.stage === "final" && r.result === "W") titles++;
  }
  const played = rows.length;
  const points = w * 3 + d;
  const bestLabel =
    deepest === 4 && titles > 0
      ? "Champions"
      : Object.entries(STAGE_RANK).find(([, v]) => v === deepest)?.[0];

  return {
    code: entry.code,
    appearances: years.size,
    titles,
    best: titles > 0 ? "Champions" : STAGE_LABEL[bestLabel] || "—",
    played,
    w, d, l, gf, ga,
    ppg: played ? +(points / played).toFixed(2) : 0,
  };
}

/** Top scorers for a country from its per-team players file. */
function teamScorers(teamsDir, code, limit = 5) {
  const p = path.join(teamsDir, `${code}.players.csv`);
  if (!fs.existsSync(p)) return [];
  return readCSV(p)
    .map((r) => ({ player: r.player, goals: Number(r.wc_goals) || 0, years: r.years }))
    .filter((r) => r.player && r.goals > 0)
    .sort((a, b) => b.goals - a.goals)
    .slice(0, limit);
}

async function main() {
  ensure(OUT);
  ensure(path.join(OUT, "thumbs"));
  ensure(path.join(OUT, "flags"));

  const fixtures = readCSV(path.join(WC, "fixtures.csv"));
  const cards = readCSV(path.join(WC, "data", "master_cards.csv"));
  const cardBySlug = Object.fromEntries(cards.map((c) => [c.slug, c]));

  // Published-video map (external hosting — YouTube id or full url, by slug).
  // Videos live off-repo; fill in scripts/wc26/videos.csv as Shorts go live.
  const videosPath = path.join(WC, "videos.csv");
  const videoBySlug = {};
  if (fs.existsSync(videosPath)) {
    for (const v of readCSV(videosPath)) {
      const id = (v.youtube_id || "").trim();
      const url = (v.url || "").trim();
      if (id || url) {
        videoBySlug[v.slug] = {
          youtubeId: id || null,
          url: url || (id ? `https://youtube.com/shorts/${id}` : null),
        };
      }
    }
  }

  const matches = [];
  let thumbN = 0, videoN = 0;

  for (const fx of fixtures) {
    const slug = fx.slug;
    const exportDir = path.join(SHORTS, slug, "export");
    const srcPng = path.join(exportDir, "short.png");

    let hasThumb = false;
    if (fs.existsSync(srcPng)) {
      await sharp(srcPng)
        .resize({ width: 720, withoutEnlargement: true }) // 9:16 still → ~720x1280
        .jpeg({ quality: 78, mozjpeg: true })
        .toFile(path.join(OUT, "thumbs", `${slug}.jpg`));
      hasThumb = true;
      thumbN++;
    }

    // Video is external (YouTube/CDN) — never bundled into the repo.
    const vid = videoBySlug[slug] || null;
    const hasVideo = !!vid;
    if (hasVideo) videoN++;

    const c = cardBySlug[slug] || {};
    const [wcA, wcB] = pair(c["S1_WorldCups"]);
    const [playedA, playedB] = pair(c["S1_Played"]);
    const [ppgA, ppgB] = pair(c["S1_Points(PPG)"]);
    const [h2hW, h2hWb] = pair(c["S2_H2H_W"]); // W is "A | B" wins from A's view

    matches.push({
      no: Number(fx.match_no),
      slug,
      phase: fx.phase,
      group: fx.group,
      matchday: Number(fx.matchday),
      date: fx.date,
      time: fx.time || "",
      venue: fx.venue,
      city: fx.city,
      teamA: fx.team_a,
      teamB: fx.team_b,
      status: fx.status,
      hasThumb,
      hasVideo,
      youtubeId: vid?.youtubeId || null,
      videoUrl: vid?.url || null,
      // headline card facts (for the match page, optional)
      worldCups: [wcA, wcB],
      played: [playedA, playedB],
      ppg: [ppgA, ppgB],
      h2h: { w: h2hW, d: pair(c["S2_H2H_D"])[0], l: pair(c["S2_H2H_L"])[0] },
      headline: [c["S4_Headline_A"] || "", c["S4_Headline_B"] || ""],
      hook: [c["S4_Hook_A"] || "", c["S4_Hook_B"] || ""],
      watch: [c["S3_Watch_A"] || "", c["S3_Watch_B"] || ""],
    });
  }

  matches.sort((a, b) => a.no - b.no);

  /* ---------- copy nation flags ---------- */
  const flagsSrc = path.join(SHARED, "flags");
  const flagFiles = fs.existsSync(flagsSrc) ? fs.readdirSync(flagsSrc) : [];
  for (const f of flagFiles) {
    if (/\.png$/i.test(f)) {
      fs.copyFileSync(path.join(flagsSrc, f), path.join(OUT, "flags", f));
    }
  }

  /* ---------- build per-team manifest ---------- */
  const teams = {};
  const PLACEHOLDER = /^(TBD|TBC|Winner|Runner|3rd|—|-)?$/i;
  for (const m of matches) {
    for (const [side, name] of [["A", m.teamA], ["B", m.teamB]]) {
      if (!name || PLACEHOLDER.test(name) || /TBD|winner|runner/i.test(name)) continue;
      if (!teams[name]) {
        teams[name] = {
          name,
          flag: flagFiles.includes(`${name}.png`) ? `${name}.png` : null,
          matches: [],
        };
      }
      teams[name].matches.push({
        slug: m.slug,
        no: m.no,
        group: m.group,
        matchday: m.matchday,
        opponent: side === "A" ? m.teamB : m.teamA,
        home: side === "A",
      });
    }
  }
  /* ---------- merge all-time WC history per country ---------- */
  const teamsDir = path.join(WC, "data", "teams");
  let withHistory = 0;
  for (const t of Object.values(teams)) {
    const h = teamHistory(teamsDir, t.name);
    if (h) {
      t.record = h;
      t.topScorers = teamScorers(teamsDir, h.code);
      withHistory++;
    } else {
      t.record = null;
      t.topScorers = [];
    }
  }

  const teamList = Object.values(teams).sort((a, b) => a.name.localeCompare(b.name));

  fs.writeFileSync(
    path.join(OUT, "matches.json"),
    JSON.stringify({ generated: new Date().toISOString(), count: matches.length, matches }, null, 2)
  );
  fs.writeFileSync(
    path.join(OUT, "teams.json"),
    JSON.stringify({ generated: new Date().toISOString(), count: teamList.length, teams: teamList }, null, 2)
  );

  console.log(`WC26 web assets built:`);
  console.log(`  matches: ${matches.length}  thumbs: ${thumbN}  videos(external): ${videoN}`);
  console.log(`  teams:   ${teamList.length}  flags: ${flagFiles.length}  withHistory: ${withHistory}`);
  console.log(`  → public/wc26/{matches.json, teams.json, thumbs/, flags/}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
