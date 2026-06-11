import path from 'path';
import fs from 'fs';

export default function handler(req, res) {
  const filePath = path.join(process.cwd(), 'public', 'wc26', 'matches.json');
  const raw = JSON.parse(fs.readFileSync(filePath, 'utf8'));
  const matches = Array.isArray(raw) ? raw : (raw.matches || []);

  const now = new Date();

  // Matches with any video, or that kicked off in the last 7 days
  const recent = matches
    .filter(m => {
      if (m.hasVideo || m.hasPostVideo) return true;
      const ko = new Date(m.date + 'T12:00:00Z');
      return ko <= now && (now - ko) < 7 * 24 * 60 * 60 * 1000;
    })
    .sort((a, b) => {
      // post-video first, then pre-video, then by date desc
      const aScore = (a.hasPostVideo ? 2 : 0) + (a.hasVideo ? 1 : 0);
      const bScore = (b.hasPostVideo ? 2 : 0) + (b.hasVideo ? 1 : 0);
      if (bScore !== aScore) return bScore - aScore;
      return new Date(b.date) - new Date(a.date);
    })
    .slice(0, 6);

  res.status(200).json(recent);
}
