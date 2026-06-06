import Head from "next/head";
import Link from "next/link";
import Image from "next/image";
import SiteHeader from "../components/SiteHeader";
import SiteFooter from "../components/SiteFooter";

export default function Home() {
  return (
    <>
      <Head>
        <title>BestMostLast — Sports Data Journalism</title>
        <meta name="description" content="Best · Most · Last — beautiful sports data journalism" />
      </Head>
      <div className="min-h-screen bg-ink text-silver flex flex-col">
        <SiteHeader active="/" />

        <main className="max-w-6xl w-full mx-auto px-6 py-16">
          {/* Hero */}
          <section className="mb-16">
            <Image
              src="/logo/new/crown-simple.png"
              alt=""
              width={72}
              height={72}
              priority
              className="mb-5 opacity-95"
            />
            <h1 className="text-5xl md:text-6xl font-black tracking-tight mb-4 text-silver">
              Best · Most · Last
            </h1>
            <p className="text-steel text-lg mb-8 max-w-xl">
              Performance × popularity, ranked over time. Sports data journalism
              rendered as living charts and short-form video.
            </p>
            <Link
              href="/wc26"
              className="inline-flex items-center gap-2 bg-brand hover:brightness-110 text-ink font-bold px-6 py-3 rounded-full transition"
            >
              World Cup 2026 →
            </Link>
          </section>

          {/* WC26 promo strip */}
          <Link
            href="/wc26"
            className="block mb-16 rounded-2xl border border-shadow bg-gunmetal/40 hover:bg-gunmetal/60 transition p-6"
          >
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div>
                <p className="text-xs font-bold uppercase tracking-widest text-gold mb-1">
                  New
                </p>
                <h2 className="text-2xl font-black text-silver">
                  WC 2026 — every match, decoded
                </h2>
                <p className="text-steel text-sm mt-1">
                  72 group-stage matchup cards: records, head-to-head, players to
                  watch.
                </p>
              </div>
              <span className="text-data font-bold whitespace-nowrap">
                Explore →
              </span>
            </div>
          </Link>
        </main>

        <SiteFooter />
      </div>
    </>
  );
}
