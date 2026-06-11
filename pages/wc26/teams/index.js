import Head from "next/head";
import Link from "next/link";
import SiteHeader from "../../../components/SiteHeader";
import SiteFooter from "../../../components/SiteFooter";
import { loadTeams } from "../../../lib/wc26";
import { teamSlug } from "../../../lib/teamSlug";

export async function getStaticProps() {
  return { props: { teams: loadTeams() } };
}

export default function TeamsIndex({ teams }) {
  return (
    <>
      <Head>
        <title>WC 2026 Countries — BestMostLast</title>
        <meta name="description" content="All 48 World Cup 2026 nations." />
      </Head>
      <div className="min-h-screen bg-ink text-silver flex flex-col">
        <SiteHeader active="/wc26" />

        <main className="max-w-6xl w-full mx-auto px-5 sm:px-6 py-12 flex-1">
          <Link href="/wc26" className="text-steel hover:text-silver text-sm">
            ← WC 2026
          </Link>
          <h1 className="text-4xl font-black text-silver mt-3 mb-8">
            All {teams.length} Nations
          </h1>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {teams.map((t) => (
              <Link
                key={t.name}
                href={`/wc26/teams/${teamSlug(t.name)}`}
                className="flex items-center gap-3 rounded-xl border border-shadow bg-gunmetal/40 hover:border-steel px-4 py-3 transition"
              >
                {t.flag ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={`/wc26/flags/${t.flag}`}
                    alt={t.name}
                    className="w-8 h-6 object-cover rounded-sm border border-shadow"
                  />
                ) : (
                  <span className="w-8 h-6 rounded-sm bg-shadow" />
                )}
                <span className="text-silver text-sm font-semibold truncate">
                  {t.name}
                </span>
              </Link>
            ))}
          </div>
        </main>

        <SiteFooter />
      </div>
    </>
  );
}
