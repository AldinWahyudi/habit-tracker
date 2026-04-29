import type { CorrelationPair } from "../types";

interface Props {
  pairs: CorrelationPair[];
}

export function CorrelationsCard({ pairs }: Props) {
  if (pairs.length === 0) {
    return (
      <p className="empty">
        Add at least two habits with varying daily completion to see correlations.
      </p>
    );
  }
  return (
    <div>
      {pairs.map((p) => (
        <div className="correlation-pair" key={`${p.habit_a_id}-${p.habit_b_id}`}>
          <div className="pair">
            {p.habit_a_name} <span style={{ color: "#9aa6c2" }}>×</span> {p.habit_b_name}{" "}
            <span style={{ color: "#9aa6c2", fontWeight: 400 }}>
              (r = {p.correlation.toFixed(2)}, n = {p.days_compared})
            </span>
          </div>
          <div className="explain">{p.explanation}</div>
        </div>
      ))}
    </div>
  );
}
