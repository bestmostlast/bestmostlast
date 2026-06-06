import Image from "next/image";

const SOCIAL = [
  { href: "https://x.com/bestmostlast", label: "Twitter" },
  { href: "https://www.youtube.com/@bestmostlast", label: "YouTube" },
  { href: "https://www.instagram.com/bestmostlast", label: "Instagram" },
];

export default function SiteFooter() {
  return (
    <footer className="border-t border-shadow px-6 py-8 mt-16">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <Image
              src="/logo/new/crown-mark.png"
              alt="BestMostLast"
              width={28}
              height={28}
              className="rounded"
            />
            <span className="font-bold text-silver">BestMostLast</span>
          </div>
          <div className="flex gap-4 text-sm">
            {SOCIAL.map((s) => (
              <a
                key={s.label}
                href={s.href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-steel hover:text-gold transition-colors"
              >
                {s.label}
              </a>
            ))}
          </div>
        </div>
        <p className="text-center text-xs text-steel">
          © 2026 BestMostLast. Sports data journalism. All rights reserved.
        </p>
      </div>
    </footer>
  );
}
