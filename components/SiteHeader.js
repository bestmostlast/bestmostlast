import Link from "next/link";
import Image from "next/image";

const NAV = [
  { href: "/charts", label: "Charts" },
];

export default function SiteHeader({ active = "/" }) {
  const isWC26 = active === "/wc26" || active?.startsWith?.("/wc26");

  return (
    <header className="sticky top-0 z-30 border-b border-shadow bg-ink/95 backdrop-blur px-6 py-0">
      <div className="max-w-6xl mx-auto flex items-center justify-between h-14">

        {/* Left: crown + wordmark + tagline */}
        <Link href="/" className="flex items-center gap-3 group shrink-0">
          <Image
            src="/logo/new/crown-simple.png"
            alt="BestMostLast"
            width={28}
            height={28}
            className="opacity-90 group-hover:opacity-100 transition"
            priority
          />
          <div className="flex items-baseline gap-2">
            <span className="text-base font-black tracking-tight bml-gradient-text leading-none">
              Best·Most·Last
            </span>
            <span className="text-[11px] text-steel font-medium leading-none hidden sm:block">
              data journalism
            </span>
          </div>
        </Link>

        {/* Right: nav + WC26 fancy tab */}
        <nav className="flex items-center gap-1">
          {NAV.map((n) => (
            <Link
              key={n.href}
              href={n.href}
              className={`px-3 py-1 text-sm font-semibold rounded transition-colors ${
                active === n.href
                  ? "text-silver"
                  : "text-steel hover:text-silver"
              }`}
            >
              {n.label}
            </Link>
          ))}

          {/* WC26 tab — fancy pill */}
          <Link
            href="/wc26"
            className={`relative ml-2 flex items-center gap-1.5 px-4 py-1.5 rounded-full text-sm font-black tracking-tight transition-all ${
              isWC26
                ? "bg-brand text-ink shadow-[0_0_12px_rgba(79,147,194,0.5)]"
                : "bg-gunmetal text-silver hover:bg-navy hover:shadow-[0_0_8px_rgba(79,147,194,0.3)] border border-shadow hover:border-brand/40"
            }`}
          >
            <span className="text-base leading-none">⚽</span>
            <span>WC 2026</span>
            {!isWC26 && (
              <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-brand animate-pulse" />
            )}
          </Link>
        </nav>
      </div>
    </header>
  );
}
