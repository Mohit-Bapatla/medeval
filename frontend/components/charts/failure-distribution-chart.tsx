"use client";

import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

const COLORS = [
  "#dc2626", // danger red — hallucination/incorrect
  "#b45309", // signal amber — partial/citation
  "#2563eb", // blue — retrieval miss
  "#9333ea", // purple — refusal
  "#3a4650", // graphite — other
  "#0f766e", // clinical teal — none/unknown
];

export function FailureDistributionChart({
  counts,
  title = "Failure Distribution",
}: {
  counts: Record<string, number>;
  title?: string;
}) {
  const data = Object.entries(counts).map(([name, value]) => ({
    name: name === "none" ? "No failure" : name.replace(/_/g, " "),
    value,
    raw: name,
  }));

  return (
    <div className="rounded-lg border border-line bg-white p-5 shadow-sm">
      <p className="mb-1 text-sm font-semibold text-ink">{title}</p>
      <p className="mb-3 text-xs text-graphite">
        Distribution of failure types across evaluated responses.
      </p>
      {data.length ? (
        <div className="h-56">
          <ResponsiveContainer height="100%" width="100%">
            <PieChart>
              <Pie
                data={data}
                dataKey="value"
                innerRadius={52}
                outerRadius={80}
                paddingAngle={3}
                nameKey="name"
              >
                {data.map((entry, index) => (
                  <Cell
                    fill={COLORS[index % COLORS.length]}
                    key={entry.raw}
                  />
                ))}
              </Pie>
              <Tooltip
                formatter={(value, name) => [value, name]}
                contentStyle={{
                  border: "1px solid #d7dee5",
                  borderRadius: 8,
                  fontSize: 12,
                  boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
                }}
              />
              <Legend
                iconType="circle"
                iconSize={8}
                wrapperStyle={{ fontSize: 11, color: "#3a4650" }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="flex h-56 items-center justify-center text-sm text-graphite">
          No failure data available.
        </div>
      )}
    </div>
  );
}
