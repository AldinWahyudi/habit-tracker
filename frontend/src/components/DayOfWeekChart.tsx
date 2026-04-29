import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { DayOfWeekPoint } from "../types";

interface Props {
  data: DayOfWeekPoint[];
}

export function DayOfWeekChart({ data }: Props) {
  const chartData = data.map((p) => ({ ...p, percent: Math.round(p.rate * 100) }));
  return (
    <div style={{ width: "100%", height: 240 }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid stroke="#243153" vertical={false} />
          <XAxis dataKey="name" stroke="#9aa6c2" tickLine={false} axisLine={false} />
          <YAxis
            stroke="#9aa6c2"
            tickLine={false}
            axisLine={false}
            domain={[0, 100]}
            tickFormatter={(v) => `${v}%`}
          />
          <Tooltip
            contentStyle={{
              background: "#1a2540",
              border: "1px solid #243153",
              borderRadius: 8,
              color: "#e6ecff",
            }}
            formatter={(value: number) => [`${value}%`, "Completion"]}
          />
          <Bar dataKey="percent" fill="#22c55e" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
