import path from 'path';
import fs from 'fs';

export default function handler(req, res) {
  const raw = JSON.parse(fs.readFileSync(path.join(process.cwd(), 'public', 'wc26', 'matches.json'), 'utf8'));
  const matches = Array.isArray(raw) ? raw : (raw.matches || []);

  // Only matches that have a published YouTube video (pre or post)
  const withVideo = matches
    .filter(m => m.hasVideo || m.hasPostVideo)
    .sort((a, b) => {
      const aScore = (a.hasPostVideo ? 2 : 0) + (a.hasVideo ? 1 : 0);
      const bScore = (b.hasPostVideo ? 2 : 0) + (b.hasVideo ? 1 : 0);
      if (bScore !== aScore) return bScore - aScore;
      return new Date(b.date) - new Date(a.date);
    })
    .slice(0, 9);

  res.status(200).json(withVideo);
}
