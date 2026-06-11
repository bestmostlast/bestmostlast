import Head from "next/head";
import Link from "next/link";
import { useState } from "react";
import StatChart from "../components/StatChart";
import PlayerComparison from "../components/PlayerComparison";
import SiteHeader from "../components/SiteHeader";
import SiteFooter from "../components/SiteFooter";

const MOCK_PLAYERS = ["Messi", "Ronaldo", "Mbappé"];
const MOCK_DATA = [
  { week: 1, player: "Messi", goals: 2 },
  { week: 2, player: "Messi", goals: 1 },
  { week: 3, player: "Messi", goals: 3 },
  { week: 1, player: "Ronaldo", goals: 1 },
  { week: 2, player: "Ronaldo", goals: 2 },
  { week: 3, player: "Ronaldo", goals: 1 },
  { week: 1, player: "Mbappé", goals: 3 },
  { week: 2, player: "Mbappé", goals: 2 },
  { week: 3, player: "Mbappé", goals: 4 },
];

export default function Charts() {
  // No live dataset wired up yet — the player-timeline charts go live once real
  // sourced data lands. (The previous demo CSV was removed.)
  // I've added mock data here to demonstrate the chart components.
  const [data] = useState(MOCK_DATA);
  const [players] = useState(MOCK_PLAYERS);

  const [selected, setSelected] = useState([]);
  const [activePlayer, setActivePlayer] = useState(null);

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

        <main className="max-w-4xl w-full mx-auto px-5 sm:px-6 py-12">
          <h1 className="text-3xl font-black mb-8 text-silver">Charts</h1>

          {data.length === 0 ? (
            <div className="rounded-2xl border border-shadow bg-gunmetal/40 px-6 py-16 text-center">
              <p className="text-xs font-bold uppercase tracking-widest text-gold mb-2">
                Coming soon
              </p>
              <h2 className="text-2xl font-black text-silver mb-2">
                Interactive charts are on the way
              </h2>
              <p className="text-steel max-w-md mx-auto mb-6">
                Player and team timelines built on real, sourced data. In the
                meantime, explore the World Cup 2026 matchups.
              </p>
              <Link
                href="/wc26"
                className="inline-block bg-brand hover:brightness-110 text-ink font-bold px-6 py-3 rounded-full transition"
              >
                World Cup 2026 →
              </Link>
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
