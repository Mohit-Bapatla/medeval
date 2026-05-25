"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

function getBarColor(value: number): string {
  if (value >= 0.75) return "#16a34a";
  if (value >= 0.5) return "#b45309";
  return "#dc2626";
}

export function MetricBarChart({
  data,
  title = "Aggregate Metrics",
}: {
  data: { name: string; value: number }[];
  title?: string;
}) {
  return (
    <div className="rounded-lg border border-line bg-white p-5 shadow-sm">
      <p className="mb-4 text-sm font-semibold text-ink">{title}</p>
      <div className="h-56">
        <ResponsiveContainer height="100%" width="100%">
          <BarChart data={data} margin={{ top: 2, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#d7dee5" strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 11, fill: "#3a4650" }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              domain={[0, 1]}
              tickFormatter={(v) => `${Math.round(v * 100)}%`}
              tick={{ fontSize: 11, fill: "#3a4650" }}
              axisLine={false}
              tickLine={false}
              width={40}
            />
            <Tooltip
              formatter={(value) => [
                `${Math.round(Number(value) * 100)}%`,
                "Score",
              ]}
              contentStyle={{
                border: "1px solid #d7dee5",
                borderRadius: 8,
                fontSize: 12,
                boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
              }}
            />
            <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={40}>
              {data.map((entry) => (
                <Cell key={entry.name} fill={getBarColor(entry.value)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-3 text-xs text-graphite">
        Green ≥ 75% · Amber ≥ 50% · Red &lt; 50%
      </p>
    </div>
  );
}
