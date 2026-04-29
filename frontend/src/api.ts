import type {
  CorrelationPair,
  DayOfWeekPoint,
  Habit,
  HeatmapResponse,
  WeeklyInsight,
} from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(path, {
    headers: { "content-type": "application/json" },
    ...init,
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`${resp.status} ${resp.statusText}: ${text}`);
  }
  if (resp.status === 204) return undefined as T;
  return (await resp.json()) as T;
}

export const api = {
  listHabits: () => request<Habit[]>("/api/habits"),
  createHabit: (name: string, color: string) =>
    request<Habit>("/api/habits", {
      method: "POST",
      body: JSON.stringify({ name, color }),
    }),
  deleteHabit: (id: number) =>
    request<void>(`/api/habits/${id}`, { method: "DELETE" }),
  toggleCompletion: (habitId: number, day: string, completed: boolean) =>
    request<{ completed: boolean }>(
      `/api/habits/${habitId}/completions/${day}`,
      { method: "PUT", body: JSON.stringify({ completed }) },
    ),
  heatmap: (habitId: number) =>
    request<HeatmapResponse>(`/api/analytics/heatmap/${habitId}`),
  dayOfWeek: () => request<DayOfWeekPoint[]>("/api/analytics/day-of-week"),
  correlations: () => request<CorrelationPair[]>("/api/analytics/correlations"),
  weeklyInsight: () => request<WeeklyInsight>("/api/analytics/weekly-insight"),
};
