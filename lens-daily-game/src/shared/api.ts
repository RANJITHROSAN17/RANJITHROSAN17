/**
 * LENS API contract (client ↔ server).
 * Server is the source of truth — clients never send "I won".
 */
import type { Puzzle, Tap } from './game';

export type DailyResponse = {
  type: 'daily';
  puzzle: Puzzle;
  /** Attempts already used today (0..3) */
  attemptsUsed: number;
  /** Best points so far today (0 if none) */
  bestPoints: number;
  /** Current streak */
  streak: number;
  /** Best streak */
  bestStreak: number;
  username: string;
  /** True anomaly is hidden until the player finishes */
  anomalyRevealed: boolean;
};

export type GuessRequest = {
  x: number; // 0..1
  y: number; // 0..1
};

export type GuessResponse = {
  type: 'guess';
  /** Points for this tap (server-computed) */
  points: number;
  distance: number;
  found: boolean;
  bullseye: boolean;
  grade: 'bullseye' | 'found' | 'near' | 'missed';
  attemptsUsed: number;
  attemptsLeft: number;
  /** True once all 3 taps are used */
  finished: boolean;
};

export type ResultsResponse = {
  type: 'results';
  puzzle: Puzzle;
  taps: Tap[];
  bestPoints: number;
  percentile: number;
  totalPlayers: number;
  foundCount: number;
  streak: number;
  bestStreak: number;
  flair: 'sharp-eye' | 'missed' | null;
};

export type HeatmapResponse = {
  type: 'heatmap';
  /** 400 ints, row-major */
  grid: number[];
  totalTaps: number;
  anomaly: { x: number; y: number };
};

export type StreakResponse = {
  type: 'streak';
  streak: number;
  bestStreak: number;
  totalFinds: number;
  totalPlays: number;
};

export type LeaderboardResponse = {
  type: 'leaderboard';
  entries: { username: string; points: number }[];
};

export type ErrorResponse = {
  status: 'error';
  message: string;
};
