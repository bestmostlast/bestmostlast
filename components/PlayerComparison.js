import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

const COLORS = ["#10b981", "#6366f1", "#f59e0b", "#ef4444", "#3b82f6"];

export default function PlayerComparison({ data, players, metric = "goals" }) {
  if (!data || data.length === 0 || !players || players.length === 0) {
    return (
      <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800 flex items-center justify-center h-64 text-gray-600">
        Select players to compare
      </div>
    );
  }

  const weeks = [...new Set(data.map((r) => r.week))].sort((a, b) => a - b);

  const chartData = weeks.map((week) => {
    const entry = { week };
    players.forEach((player) => {
      const row = data.find((r) => r.player === player && r.week === week);
      entry[player] = row ? row[metric] : 0;
    });
    return entry;
  });

  return (
    <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
      <h3 className="text-lg font-bold text-white mb-4">Player Comparison — {metric}</h3>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="week" stroke="#4b5563" tick={{ fill: "#9ca3af", fontSize: 12 }} />
          <YAxis stroke="#4b5563" tick={{ fill: "#9ca3af", fontSize: 12 }} />
          <Tooltip contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: 8, color: "#f9fafb" }} />
          <Legend wrapperStyle={{ color: "#9ca3af", fontSize: 13 }} />
          {players.map((player, i) => (
            <Bar key={player} dataKey={player} fill={COLORS[i % COLORS.length]} radius={[3, 3, 0, 0]} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
