import Link from "next/link";

// Primary country colors for kit-style accents
const TEAM_COLORS = {
  "Mexico":               "#006847",
  "South Africa":         "#007a4d",
  "South Korea":          "#c60c30",
  "Czech Republic":       "#d7141a",
  "Canada":               "#ff0000",
  "Bosnia & Herzegovina": "#002395",
  "USA":                  "#002868",
  "Paraguay":             "#d52b1e",
  "Qatar":                "#8d1b3d",
  "Switzerland":          "#ff0000",
  "Brazil":               "#009c3b",
  "Morocco":              "#c1272d",
  "Haiti":                "#00209f",
  "Scotland":             "#003078",
  "Australia":            "#00843d",
  "Turkey":               "#e30a17",
  "Germany":              "#000000",
  "Curacao":              "#003da5",
  "Netherlands":          "#ff6600",
  "Japan":                "#bc002d",
  "Ivory Coast":          "#f77f00",
  "Ecuador":              "#ffd100",
  "Sweden":               "#006aa7",
  "Tunisia":              "#e70013",
  "Spain":                "#c60b1e",
  "Cape Verde":           "#003893",
  "Belgium":              "#000000",
  "Egypt":                "#ce1126",
  "Saudi Arabia":         "#006c35",
  "Uruguay":              "#5aaaa5",
  "Iran":                 "#239f40",
  "New Zealand":          "#00247d",
  "France":               "#002395",
  "Senegal":              "#00853f",
  "Iraq":                 "#007a3d",
  "Norway":               "#ef2b2d",
  "Argentina":            "#74acdf",
  "Algeria":              "#006233",
  "Austria":              "#ed2939",
  "Jordan":               "#007a3d",
  "Portugal":             "#006600",
  "DR Congo":             "#007fff",
  "England":              "#cf142b",
  "Croatia":              "#ff0000",
  "Ghana":                "#006b3f",
  "Panama":               "#da121a",
  "Uzbekistan":           "#1eb53a",
  "Colombia":             "#fcd116",
  "Poland":               "#dc143c",
  "Serbia":               "#c6363c",
};

function teamColor(name) {
  return TEAM_COLORS[name] || "#4f93c2";
}

export default function MatchCard({ m }) {
  const activeVideoId = m.hasPostVideo ? m.youtubePostId : (m.hasVideo ? m.youtubeId : null);
  const isResult = m.hasPostVideo;
  const colorA = teamColor(m.teamA);
  const colorB = teamColor(m.teamB);

  return (
    <Link
      href={`/wc26/${m.slug}`}
      className="group block rounded-xl overflow-hidden border border-shadow bg-gunmetal/40 hover:border-steel/60 transition-all hover:shadow-lg"
      style={{ "--ca": colorA, "--cb": colorB }}
    >
      {/* Color bar */}
      <div
        className="h-1"
        style={{ background: `linear-gradient(90deg, ${colorA} 50%, ${colorB} 50%)` }}
      />

      {/* Video embed */}
      <div className="relative aspect-[9/16] bg-shadow">
        <iframe
          className="w-full h-full pointer-events-none"
          src={`https://www.youtube.com/embed/${activeVideoId}?autoplay=0&rel=0&modestbranding=1`}
          title={`${m.teamA} vs ${m.teamB}`}
          allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        />

        {/* Badge */}
        {isResult ? (
          <span className="absolute top-2 right-2 bg-gold text-ink text-[10px] font-black px-2 py-0.5 rounded-full">
            FT
          </span>
        ) : (
          <span className="absolute top-2 right-2 bg-brand text-ink text-[10px] font-black px-2 py-0.5 rounded-full">
            ▶ SHORT
          </span>
        )}

        {m.group && (
          <span className="absolute top-2 left-2 bg-ink/80 text-silver text-[10px] font-bold px-2 py-0.5 rounded">
            GRP {m.group}
          </span>
        )}
      </div>

      {/* Footer */}
      <div className="px-3 py-2">
        <p className="text-silver text-sm font-bold leading-tight truncate">
          <span style={{ color: colorA }}>{m.teamA}</span>
          {isResult && m.scoreA != null
            ? <span className="text-gold mx-1">{m.scoreA}–{m.scoreB}</span>
            : <span className="text-steel font-normal mx-1">v</span>
          }
          <span style={{ color: colorB }}>{m.teamB}</span>
        </p>
        <p className="text-steel text-[11px] mt-0.5 truncate">
          {m.date}{m.city ? ` · ${m.city}` : ""}
        </p>
      </div>
    </Link>
  );
}
