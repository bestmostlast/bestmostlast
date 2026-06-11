#!/usr/bin/env node
/* Batch-render WC26 post-match result shorts to MP4 (1080×1920).
 *
 * Run (one match):  node scripts/wc26/shorts/render_result.js --mp4 m001-mexico-vs-south-africa
 * Run (all):        node scripts/wc26/shorts/render_result.js --mp4
 * PNG only:         node scripts/wc26/shorts/render_result.js m001-mexico-vs-south-africa
 */
const fs   = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const MAKE_MP4  = process.argv.includes('--mp4');
const NO_MUSIC  = process.argv.includes('--no-music');
const SKIP_DONE = process.argv.includes('--resume');
const ONLY      = process.argv.find(a => a.startsWith('m0') || /^\d+$/.test(a));

const FPS        = 30, SECS = 35;
const HERE       = __dirname;
const CSV        = path.join(HERE, '..', 'data', 'results.csv');
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
  const head = L[0];
  return L.slice(1).filter(r => r.length > 1 && r[0]).map(r => Object.fromEntries(head.map((h,i)=>[h,r[i]||''])));
}

(async () => {
  let puppeteer;
  try { puppeteer = require('puppeteer'); }
  catch { console.error('Missing puppeteer.  Run:  npm i puppeteer'); process.exit(1); }

  let rows = parseCSV(fs.readFileSync(CSV, 'utf8'));
  if (ONLY) rows = rows.filter(r => r.slug === ONLY || r.match_no === ONLY);
  if (!rows.length) { console.error('No matching rows in results.csv'); process.exit(1); }

  let browser, page, sinceRestart = 0;
  async function fresh(){
    if (browser) await browser.close().catch(()=>{});
    browser = await puppeteer.launch({ args:['--allow-file-access-from-files','--disable-web-security'] });
    page    = await browser.newPage();
    await page.setViewport({ width:1100, height:2000 });
    await page.goto('file://' + path.join(HERE, 'result_card.html'));
    await page.waitForFunction('typeof draw === "function"');
    await page.waitForFunction('assets.splashCombo !== null', { timeout:8000 }).catch(()=>{});
    sinceRestart = 0;
  }
  await fresh();

  for (const row of rows){
    const outDir  = path.join(HERE, row.slug, 'export');
    const ext     = MAKE_MP4 ? 'mp4' : 'png';
    const finalOut = path.join(outDir, `result.${ext}`);
    if (SKIP_DONE && fs.existsSync(finalOut)){ console.log(`· m${row.match_no} skip`); continue; }
    if (sinceRestart >= 6) await fresh();
    sinceRestart++;

    await page.evaluate(async (r) => {
      current = r;
      const enc = s => s.split('/').map(p=>encodeURIComponent(p)).join('/');
      const tryImg = p => new Promise(res=>{ const i=new Image(); i.onload=()=>res(i); i.onerror=()=>res(null); i.src=enc(p); });
      assets.bg   = await tryImg(`_shared/stadiums/${r.city}.jpg`) || await tryImg(`_shared/stadiums/${r.venue}.jpg`) || null;
      assets.flagA = await tryImg(`_shared/flags/${r.team_a}.png`);
      assets.flagB = await tryImg(`_shared/flags/${r.team_b}.png`);
      assets.potm  = r.potm_name ? (await tryImg(`_shared/players/${r.potm_name}.jpg`) || null) : null;
      draw(0);
    }, row);

    fs.mkdirSync(outDir, { recursive:true });

    const grab = async (t) => {
      const url = await page.evaluate(tt => { draw(tt); return document.getElementById('c').toDataURL('image/png'); }, t);
      return Buffer.from(url.split(',')[1], 'base64');
    };

    // always write still
    fs.writeFileSync(path.join(outDir, 'result.png'), await grab(1));

    if (MAKE_MP4){
      const framesDir = path.join(outDir, 'frames_result');
      fs.mkdirSync(framesDir, { recursive:true });
      const total = FPS * SECS;
      for (let f = 0; f < total; f++)
        fs.writeFileSync(path.join(framesDir, `f${String(f).padStart(4,'0')}.png`), await grab(f / (total-1)));

      const silent = path.join(outDir, '_result_silent.mp4');
      execFileSync('ffmpeg', ['-y','-framerate',String(FPS),'-i',path.join(framesDir,'f%04d.png'),
        '-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart', silent], { stdio:'ignore' });

      const bgm        = !NO_MUSIC ? pickMusic() : null;
      const narration  = path.join(outDir, 'narration.mp3');
      const hasNarr    = fs.existsSync(narration);
      const hasBgm     = bgm && fs.existsSync(bgm);

      if (hasBgm || hasNarr) {
        // Build ffmpeg inputs + filter_complex
        const inputs = ['-y', '-i', silent];
        if (hasBgm)  inputs.push('-i', bgm);
        if (hasNarr) inputs.push('-i', narration);

        let filterComplex, audioMap;
        if (hasBgm && hasNarr) {
          // music at -18dB under narration, fade out last 2s, narration at 0dB
          const bgmIdx  = 1, narrIdx = 2;
          filterComplex = `[${bgmIdx}:a]volume=0.18,afade=t=out:st=${SECS-2}:d=2,atrim=0:${SECS}[bgm];` +
                          `[${narrIdx}:a]adelay=1500|1500[narr];` +
                          `[bgm][narr]amix=inputs=2:normalize=0[a]`;
          audioMap = '[a]';
        } else if (hasBgm) {
          filterComplex = `[1:a]afade=t=out:st=${SECS-2}:d=2,atrim=0:${SECS}[a]`;
          audioMap = '[a]';
        } else {
          filterComplex = `[1:a]adelay=1500|1500[a]`;
          audioMap = '[a]';
        }

        execFileSync('ffmpeg', [
          ...inputs,
          '-filter_complex', filterComplex,
          '-map', '0:v', '-map', audioMap,
          '-c:v', 'copy', '-c:a', 'aac', '-shortest', finalOut,
        ], { stdio: 'ignore' });
        fs.rmSync(silent, { force: true });
        if (hasBgm) console.log(`  ♫ music: ${path.basename(bgm)}`);
        if (hasNarr) console.log(`  🎙 narration mixed in`);
      } else {
        fs.renameSync(silent, finalOut);
      }
      fs.rmSync(framesDir, { recursive:true, force:true });
    }
    console.log(`✓ m${row.match_no}  ${row.team_a} vs ${row.team_b}${MAKE_MP4?' (mp4)':''}`);
  }
  await browser.close();
  console.log(`\nDone. → <slug>/export/result.${MAKE_MP4?'mp4':'png'}`);
})();
