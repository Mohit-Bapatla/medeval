"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export function MetricBarChart({ data }: { data: { name: string; value: number }[] }) {
  return (
    <div className="h-72 rounded-lg border border-line bg-white p-4 shadow-sm">
      <ResponsiveContainer height="100%" width="100%">
        <BarChart data={data}>
          <CartesianGrid stroke="#d7dee5" strokeDasharray="3 3" />
          <XAxis dataKey="name" tick={{ fontSize: 12 }} />
          <YAxis domain={[0, 1]} tickFormatter={(value) => `${Math.round(value * 100)}%`} />
          <Tooltip formatter={(value) => `${Math.round(Number(value) * 100)}%`} />
          <Bar dataKey="value" fill="#0f766e" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
