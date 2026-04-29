import { useCallback, useEffect, useMemo, useState } from "react";

import { api } from "../api";
import { CorrelationsCard } from "../components/CorrelationsCard";
import { DayOfWeekChart } from "../components/DayOfWeekChart";
import { HabitList } from "../components/HabitList";
import { Heatmap } from "../components/Heatmap";
import { WeeklyInsightCard } from "../components/WeeklyInsightCard";
import type {
  CorrelationPair,
  DayOfWeekPoint,
  Habit,
  HeatmapResponse,
  WeeklyInsight,
} from "../types";

function todayIso(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export function Dashboard() {
  const [habits, setHabits] = useState<Habit[]>([]);
  const [heatmaps, setHeatmaps] = useState<HeatmapResponse[]>([]);
  const [dow, setDow] = useState<DayOfWeekPoint[]>([]);
  const [pairs, setPairs] = useState<CorrelationPair[]>([]);
  const [insight, setInsight] = useState<WeeklyInsight | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const today = useMemo(() => todayIso(), []);
  const todayCompletions = useMemo(() => {
    const map: Record<number, boolean> = {};
    for (const hm of heatmaps) {
      const last = hm.cells[hm.cells.length - 1];
      if (last) map[hm.habit_id] = last.completed;
    }
    return map;
  }, [heatmaps]);

  const refresh = useCallback(async () => {
    setError(null);
    try {
      const list = await api.listHabits();
      setHabits(list);
      const [maps, dowData, pairsData, insightData] = await Promise.all([
        Promise.all(list.map((h) => api.heatmap(h.id))),
        api.dayOfWeek(),
        api.correlations(),
        api.weeklyInsight(),
      ]);
      setHeatmaps(maps);
      setDow(dowData);
      setPairs(pairsData);
      setInsight(insightData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const handleToggle = useCallback(
    async (habitId: number, completed: boolean) => {
      await api.toggleCompletion(habitId, today, completed);
      await refresh();
    },
    [today, refresh],
  );

  const handleCreate = useCallback(
    async (name: string, color: string) => {
      await api.createHabit(name, color);
      await refresh();
    },
    [refresh],
  );

  const handleDelete = useCallback(
    async (id: number) => {
      await api.deleteHabit(id);
      await refresh();
    },
    [refresh],
  );

  return (
    <div className="app">
      <h1>Habit Tracker</h1>
      <div className="subtitle">
        Track daily habits and discover patterns across {habits.length} habit
        {habits.length === 1 ? "" : "s"}.
      </div>

      {error && <div className="error" style={{ marginBottom: 12 }}>{error}</div>}
      {loading && <div className="empty" style={{ marginBottom: 12 }}>Loading…</div>}

      <div className="grid">
        <div className="panel col-4">
          <h2>Today · {today}</h2>
          <HabitList
            habits={habits}
            todayCompletions={todayCompletions}
            todayIso={today}
            onToggle={handleToggle}
            onCreate={handleCreate}
            onDelete={handleDelete}
          />
        </div>

        <div className="panel col-8">
          <h2>Day-of-week consistency</h2>
          <DayOfWeekChart data={dow} />
        </div>

        <div className="panel col-12">
          <h2>365-day heatmaps</h2>
          {heatmaps.length === 0 ? (
            <p className="empty">Add habits to see heatmaps.</p>
          ) : (
            heatmaps.map((hm) => (
              <div key={hm.habit_id} style={{ marginBottom: 16 }}>
                <Heatmap data={hm} />
              </div>
            ))
          )}
        </div>

        <div className="panel col-6">
          <h2>Top correlations</h2>
          <CorrelationsCard pairs={pairs} />
        </div>

        <div className="panel col-6">
          <h2>Weekly AI insight</h2>
          {insight ? (
            <WeeklyInsightCard data={insight} />
          ) : (
            <p className="empty">Loading…</p>
          )}
        </div>
      </div>
    </div>
  );
}
