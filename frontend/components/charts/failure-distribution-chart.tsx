"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

const colors = ["#0f766e", "#b45309", "#3a4650", "#2563eb", "#9333ea", "#be123c"];

export function FailureDistributionChart({
  counts,
}: {
  counts: Record<string, number>;
}) {
  const data = Object.entries(counts).map(([name, value]) => ({ name, value }));
  return (
    <div className="h-72 rounded-lg border border-line bg-white p-4 shadow-sm">
      {data.length ? (
        <ResponsiveContainer height="100%" width="100%">
          <PieChart>
            <Pie data={data} dataKey="value" innerRadius={58} outerRadius={92} paddingAngle={3}>
              {data.map((entry, index) => (
                <Cell fill={colors[index % colors.length]} key={entry.name} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      ) : (
        <div className="flex h-full items-center justify-center text-sm text-graphite">
          No failure counts available.
        </div>
      )}
    </div>
  );
}
