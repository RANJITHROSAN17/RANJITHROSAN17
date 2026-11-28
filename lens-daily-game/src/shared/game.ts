/**
 * LENS — The Daily Anomaly Hunt
 * Shared game logic: seeded daily puzzles, scoring, difficulty.
 * Pure functions only — safe to import from client and server.
 */

export type PackId = 'space' | 'lab' | 'safety' | 'terrain' | 'mixed';

export type Puzzle = {
  /** Stable id, e.g. "2026-11-28" or "bank-042" */
  id: string;
  /** Day number since epoch (UTC) */
  day: number;
  /** Human label, e.g. "LENS #42" */
  label: string;
  /** Theme pack */
  pack: PackId;
  /** Image reference — URL or bundled asset path */
  imageRef: string;
  /** True anomaly centre, 0..1 (x from left, y from top) */
  anomaly: { x: number; y: number };
  /** Anomaly radius in 0..1 units (for bullseye) */
  radius: number;
  /** 1 (easy) .. 10 (expert) */
  difficulty: number;
  /** Short reveal text, e.g. "A missing crater" */
  reveal: string;
  /** How the anomaly was injected */
  method: 'copy-paste' | 'color-shift' | 'rotation' | 'removal' | 'camouflage';
};

export type Tap = { x: number; y: number; t: number };

export type ScoreResult = {
  points: number;
  distance: number; // 0..1 (Euclidean, image-diagonal normalised)
  found: boolean;
  bullseye: boolean;
  grade: 'bullseye' | 'found' | 'near' | 'missed';
};

/** Mulberry32 PRNG — deterministic from a seed. */
export function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** UTC day number (days since 1970-01-01). All players share this boundary. */
export function dayNumber(now: Date = new Date()): number {
  return Math.floor(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()) / 86400000);
}

export function dayLabel(day: number): string {
  const d = new Date(day * 86400000);
  return `LENS #${day.toString().slice(-3)} · ${d.toISOString().slice(0, 10)}`;
}

/** Weekday (0=Sun..6=Sat) for a UTC day number. */
export function weekdayOf(day: number): number {
  return new Date(day * 86400000).getUTCDay();
}

/**
 * Calibrated difficulty by weekday:
 * Mon–Tue warm-up (1–3), Wed–Thu standard (4–6), Fri–Sun expert (7–10).
 */
export function difficultyForDay(day: number, rand: () => number): number {
  const wd = weekdayOf(day);
  if (wd === 1 || wd === 2) return 1 + Math.floor(rand() * 3); // 1–3
  if (wd === 3 || wd === 4) return 4 + Math.floor(rand() * 3); // 4–6
  return 7 + Math.floor(rand() * 4); // 7–10
}

/** Score a tap against the true anomaly. Distance is diagonal-normalised. */
export function scoreTap(tap: { x: number; y: number }, puzzle: Puzzle): ScoreResult {
  const dx = tap.x - puzzle.anomaly.x;
  const dy = tap.y - puzzle.anomaly.y;
  const distance = Math.sqrt(dx * dx + dy * dy) / Math.SQRT2;
  const bullseye = distance <= puzzle.radius;
  const found = distance <= 0.12;
  const near = distance <= 0.25;
  let points: number;
  if (bullseye) points = 1000;
  else if (found) points = Math.round(600 + (0.12 - distance) * 3000);
  else if (near) points = Math.round(200 + (0.25 - distance) * 1600);
  else points = Math.max(0, Math.round(100 - distance * 200));
  const grade: ScoreResult['grade'] = bullseye ? 'bullseye' : found ? 'found' : near ? 'near' : 'missed';
  return { points, distance, found, bullseye, grade };
}

/** Best score across up to 3 taps. */
export function bestOfTaps(taps: Tap[], puzzle: Puzzle): ScoreResult | null {
  if (taps.length === 0) return null;
  let best: ScoreResult | null = null;
  for (const t of taps) {
    const s = scoreTap(t, puzzle);
    if (!best || s.points > best.points) best = s;
  }
  return best;
}

/** Percentile helper: share of crowd scores below yours (0..100). */
export function percentileOf(score: number, crowd: number[]): number {
  if (crowd.length === 0) return 50;
  const below = crowd.filter((s) => s < score).length;
  return Math.round((below / crowd.length) * 100);
}

export const MAX_TAPS = 3;
export const GAME_SECONDS = 60;
export const HEATMAP_GRID = 20; // 20×20 = 400 cells

/** Grid cell index (0..399) for a tap. */
export function gridIndex(x: number, y: number): number {
  const gx = Math.min(HEATMAP_GRID - 1, Math.max(0, Math.floor(x * HEATMAP_GRID)));
  const gy = Math.min(HEATMAP_GRID - 1, Math.max(0, Math.floor(y * HEATMAP_GRID)));
  return gy * HEATMAP_GRID + gx;
}

/** Fallback puzzle used when the bank is empty (dev / first run). */
export function fallbackPuzzle(day: number): Puzzle {
  const rand = mulberry32(day * 2654435761);
  return {
    id: `fallback-${day}`,
    day,
    label: dayLabel(day),
    pack: 'mixed',
    imageRef: '/puzzles/fallback.svg',
    anomaly: { x: 0.3 + rand() * 0.4, y: 0.3 + rand() * 0.4 },
    radius: 0.05,
    difficulty: difficultyForDay(day, rand),
    reveal: 'The odd one out',
    method: 'copy-paste',
  };
}
