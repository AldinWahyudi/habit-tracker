import type { HeatmapResponse } from "../types";

interface Props {
  data: HeatmapResponse;
}

const CELL = 11;
const GAP = 2;

function intensityColor(level: number, base: string): string {
  if (level <= 0) return "#1c2742";
  // Mix base color with dark background by alpha-style scaling.
  const alpha = 0.25 + level * 0.18;
  return blend(base, "#0b1220", alpha);
}

function blend(hex: string, bg: string, alpha: number): string {
  const a = parseHex(hex);
  const b = parseHex(bg);
  const r = Math.round(a[0] * alpha + b[0] * (1 - alpha));
  const g = Math.round(a[1] * alpha + b[1] * (1 - alpha));
  const bl = Math.round(a[2] * alpha + b[2] * (1 - alpha));
  return `rgb(${r},${g},${bl})`;
}

function parseHex(hex: string): [number, number, number] {
  const h = hex.replace("#", "");
  return [
    parseInt(h.substring(0, 2), 16),
    parseInt(h.substring(2, 4), 16),
    parseInt(h.substring(4, 6), 16),
  ];
}

const MONTH_LABELS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

export function Heatmap({ data }: Props) {
  const cells = data.cells;
  if (cells.length === 0) return null;

  // Align grid so the first column starts at the appropriate weekday offset.
  const first = new Date(cells[0].date + "T00:00:00");
  const startWeekday = (first.getDay() + 6) % 7; // 0=Mon..6=Sun

  const totalDays = cells.length;
  const columns = Math.ceil((startWeekday + totalDays) / 7);
  const width = columns * (CELL + GAP) + 30;
  const height = 7 * (CELL + GAP) + 24;

  const monthMarkers: { col: number; label: string }[] = [];
  let lastMonth = -1;
  cells.forEach((c, idx) => {
    const d = new Date(c.date + "T00:00:00");
    const m = d.getMonth();
    if (m !== lastMonth) {
      const col = Math.floor((idx + startWeekday) / 7);
      monthMarkers.push({ col, label: MONTH_LABELS[m] });
      lastMonth = m;
    }
  });

  return (
    <div className="heatmap">
      <div className="header">
        <strong style={{ color: data.color }}>{data.habit_name}</strong>
        <span className="rate">{Math.round(data.completion_rate * 100)}% over 365 days</span>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${data.habit_name} heatmap`}>
        {monthMarkers.map((m, i) => {
          const next = monthMarkers[i + 1];
          if (next && next.col - m.col < 2) return null;
          return (
            <text
              key={i}
              x={30 + m.col * (CELL + GAP)}
              y={10}
              fontSize={9}
              fill="#9aa6c2"
            >
              {m.label}
            </text>
          );
        })}
        {["Mon", "Wed", "Fri"].map((label, i) => (
          <text
            key={label}
            x={0}
            y={24 + i * 2 * (CELL + GAP) + CELL - 2}
            fontSize={9}
            fill="#9aa6c2"
          >
            {label}
          </text>
        ))}
        {cells.map((cell, idx) => {
          const pos = idx + startWeekday;
          const col = Math.floor(pos / 7);
          const row = pos % 7;
          const fill = intensityColor(cell.intensity, data.color);
          return (
            <rect
              key={cell.date}
              x={30 + col * (CELL + GAP)}
              y={24 + row * (CELL + GAP)}
              width={CELL}
              height={CELL}
              rx={2}
              ry={2}
              fill={fill}
            >
              <title>
                {cell.date} — {cell.completed ? `Completed (level ${cell.intensity})` : "Not completed"}
              </title>
            </rect>
          );
        })}
      </svg>
      <div className="legend">
        <span>Less</span>
        <div className="swatches">
          {[0, 1, 2, 3, 4].map((lvl) => (
            <div key={lvl} style={{ background: intensityColor(lvl, data.color) }} />
          ))}
        </div>
        <span>More</span>
      </div>
    </div>
  );
}
