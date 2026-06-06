import Link from "next/link";
import Image from "next/image";

const NAV = [
  { href: "/", label: "Home" },
  { href: "/wc26", label: "WC 2026" },
  { href: "/charts", label: "Charts" },
];

export default function SiteHeader({ active = "/" }) {
  return (
    <header className="sticky top-0 z-30 border-b border-shadow bg-ink/90 backdrop-blur px-6 py-3">
      <div className="max-w-6xl mx-auto flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3 group">
          <Image
            src="/logo/new/crown-simple.png"
            alt="BestMostLast"
            width={36}
            height={36}
            className="rounded transition-transform group-hover:scale-105"
            priority
          />
          <span className="text-lg font-black tracking-tight bml-gradient-text">
            BestMostLast
          </span>
        </Link>
        <nav className="flex gap-6 text-sm font-semibold">
          {NAV.map((n) => (
            <Link
              key={n.href}
              href={n.href}
              className={
                active === n.href
                  ? "text-silver"
                  : "text-steel hover:text-silver transition-colors"
              }
            >
              {n.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
