import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

export default function StatChart({ data, title, dataKey = "goals", color = "#10b981" }) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800 flex items-center justify-center h-64 text-gray-600">
        No data available
      </div>
    );
  }

  return (
    <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
      {title && <h3 className="text-lg font-bold text-white mb-4">{title}</h3>}
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="week" stroke="#4b5563" tick={{ fill: "#9ca3af", fontSize: 12 }} label={{ value: "Week", position: "insideBottom", offset: -2, fill: "#6b7280", fontSize: 12 }} />
          <YAxis stroke="#4b5563" tick={{ fill: "#9ca3af", fontSize: 12 }} />
          <Tooltip contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: 8, color: "#f9fafb" }} />
          <Legend wrapperStyle={{ color: "#9ca3af", fontSize: 13 }} />
          <Line type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2} dot={false} name={dataKey} />
          {data[0]?.avg7 !== undefined && (
            <Line type="monotone" dataKey="avg7" stroke="#6366f1" strokeWidth={1.5} dot={false} strokeDasharray="4 2" name="7-day avg" />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
