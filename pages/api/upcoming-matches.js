import path from 'path';
import fs from 'fs';

export default function handler(req, res) {
  const raw = JSON.parse(fs.readFileSync(path.join(process.cwd(), 'public', 'wc26', 'matches.json'), 'utf8'));
  const matches = Array.isArray(raw) ? raw : (raw.matches || []);

  const now = new Date();

  // Next 20 unplayed matches (no post video yet), sorted by date
  const upcoming = matches
    .filter(m => {
      if (m.hasPostVideo) return false;
      const ko = new Date(m.date + 'T12:00:00Z');
      return ko >= now;
    })
    .sort((a, b) => new Date(a.date) - new Date(b.date))
    .slice(0, 20);

  res.status(200).json(upcoming);
}
