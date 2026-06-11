#!/usr/bin/env node
/* Batch-render all WC26 H2H Shorts to PNG (1080x1920).
 * Reuses card.html's exact draw code by loading it in a headless browser.
 *
 * Setup (one-time):   npm i puppeteer
 * Run:                node scripts/wc26/shorts/render_all.js
 * Output:             scripts/wc26/shorts/<slug>/export/short.png
 *
 * Per-game assets (optional, picked up if present):
 *   _shared/stadiums/<city>.jpg   (or <slug>.jpg)   stadium background
 *   _shared/flags/<CODE>.png                          team flag
 * Missing assets fall back to gradient bg / placeholder flag.
 */
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const MAKE_MP4 = process.argv.includes('--mp4');   // node render_all.js --mp4
const FPS = 30, SECS = 39;                          // 5-screen sequence, 31s total
const NO_MUSIC = process.argv.includes('--no-music');

const HERE       = __dirname;
const CSV        = path.join(HERE, '..', 'data', 'h2h_short.csv');
const MUSIC_DIR  = path.join(HERE, '_shared', 'music');

function pickMusic() {
  try {
    const tracks = fs.readdirSync(MUSIC_DIR).filter(f => /\.(mp3|wav|m4a)$/i.test(f));
    if (!tracks.length) return null;
    return path.join(MUSIC_DIR, tracks[Math.floor(Math.random() * tracks.length)]);
  } catch { return null; }
}

function parseCSV(t){
  const L = t.trim().split('\n').map(l => l.split(',').map(v => v.trim().replace(/^"|"$/g,'')));
  const head = L[0]; return L.slice(1).map(r => Object.fromEntries(head.map((h,i)=>[h,r[i]])));
}

(async () => {
  let puppeteer;
  try { puppeteer = require('puppeteer'); }
  catch { console.error('Missing puppeteer. Run:  npm i puppeteer'); process.exit(1); }

  const rows = parseCSV(fs.readFileSync(CSV, 'utf8'));
  const SKIP_DONE = process.argv.includes('--resume');
  // allow local file images to be read back via toDataURL (no canvas taint)
  let browser, page, sinceRestart = 0;
  async function fresh() {
    if (browser) await browser.close().catch(()=>{});
    browser = await puppeteer.launch({
      args: ['--allow-file-access-from-files', '--disable-web-security']
    });
    page = await browser.newPage();
    await page.setViewport({ width: 1100, height: 2000 });
    await page.goto('file://' + path.join(HERE, 'card.html'));
    await page.waitForFunction('typeof draw === "function"');
    sinceRestart = 0;
  }
  await fresh();

  for (const row of rows) {
    const finalOut = path.join(HERE, row.slug, 'export', MAKE_MP4 ? 'short.mp4' : 'short.png');
    if (SKIP_DONE && fs.existsSync(finalOut)) { console.log(`· m${row.match_no} skip (done)`); continue; }
    if (sinceRestart >= 6) await fresh();   // relaunch periodically → avoid CDP ProtocolError
    sinceRestart++;
    // hand the row + asset paths to the page, then screenshot the canvas
    await page.evaluate(async (r, here) => {
      current = r;
      assets.players = {}; assets.highlight = {};
      const tryImg = (p) => new Promise(res => { const i = new Image(); i.onload=()=>res(i); i.onerror=()=>res(null); i.src=p; });
      const clean = v => (v||'').replace(/\s*\(\d+\)\s*$/,'').trim();
      assets.bg    = await tryImg(`_shared/stadiums/${r.city}.jpg`) || await tryImg(`_shared/stadiums/${r.slug}.jpg`);
      assets.flagA = await tryImg(`_shared/flags/${r.team_a}.png`);
      assets.flagB = await tryImg(`_shared/flags/${r.team_b}.png`);
      // player photos for the scorers screen
      const names=[r.Top1_a,r.Top2_a,r.Top1_b,r.Top2_b,r.Star1_a,r.Star2_a,r.Star1_b,r.Star2_b].map(clean).filter(Boolean);
      for(const n of names){ const im=await tryImg(`_shared/players/${n}.jpg`); if(im) assets.players[n]=im; }
      // S4 highlight: prefer a supplied national-jersey photo, else the portrait.
      for(const [side,star] of [['a',clean(r.Star1_a)],['b',clean(r.Star1_b)]]){
        if(!star) continue;
        assets.highlight[side] = await tryImg(`_shared/highlight/${star}.jpg`) || await tryImg(`_shared/players/${star}.jpg`);
      }
      // H2H fan photos (optional) — cartoon fallback if absent.
      assets.fans = {};
      for(const tm of [r.team_a, r.team_b]){ const im=await tryImg(`_shared/fans/${tm}.jpg`); if(im) assets.fans[tm]=im; }
      document.getElementById('stadium').value = r.stadium || '';
      document.getElementById('datetime').value = r.datetime || '';
      draw();
    }, row, HERE);

    const outDir = path.join(HERE, row.slug, 'export');
    fs.mkdirSync(outDir, { recursive: true });

    const grab = async (t) => {
      const url = await page.evaluate((tt) => { draw(tt); return document.getElementById('c').toDataURL('image/png'); }, t);
      return Buffer.from(url.split(',')[1], 'base64');
    };

    // always write the final still
    fs.writeFileSync(path.join(outDir, 'short.png'), await grab(1));

    if (MAKE_MP4) {
      const framesDir = path.join(outDir, 'frames');
      fs.mkdirSync(framesDir, { recursive: true });
      const total = FPS * SECS;
      for (let f = 0; f < total; f++)
        fs.writeFileSync(path.join(framesDir, `f${String(f).padStart(4,'0')}.png`), await grab(f / (total - 1)));
      const silent = path.join(outDir, '_silent.mp4');
      execFileSync('ffmpeg', ['-y', '-framerate', String(FPS), '-i', path.join(framesDir, 'f%04d.png'),
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', silent], { stdio: 'ignore' });
      const out       = path.join(outDir, 'short.mp4');
      const bgm       = !NO_MUSIC ? pickMusic() : null;
      const narration = path.join(outDir, 'narration.mp3');
      const hasNarr   = fs.existsSync(narration);
      const hasBgm    = bgm && fs.existsSync(bgm);

      if (hasBgm || hasNarr) {
        const inputs = ['-y', '-i', silent];
        if (hasBgm)  inputs.push('-i', bgm);
        if (hasNarr) inputs.push('-i', narration);

        let filterComplex, audioMap;
        if (hasBgm && hasNarr) {
          const bgmIdx = 1, narrIdx = 2;
          filterComplex = `[${bgmIdx}:a]volume=0.18,afade=t=out:st=${SECS-2}:d=2,atrim=0:${SECS}[bgm];` +
                          `[${narrIdx}:a]adelay=4000|4000[narr];` +
                          `[bgm][narr]amix=inputs=2:normalize=0[a]`;
          audioMap = '[a]';
        } else if (hasBgm) {
          filterComplex = `[1:a]afade=t=out:st=${SECS-2}:d=2,atrim=0:${SECS}[a]`;
          audioMap = '[a]';
        } else {
          filterComplex = `[1:a]adelay=4000|4000[a]`;
          audioMap = '[a]';
        }

        execFileSync('ffmpeg', [
          ...inputs,
          '-filter_complex', filterComplex,
          '-map', '0:v', '-map', audioMap,
          '-c:v', 'copy', '-c:a', 'aac', '-shortest', out,
        ], { stdio: 'ignore' });
        fs.rmSync(silent, { force: true });
        if (hasBgm)  console.log(`  ♫ music: ${path.basename(bgm)}`);
        if (hasNarr) console.log(`  🎙 narration mixed in`);
      } else {
        fs.renameSync(silent, out);
      }
      fs.rmSync(framesDir, { recursive: true, force: true });
    }
    console.log(`✓ m${row.match_no}  ${row.team_a} vs ${row.team_b}${MAKE_MP4 ? ' (mp4)' : ''}`);
  }
  await browser.close();
  console.log(`\nDone. ${rows.length} shorts → scripts/wc26/shorts/<slug>/export/short.png`);
})();
