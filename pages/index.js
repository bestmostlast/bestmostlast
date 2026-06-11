import Head from "next/head";
import Link from "next/link";
import { useEffect, useState } from "react";
import SiteHeader from "../components/SiteHeader";
import SiteFooter from "../components/SiteFooter";
import MatchCard from "../components/MatchCard";

function UpcomingRow({ m }) {
  const ko = new Date(m.date + "T" + (m.time?.split("·")[0]?.trim()?.replace(" CET","") || "12:00") + ":00+01:00");
  const dateStr = ko.toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" });
  const timeStr = ko.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" }) + " CET";

  return (
    <Link
      href={`/wc26/${m.slug}`}
      className="flex items-center justify-between gap-3 py-2.5 border-b border-shadow/50 hover:bg-shadow/30 px-2 rounded transition-colors group"
    >
      <div className="flex items-center gap-2 min-w-0">
        <span className="text-[10px] font-bold text-steel shrink-0 w-10">Gr {m.group}</span>
        <span className="text-silver text-xs font-semibold truncate">
          {m.teamA} <span className="text-steel font-normal">v</span> {m.teamB}
        </span>
      </div>
      <div className="text-right shrink-0">
        <p className="text-[10px] text-steel">{dateStr}</p>
        <p className="text-[11px] text-brand font-bold">{timeStr}</p>
      </div>
    </Link>
  );
}

export default function Home() {
  const [videos, setVideos] = useState([]);
  const [upcoming, setUpcoming] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch("/api/latest-matches").then(r => r.json()).catch(() => []),
      fetch("/api/upcoming-matches").then(r => r.json()).catch(() => []),
    ]).then(([v, u]) => {
      setVideos(v);
      setUpcoming(u);
      setLoading(false);
    });
  }, []);

  return (
    <>
      <Head>
        <title>BestMostLast — Sports Data Journalism</title>
        <meta name="description" content="Best · Most · Last — data journalism through sport" />
      </Head>
      <div className="min-h-screen bg-ink text-silver flex flex-col">
        <SiteHeader active="/" />

        <main className="max-w-6xl w-full mx-auto px-5 sm:px-4 py-8 flex-1">
          <div className="flex gap-6 items-start">

            {/* Left: videos */}
            <div className="flex-1 min-w-0">
              {loading ? (
                <div className="text-steel text-sm py-12 text-center">Loading…</div>
              ) : videos.length > 0 ? (
                <>
                  <h2 className="text-xs font-bold uppercase tracking-widest text-steel mb-4">Latest Videos</h2>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                    {videos.map((m) => (
                      <MatchCard m={m} key={m.slug} />
                    ))}
                  </div>
                </>
              ) : (
                <div className="flex flex-col items-center justify-center py-24 text-center">
                  <span className="text-4xl mb-4">⚽</span>
                  <p className="text-silver font-bold text-lg mb-1">Tournament kicks off June 11</p>
                  <p className="text-steel text-sm">Videos publish before and after each match.</p>
                  <Link href="/wc26" className="mt-6 px-5 py-2 bg-brand text-ink font-bold rounded-full text-sm hover:brightness-110 transition">
                    See all matches →
                  </Link>
                </div>
              )}
            </div>

            {/* Right: upcoming matches panel */}
            <aside className="w-64 shrink-0 hidden md:block">
              <div className="rounded-xl border border-shadow bg-gunmetal/20 overflow-hidden">
                <div className="px-3 py-2.5 border-b border-shadow flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-widest text-steel">Upcoming</span>
                  <Link href="/wc26" className="text-[10px] text-brand hover:underline font-semibold">All →</Link>
                </div>
                <div className="px-1 py-1 max-h-[70vh] overflow-y-auto">
                  {upcoming.length > 0
                    ? upcoming.map(m => <UpcomingRow key={m.slug} m={m} />)
                    : <p className="text-steel text-xs px-2 py-3">No upcoming matches</p>
                  }
                </div>
              </div>
            </aside>

          </div>
        </main>

        <SiteFooter />
      </div>
    </>
  );
}
