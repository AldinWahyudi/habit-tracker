import { useState } from "react";

import type { Habit } from "../types";

interface Props {
  habits: Habit[];
  todayCompletions: Record<number, boolean>;
  todayIso: string;
  onToggle: (habitId: number, completed: boolean) => Promise<void>;
  onCreate: (name: string, color: string) => Promise<void>;
  onDelete: (habitId: number) => Promise<void>;
}

export function HabitList({
  habits,
  todayCompletions,
  todayIso,
  onToggle,
  onCreate,
  onDelete,
}: Props) {
  const [name, setName] = useState("");
  const [color, setColor] = useState("#22c55e");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await onCreate(name.trim(), color);
      setName("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create habit");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <form
        onSubmit={handleSubmit}
        style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}
      >
        <input
          type="text"
          placeholder="New habit name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          style={{ flex: 1, minWidth: 160 }}
        />
        <input type="color" value={color} onChange={(e) => setColor(e.target.value)} />
        <button type="submit" className="primary" disabled={busy}>
          Add habit
        </button>
      </form>
      {error && <div className="error" style={{ marginBottom: 12 }}>{error}</div>}
      {habits.length === 0 ? (
        <p className="empty">No habits yet — add one above.</p>
      ) : (
        habits.map((h) => {
          const done = !!todayCompletions[h.id];
          return (
            <div className="habit-row" key={h.id}>
              <div className="swatch" style={{ background: h.color }} />
              <div className="name">{h.name}</div>
              <button
                className={`toggle ${done ? "on" : ""}`}
                onClick={() => onToggle(h.id, !done)}
                title={`Toggle ${h.name} for ${todayIso}`}
              >
                {done ? "Done today" : "Mark done"}
              </button>
              <button
                className="danger"
                onClick={() => {
                  if (confirm(`Delete habit "${h.name}"? All completions will be removed.`)) {
                    void onDelete(h.id);
                  }
                }}
              >
                ×
              </button>
            </div>
          );
        })
      )}
    </div>
  );
}
