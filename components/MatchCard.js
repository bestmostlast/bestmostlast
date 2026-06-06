import Link from "next/link";

/**
 * A single WC26 match tile for the grid. Uses the optimized thumbnail still;
 * a video badge marks matches whose Short has been rendered.
 */
export default function MatchCard({ m }) {
  return (
    <Link
      href={`/wc26/${m.slug}`}
      className="group block rounded-xl overflow-hidden border border-shadow bg-gunmetal/40 hover:border-steel transition"
    >
      <div className="relative aspect-[9/16] bg-shadow">
        {m.hasThumb ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={`/wc26/thumbs/${m.slug}.jpg`}
            alt={`${m.teamA} vs ${m.teamB}`}
            loading="lazy"
            className="w-full h-full object-cover group-hover:scale-[1.03] transition-transform"
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center text-center px-3">
            <span className="text-silver font-bold text-sm">{m.teamA}</span>
            <span className="text-steel text-xs my-1">vs</span>
            <span className="text-silver font-bold text-sm">{m.teamB}</span>
            <span className="mt-3 text-[10px] uppercase tracking-widest text-steel">
              Card coming soon
            </span>
          </div>
        )}
        {m.hasVideo && (
          <span className="absolute top-2 right-2 bg-brand text-ink text-[10px] font-black px-2 py-0.5 rounded-full">
            ▶ VIDEO
          </span>
        )}
        {m.group && (
          <span className="absolute top-2 left-2 bg-ink/80 text-silver text-[10px] font-bold px-2 py-0.5 rounded">
            GRP {m.group}
          </span>
        )}
      </div>
      <div className="px-3 py-2">
        <p className="text-silver text-sm font-bold leading-tight truncate">
          {m.teamA} <span className="text-steel font-normal">v</span> {m.teamB}
        </p>
        <p className="text-steel text-[11px] mt-0.5 truncate">
          {m.date}
          {m.city ? ` · ${m.city}` : ""}
        </p>
      </div>
    </Link>
  );
}
