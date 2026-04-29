export interface Habit {
  id: number;
  name: string;
  color: string;
  created_at: string;
}

export interface HeatmapCell {
  date: string;
  completed: boolean;
  intensity: number;
}

export interface HeatmapResponse {
  habit_id: number;
  habit_name: string;
  color: string;
  start_date: string;
  end_date: string;
  cells: HeatmapCell[];
  completion_rate: number;
}

export interface DayOfWeekPoint {
  weekday: number;
  name: string;
  rate: number;
}

export interface CorrelationPair {
  habit_a_id: number;
  habit_a_name: string;
  habit_b_id: number;
  habit_b_name: string;
  correlation: number;
  days_compared: number;
  explanation: string;
}

export interface WeeklyInsight {
  bullets: string[];
  source: "claude" | "heuristic";
  week_start: string;
  week_end: string;
}
