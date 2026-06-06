import Head from "next/head";
import { useState, useEffect } from "react";
import StatChart from "../components/StatChart";
import PlayerComparison from "../components/PlayerComparison";
import SiteHeader from "../components/SiteHeader";
import SiteFooter from "../components/SiteFooter";

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
      <div className="min-h-screen bg-ink text-silver flex flex-col">
        <SiteHeader active="/charts" />

        <main className="max-w-4xl w-full mx-auto px-6 py-12">
          <h1 className="text-3xl font-black mb-8 text-silver">Charts</h1>

          {data.length === 0 ? (
            <div className="text-center py-24 text-steel">
              <p>No data yet. Add rows to <code className="text-silver">public/data/premier-league.csv</code></p>
            </div>
          ) : (
            <div className="space-y-10">
              <section>
                <h2 className="text-lg font-bold text-silver mb-3">Player Goal Timeline</h2>
                <div className="flex flex-wrap gap-2 mb-4">
                  {players.map((p) => (
                    <button
                      key={p}
                      onClick={() => setActivePlayer(p)}
                      className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                        activePlayer === p
                          ? "bg-brand text-ink"
                          : "bg-gunmetal text-steel hover:bg-navy"
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
                <StatChart data={playerData} title={`${activePlayer} — Goals by Week`} dataKey="goals" />
              </section>

              <section>
                <h2 className="text-lg font-bold text-silver mb-3">Compare Players (up to 4)</h2>
                <div className="flex flex-wrap gap-2 mb-4">
                  {players.map((p) => (
                    <button
                      key={p}
                      onClick={() => togglePlayer(p)}
                      className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                        selected.includes(p)
                          ? "bg-data text-ink"
                          : "bg-gunmetal text-steel hover:bg-navy"
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

        <SiteFooter />
      </div>
    </>
  );
}
