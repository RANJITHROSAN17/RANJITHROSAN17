import { dayNumber, fallbackPuzzle, mulberry32, type Puzzle } from '../../shared/game';
import bank from '../../shared/puzzle-bank.json';

/**
 * Resolve today's puzzle.
 * Prefers the generated bank (matched by day offset), falls back to a
 * deterministic procedural puzzle so the game never breaks on day 1.
 */
export function puzzleForDay(day: number): Puzzle {
  const puzzles = (bank as { puzzles: Puzzle[] }).puzzles;
  if (puzzles.length > 0) {
    // Bank entries carry a `day` offset; map real day -> bank slot.
    const slot = ((day % puzzles.length) + puzzles.length) % puzzles.length;
    const base = puzzles[slot];
    if (base) {
      return { ...base, day, label: `LENS #${String(day).slice(-3)}` };
    }
  }
  return fallbackPuzzle(day);
}

export function todayPuzzle(): Puzzle {
  return puzzleForDay(dayNumber());
}

/** Deterministic jitter so repeated calls are stable within a day. */
export function stableRand(day: number): () => number {
  return mulberry32(day * 2654435761);
}
