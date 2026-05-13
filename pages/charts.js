import Head from "next/head";
import Link from "next/link";
import { useState, useEffect } from "react";
import StatChart from "../components/StatChart";
import PlayerComparison from "../components/PlayerComparison";

function parseCSV(text) {
  const lines = text.trim().split("\n");
  const headers = lines[0].split(",");
  return lines.slice(1).map((line) => {
    const vals = line.split(",");
    return Object.fromEntries(
      headers.map((h, i) => [h.trim(), isNaN(vals[i]) ? vals[i]?.trim() : +vals[i]])
    );
  });
}

export default function Charts() {
  const [data, setData] = useState([]);
  const [players, setPlayers] = useState([]);
  const [selected, setSelected] = useState([]);
  const [activePlayer, setActivePlayer] = useState(null);

  useEffect(() => {
    fetch("/data/premier-league.csv")
      .then((r) => r.text())
      .then((text) => {
        const rows = parseCSV(text);
        setData(rows);
        const unique = [...new Set(rows.map((r) => r.player))];
        setPlayers(unique);
        if (unique.length > 0) {
          setActivePlayer(unique[0]);
          setSelected(unique.slice(0, 2));
        }
      })
      .catch(() => {});
  }, []);

  const playerData = data.filter((r) => r.player === activePlayer);

  const togglePlayer = (p) => {
    setSelected((prev) =>
      prev.includes(p) ? prev.filter((x) => x !== p) : prev.length < 4 ? [...prev, p] : prev
    );
  };

  return (
    <>
      <Head>
        <title>Charts — BEST</title>
      </Head>
      <div className="min-h-screen bg-gray-950 text-white">
        <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
          <Link href="/" className="text-2xl font-black tracking-tight text-emerald-400">BEST</Link>
          <nav className="flex gap-6 text-sm font-medium text-gray-400">
            <Link href="/" className="hover:text-white transition-colors">Home</Link>
            <Link href="/charts" className="text-white">Charts</Link>
          </nav>
        </header>

        <main className="max-w-4xl mx-auto px-6 py-12">
          <h1 className="text-3xl font-black mb-8">Charts</h1>

          {data.length === 0 ? (
            <div className="text-center py-24 text-gray-600">
              <p>No data yet. Add rows to <code className="text-gray-500">public/data/premier-league.csv</code></p>
            </div>
          ) : (
            <div className="space-y-10">
              <section>
                <h2 className="text-lg font-bold text-gray-300 mb-3">Player Goal Timeline</h2>
                <div className="flex flex-wrap gap-2 mb-4">
                  {players.map((p) => (
                    <button
                      key={p}
                      onClick={() => setActivePlayer(p)}
                      className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                        activePlayer === p
                          ? "bg-emerald-500 text-black"
                          : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
                <StatChart data={playerData} title={`${activePlayer} — Goals by Week`} dataKey="goals" />
              </section>

              <section>
                <h2 className="text-lg font-bold text-gray-300 mb-3">Compare Players (up to 4)</h2>
                <div className="flex flex-wrap gap-2 mb-4">
                  {players.map((p) => (
                    <button
                      key={p}
                      onClick={() => togglePlayer(p)}
                      className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                        selected.includes(p)
                          ? "bg-indigo-500 text-white"
                          : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
                <PlayerComparison data={data} players={selected} metric="goals" />
              </section>
            </div>
          )}
        </main>
      </div>
    </>
  );
}
