import Head from "next/head";
import Link from "next/link";
import Image from "next/image";
import { useState, useMemo } from "react";
import SiteHeader from "../../components/SiteHeader";
import SiteFooter from "../../components/SiteFooter";
import MatchCard from "../../components/MatchCard";
import { loadMatches } from "../../lib/wc26";

export async function getStaticProps() {
  const matches = loadMatches();
  const groups = [...new Set(matches.map((m) => m.group).filter(Boolean))].sort();
  return { props: { matches, groups } };
}

export default function WC26Hub({ matches, groups }) {
  const [group, setGroup] = useState("ALL");

  const shown = useMemo(
    () => (group === "ALL" ? matches : matches.filter((m) => m.group === group)),
    [group, matches]
  );

  const videoCount = matches.filter((m) => m.hasVideo).length;

  return (
    <>
      <Head>
        <title>World Cup 2026 — BestMostLast</title>
        <meta
          name="description"
          content="Every World Cup 2026 matchup, decoded: records, head-to-head, players to watch."
        />
      </Head>
      <div className="min-h-screen bg-ink text-silver flex flex-col">
        <SiteHeader active="/wc26" />

        <main className="max-w-6xl w-full mx-auto px-5 sm:px-6 py-12 flex-1">
          {/* Hero */}
          <section className="mb-10">
            <div className="flex items-center gap-3 mb-2">
              <Image
                src="/logo/new/crown-simple.png"
                alt=""
                width={40}
                height={40}
                className="opacity-90"
              />
              <p className="text-xs font-bold uppercase tracking-widest text-gold">
                June 11 – July 19, 2026
              </p>
            </div>
            <h1 className="text-4xl md:text-5xl font-black tracking-tight text-silver mb-3">
              World Cup 2026
            </h1>
            <p className="text-steel text-lg max-w-2xl">
              Every group-stage matchup decoded — World Cup records, head-to-head
              history, and the players to watch. {videoCount} match Shorts live,
              more landing as the tournament nears.
            </p>
            <div className="flex gap-3 mt-5">
              <Link
                href="/wc26/teams"
                className="inline-block bg-gunmetal hover:bg-navy text-silver font-bold px-5 py-2.5 rounded-full transition-colors"
              >
                Browse by country →
              </Link>
            </div>
          </section>

          {/* Group filter */}
          <div className="flex flex-wrap gap-2 mb-6">
            {["ALL", ...groups].map((g) => (
              <button
                key={g}
                onClick={() => setGroup(g)}
                className={`px-3 py-1 rounded-full text-sm font-bold transition-colors ${
                  group === g
                    ? "bg-brand text-ink"
                    : "bg-gunmetal text-steel hover:bg-navy"
                }`}
              >
                {g === "ALL" ? "All" : `Group ${g}`}
              </button>
            ))}
          </div>

          {/* Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {shown.map((m) => (
              <MatchCard key={m.slug} m={m} />
            ))}
          </div>
        </main>

        <SiteFooter />
      </div>
    </>
  );
}
