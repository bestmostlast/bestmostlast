#!/usr/bin/env node
/* Contact sheets: per match, render the 6 screens (S0-S5) as stills and montage
 * them SIDE BY SIDE into one wide PNG. NO video. Output:
 *   scripts/wc26/shorts/<slug>/export/contact.png
 *
 * Run:  node scripts/wc26/shorts/contact_sheets.js   (all 72)
 *       node scripts/wc26/shorts/contact_sheets.js m001-...   (one slug)
 */
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const HERE = __dirname;
const CSV = path.join(HERE, '..', 'data', 'h2h_short.csv');
const ONLY = process.argv[2];                // optional slug filter
// the 6 screens and the t-value that shows each clearly (final state)
const SHOTS = [['S0', 0.06], ['S1', 0.30], ['S2', 0.48], ['S3', 0.62], ['S4', 0.78], ['S5', 0.95]];

function parseCSV(t){
  const L = t.trim().split('\n').map(l => l.split(',').map(v => v.trim().replace(/^"|"$/g,'')));
  const head = L[0]; return L.slice(1).map(r => Object.fromEntries(head.map((h,i)=>[h,r[i]])));
}

(async () => {
  const puppeteer = require('puppeteer');
  let rows = parseCSV(fs.readFileSync(CSV, 'utf8'));
  if (ONLY) rows = rows.filter(r => r.slug === ONLY || r.match_no === ONLY);

  const browser = await puppeteer.launch({ args: ['--allow-file-access-from-files', '--disable-web-security'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1100, height: 2000 });
  await page.goto('file://' + path.join(HERE, 'card.html'));
  await page.waitForFunction('typeof draw === "function"');
  await page.waitForFunction('assets.headerBg !== null', { timeout: 8000 }).catch(()=>{});

  let n = 0;
  for (const row of rows) {
    await page.evaluate(async (r) => {
      current = r;
      assets.players = {}; assets.highlight = {}; assets.fans = {};
      const tryImg = (p) => new Promise(res => { const i = new Image(); i.onload=()=>res(i); i.onerror=()=>res(null); i.src=p; });
      const clean = v => (v||'').replace(/\s*\(\d+\)\s*$/,'').trim();
      assets.bg    = await tryImg(`_shared/stadiums/${r.city}.jpg`) || await tryImg(`_shared/stadiums/${r.slug}.jpg`);
      assets.flagA = await tryImg(`_shared/flags/${r.team_a}.png`);
      assets.flagB = await tryImg(`_shared/flags/${r.team_b}.png`);
      const names=[r.Top1_a,r.Top2_a,r.Top1_b,r.Top2_b,r.Best1_a,r.Best2_a,r.Best1_b,r.Best2_b,r.Star1_a,r.Star1_b].map(clean).filter(Boolean);
      for(const nm of names){ const im=await tryImg(`_shared/players/${nm}.jpg`); if(im) assets.players[nm]=im; }
      for(const [side,star] of [['a',clean(r.Star1_a)],['b',clean(r.Star1_b)]]){
        if(star) assets.highlight[side]=await tryImg(`_shared/highlight/${star}.jpg`)||await tryImg(`_shared/players/${star}.jpg`); }
      for(const tm of [r.team_a,r.team_b]){ const im=await tryImg(`_shared/fans/${tm}.jpg`); if(im) assets.fans[tm]=im; }
      document.getElementById('stadium').value = r.stadium || '';
      document.getElementById('datetime').value = r.datetime || '';
    }, row);

    const outDir = path.join(HERE, row.slug, 'export');
    fs.mkdirSync(outDir, { recursive: true });
    const tmp = [];
    for (const [tag, t] of SHOTS) {
      const url = await page.evaluate((tt) => { draw(tt); return document.getElementById('c').toDataURL('image/png'); }, t);
      const f = path.join(outDir, `_${tag}.png`);
      fs.writeFileSync(f, Buffer.from(url.split(',')[1], 'base64'));
      tmp.push(f);
    }
    // montage 6 stills side by side, labelled, into contact.png
    const out = path.join(outDir, 'contact.png');
    // montage the 6 stills side by side. Tolerate ImageMagick's non-zero exit on
    // harmless font warnings — we only care that the output file got written.
    try {
      execFileSync('montage', [...tmp, '-tile', '6x1', '-geometry', '+6+6',
        '-background', '#111', '-border', '2', '-bordercolor', '#333', out], { stdio: 'ignore' });
    } catch (e) { /* check below */ }
    if (!fs.existsSync(out)) { console.error(`! montage failed for m${row.match_no}`); continue; }
    tmp.forEach(f => fs.rmSync(f, { force: true }));
    console.log(`✓ m${row.match_no}  ${row.team_a} vs ${row.team_b}  → contact.png`);
    n++;
  }
  await browser.close();
  console.log(`\nDone. ${n} contact sheets.`);
})();
