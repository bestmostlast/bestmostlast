import Head from "next/head";
import Link from "next/link";
import Image from "next/image";
import { useState, useEffect } from "react";

export default function Home() {
  const [latestStats, setLatestStats] = useState([]);

  useEffect(() => {
    fetch("/data/premier-league.csv")
      .then((r) => r.text())
      .then((text) => {
        const lines = text.trim().split("\n").slice(1);
        const rows = lines.map((l) => {
          const [player, team, goals, week, competition, date, avg7, avg30] = l.split(",");
          return { player, team, goals: +goals, week: +week, competition, date, avg7: +avg7, avg30: +avg30 };
        });
        const sorted = [...rows].sort((a, b) => b.goals - a.goals).slice(0, 5);
        setLatestStats(sorted);
      })
      .catch(() => {});
  }, []);

  return (
    <>
      <Head>
        <title>BestMostLast — Premier League Stats</title>
        <meta name="description" content="Beautiful Premier League data journalism" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <div className="min-h-screen bg-gray-950 text-white flex flex-col">
        <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Image src="/logo/logobml.png" alt="BestMostLast" width={40} height={40} className="rounded" />
            <span className="text-xl font-black tracking-tight bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">BestMostLast</span>
          </div>
          <nav className="flex gap-6 text-sm font-medium text-gray-400">
            <Link href="/" className="text-white">Home</Link>
            <Link href="/charts" className="hover:text-cyan-400 transition-colors">Charts</Link>
          </nav>
        </header>

        <main className="max-w-4xl mx-auto px-6 py-16">
          <h1 className="text-5xl font-black tracking-tight mb-4">
            Premier League<br />
            <span className="text-emerald-400">Data Stories</span>
          </h1>
          <p className="text-gray-400 text-lg mb-12 max-w-xl">
            Real-time stats, beautiful charts, and deep dives into the Premier League.
          </p>

          {latestStats.length > 0 && (
            <section>
              <h2 className="text-xl font-bold mb-4 text-gray-300">Top Scorers</h2>
              <div className="grid gap-3">
                {latestStats.map((s, i) => (
                  <div key={i} className="flex items-center justify-between bg-gray-900 rounded-xl px-5 py-4 border border-gray-800">
                    <div>
                      <span className="font-bold text-white">{s.player}</span>
                      <span className="ml-2 text-sm text-gray-500">{s.team}</span>
                    </div>
                    <span className="text-2xl font-black text-emerald-400">{s.goals}</span>
                  </div>
                ))}
              </div>
              <div className="mt-6">
                <Link href="/charts" className="inline-block bg-emerald-500 hover:bg-emerald-400 text-black font-bold px-6 py-3 rounded-full transition-colors">
                  View All Charts →
                </Link>
              </div>
            </section>
          )}

          {latestStats.length === 0 && (
            <div className="text-center py-24 text-gray-600">
              <p className="text-lg">Add data to <code className="text-gray-500">public/data/premier-league.csv</code> to get started.</p>
              <Link href="/charts" className="mt-6 inline-block bg-emerald-500 hover:bg-emerald-400 text-black font-bold px-6 py-3 rounded-full transition-colors">
                Explore Charts →
              </Link>
            </div>
          )}
        </main>

        <footer className="border-t border-gray-800 px-6 py-8 mt-16">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <Image src="/logo/logobml.png" alt="BestMostLast" width={32} height={32} className="rounded" />
                <span className="font-bold text-gray-300">BestMostLast</span>
              </div>
              <div className="flex gap-4">
                <a href="https://x.com/bestmostlast" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-cyan-400 transition-colors">
                  Twitter
                </a>
                <a href="https://www.youtube.com/@bestmostlast" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-cyan-400 transition-colors">
                  YouTube
                </a>
                <a href="https://www.instagram.com/bestmostlast" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-cyan-400 transition-colors">
                  Instagram
                </a>
              </div>
            </div>
            <div className="text-center text-xs text-gray-600">
              <p>© 2026 BestMostLast. Sports data journalism. All rights reserved.</p>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
}
