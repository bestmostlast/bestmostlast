import Head from "next/head";
import Link from "next/link";
import SiteHeader from "../../../components/SiteHeader";
import SiteFooter from "../../../components/SiteFooter";
import MatchCard from "../../../components/MatchCard";
import { loadTeams, loadMatches } from "../../../lib/wc26";
import { teamSlug } from "../../../lib/teamSlug";

export async function getStaticPaths() {
  const teams = loadTeams();
  return {
    paths: teams.map((t) => ({ params: { country: teamSlug(t.name) } })),
    fallback: false,
  };
}

export async function getStaticProps({ params }) {
  const teams = loadTeams();
  const allMatches = loadMatches();
  const team = teams.find((t) => teamSlug(t.name) === params.country) || null;
  const matches = team
    ? team.matches
        .map((tm) => allMatches.find((m) => m.slug === tm.slug))
        .filter(Boolean)
        .sort((a, b) => a.no - b.no)
    : [];
  return { props: { team, matches } };
}

export default function CountryPage({ team, matches }) {
  if (!team) return null;
  const group = matches[0]?.group;

  return (
    <>
      <Head>
        <title>{team.name} — WC 2026 | BestMostLast</title>
        <meta
          name="description"
          content={`${team.name} at the 2026 World Cup — group-stage fixtures and matchup cards.`}
        />
      </Head>
      <div className="min-h-screen bg-ink text-silver flex flex-col">
        <SiteHeader active="/wc26" />

        <main className="max-w-6xl w-full mx-auto px-5 sm:px-6 py-10 flex-1">
          <Link href="/wc26/teams" className="text-steel hover:text-silver text-sm">
            ← All nations
          </Link>

          <div className="flex items-center gap-4 mt-4 mb-8">
            {team.flag && (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={`/wc26/flags/${team.flag}`}
                alt={team.name}
                className="w-16 h-11 object-cover rounded border border-shadow"
              />
            )}
            <div>
              <h1 className="text-4xl font-black text-silver">{team.name}</h1>
              {group && (
                <p className="text-steel">
                  Group {group} · {matches.length} group-stage matches
                </p>
              )}
            </div>
          </div>

          {/* All-time World Cup record */}
          {team.record ? (
            <section className="mb-10">
              <div className="flex items-baseline justify-between mb-3 flex-wrap gap-2">
                <h2 className="text-lg font-bold text-silver">All-time World Cup record</h2>
                <span className="text-sm font-bold text-gold">
                  {team.record.appearances} appearances
                  {team.record.titles > 0
                    ? ` · ${team.record.titles}× champions`
                    : ` · best: ${team.record.best}`}
                </span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
                {[
                  ["Played", team.record.played],
                  ["Won", team.record.w],
                  ["Drawn", team.record.d],
                  ["Lost", team.record.l],
                  ["Goals for", team.record.gf],
                  ["Goals against", team.record.ga],
                  ["Pts / game", team.record.ppg],
                ].map(([label, val]) => (
                  <div
                    key={label}
                    className="rounded-xl border border-shadow bg-gunmetal/40 px-3 py-3 text-center"
                  >
                    <div className="text-2xl font-black text-silver">{val}</div>
                    <div className="text-[10px] uppercase tracking-widest text-steel mt-1">
                      {label}
                    </div>
                  </div>
                ))}
              </div>

              {team.topScorers.length > 0 && (
                <div className="mt-5">
                  <h3 className="text-sm font-bold text-silver mb-2">
                    Top World Cup scorers
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {team.topScorers.map((s) => (
                      <span
                        key={s.player}
                        className="inline-flex items-center gap-2 rounded-full border border-shadow bg-gunmetal/40 pl-3 pr-2 py-1 text-sm"
                      >
                        <span className="text-silver">{s.player}</span>
                        <span className="bg-data text-ink font-black text-xs rounded-full px-2 py-0.5">
                          {s.goals}
                        </span>
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </section>
          ) : (
            <section className="mb-10">
              <div className="rounded-xl border border-shadow bg-gunmetal/40 px-5 py-4">
                <p className="text-gold text-sm font-bold uppercase tracking-widest mb-1">
                  World Cup debut
                </p>
                <p className="text-steel text-sm">
                  {team.name} are appearing at the FIFA World Cup for the first time
                  in 2026 — no prior tournament record.
                </p>
              </div>
            </section>
          )}

          <h2 className="text-lg font-bold text-silver mb-4">Group-stage fixtures</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {matches.map((m) => (
              <MatchCard key={m.slug} m={m} />
            ))}
          </div>
        </main>

        <SiteFooter />
      </div>
    </>
  );
}
