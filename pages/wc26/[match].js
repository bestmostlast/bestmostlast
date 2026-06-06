import Head from "next/head";
import Link from "next/link";
import SiteHeader from "../../components/SiteHeader";
import SiteFooter from "../../components/SiteFooter";
import { loadMatches } from "../../lib/wc26";
import { teamSlug } from "../../lib/teamSlug";

export async function getStaticPaths() {
  const matches = loadMatches();
  return {
    paths: matches.map((m) => ({ params: { match: m.slug } })),
    fallback: false,
  };
}

export async function getStaticProps({ params }) {
  const matches = loadMatches();
  const m = matches.find((x) => x.slug === params.match) || null;
  return { props: { m } };
}

function StatRow({ label, a, b }) {
  if (!a && !b) return null;
  return (
    <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 py-2 border-b border-shadow/60">
      <span className="text-right text-silver text-sm font-semibold">{a || "—"}</span>
      <span className="text-[10px] uppercase tracking-widest text-steel">{label}</span>
      <span className="text-left text-silver text-sm font-semibold">{b || "—"}</span>
    </div>
  );
}

export default function MatchPage({ m }) {
  if (!m) return null;

  return (
    <>
      <Head>
        <title>
          {m.teamA} vs {m.teamB} — WC 2026 | BestMostLast
        </title>
        <meta
          name="description"
          content={`World Cup 2026: ${m.teamA} vs ${m.teamB} — records, head-to-head and players to watch.`}
        />
      </Head>
      <div className="min-h-screen bg-ink text-silver flex flex-col">
        <SiteHeader active="/wc26" />

        <main className="max-w-5xl w-full mx-auto px-6 py-10 flex-1">
          <Link href="/wc26" className="text-steel hover:text-silver text-sm">
            ← All WC 2026 matches
          </Link>

          <div className="mt-4 mb-8">
            {m.group && (
              <span className="text-xs font-bold uppercase tracking-widest text-gold">
                Group {m.group} · Matchday {m.matchday}
              </span>
            )}
            <h1 className="text-3xl md:text-4xl font-black text-silver mt-1">
              <Link href={`/wc26/teams/${teamSlug(m.teamA)}`} className="hover:text-data">
                {m.teamA}
              </Link>{" "}
              <span className="text-steel">vs</span>{" "}
              <Link href={`/wc26/teams/${teamSlug(m.teamB)}`} className="hover:text-data">
                {m.teamB}
              </Link>
            </h1>
            <p className="text-steel mt-1">
              {m.date}
              {m.time ? ` · ${m.time}` : ""} · {m.venue}
              {m.city ? `, ${m.city}` : ""}
            </p>
          </div>

          <div className="grid md:grid-cols-[auto_1fr] gap-8 items-start">
            {/* Media */}
            <div className="w-full max-w-[320px] mx-auto md:mx-0">
              <div className="aspect-[9/16] rounded-2xl overflow-hidden border border-shadow bg-shadow">
                {m.hasVideo && m.youtubeId ? (
                  <iframe
                    className="w-full h-full"
                    src={`https://www.youtube.com/embed/${m.youtubeId}`}
                    title={`${m.teamA} vs ${m.teamB} — WC 2026 Short`}
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  />
                ) : m.hasThumb ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={`/wc26/thumbs/${m.slug}.jpg`}
                    alt={`${m.teamA} vs ${m.teamB} card`}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-steel text-sm">
                    Card coming soon
                  </div>
                )}
              </div>
              {m.hasVideo && m.videoUrl && !m.youtubeId && (
                <a
                  href={m.videoUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-2 block text-center text-brand text-sm font-bold hover:underline"
                >
                  ▶ Watch the Short
                </a>
              )}
              {!m.hasVideo && m.hasThumb && (
                <p className="text-center text-steel text-xs mt-2">
                  Video Short coming soon
                </p>
              )}
            </div>

            {/* Data */}
            <div>
              <section className="mb-6">
                <h2 className="text-lg font-bold text-silver mb-2">World Cup record</h2>
                <StatRow label="World Cups" a={m.worldCups[0]} b={m.worldCups[1]} />
                <StatRow label="Matches played" a={m.played[0]} b={m.played[1]} />
                <StatRow label="Points / game" a={m.ppg[0]} b={m.ppg[1]} />
              </section>

              {(m.headline[0] || m.headline[1]) && (
                <section className="mb-6">
                  <h2 className="text-lg font-bold text-silver mb-2">The storyline</h2>
                  <div className="grid sm:grid-cols-2 gap-3">
                    {[0, 1].map((i) => (
                      <div
                        key={i}
                        className="rounded-xl border border-shadow bg-gunmetal/40 p-4"
                      >
                        <p className="text-xs font-bold text-gold uppercase tracking-widest mb-1">
                          {i === 0 ? m.teamA : m.teamB}
                        </p>
                        <p className="text-silver text-sm font-semibold">{m.headline[i]}</p>
                        {m.hook[i] && (
                          <p className="text-steel text-xs mt-1">{m.hook[i]}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {(m.watch[0] || m.watch[1]) && (
                <section>
                  <h2 className="text-lg font-bold text-silver mb-2">Players to watch</h2>
                  <div className="grid sm:grid-cols-2 gap-3">
                    {[0, 1].map((i) => (
                      <div key={i} className="rounded-xl border border-shadow p-4">
                        <p className="text-xs font-bold text-data uppercase tracking-widest mb-1">
                          {i === 0 ? m.teamA : m.teamB}
                        </p>
                        <p className={m.watch[i] ? "text-silver text-sm" : "text-steel text-sm italic"}>
                          {m.watch[i] || "Lineup TBC"}
                        </p>
                      </div>
                    ))}
                  </div>
                </section>
              )}
            </div>
          </div>
        </main>

        <SiteFooter />
      </div>
    </>
  );
}
