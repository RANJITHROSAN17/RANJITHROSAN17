import { Hono } from 'hono';
import { context, redis, reddit } from '@devvit/web/server';
import {
  bestOfTaps,
  dayNumber,
  gridIndex,
  HEATMAP_GRID,
  MAX_TAPS,
  percentileOf,
  scoreTap,
  type Tap,
} from '../../shared/game';
import type {
  DailyResponse,
  ErrorResponse,
  GuessRequest,
  GuessResponse,
  HeatmapResponse,
  LeaderboardResponse,
  ResultsResponse,
  StreakResponse,
} from '../../shared/api';
import { todayPuzzle } from '../core/puzzle';

export const api = new Hono();

const guessKey = (user: string, day: number) => `guess:${user}:${day}`;
const streakKey = (user: string) => `streak:${user}`;
const heatKey = (day: number) => `heatmap:${day}`;
const boardKey = (day: number) => `leaderboard:${day}`;

async function getTaps(user: string, day: number): Promise<Tap[]> {
  const raw = await redis.get(guessKey(user, day));
  if (!raw) return [];
  try {
    return JSON.parse(raw) as Tap[];
  } catch {
    return [];
  }
}

async function getStreak(user: string): Promise<{ streak: number; best: number; finds: number; plays: number }> {
  const raw = await redis.get(streakKey(user));
  if (!raw) return { streak: 0, best: 0, finds: 0, plays: 0 };
  try {
    return JSON.parse(raw) as { streak: number; best: number; finds: number; plays: number };
  } catch {
    return { streak: 0, best: 0, finds: 0, plays: 0 };
  }
}

/** GET /api/daily — today's puzzle (anomaly hidden until finished). */
api.get('/daily', async (c) => {
  try {
    const username = (await reddit.getCurrentUsername()) ?? '';
    if (!username) return c.json<ErrorResponse>({ status: 'error', message: 'Sign in to Reddit to play' }, 401);
    const day = dayNumber();
    const puzzle = todayPuzzle();
    const taps = await getTaps(username, day);
    const best = bestOfTaps(taps, puzzle);
    const s = await getStreak(username);
    const finished = taps.length >= MAX_TAPS;
    return c.json<DailyResponse>({
      type: 'daily',
      // Never leak the anomaly before the player finishes.
      puzzle: finished ? puzzle : { ...puzzle, anomaly: { x: 0.5, y: 0.5 }, reveal: '???' },
      attemptsUsed: taps.length,
      bestPoints: best?.points ?? 0,
      streak: s.streak,
      bestStreak: s.best,
      username,
      anomalyRevealed: finished,
    });
  } catch (e) {
    console.error('daily error', e);
    return c.json<ErrorResponse>({ status: 'error', message: 'Failed to load today\'s Lens' }, 500);
  }
});

/** POST /api/guess — submit one tap. Server scores it. */
api.post('/guess', async (c) => {
  let lockKey: string | undefined;
  try {
    const body = await c.req.json<GuessRequest>();
    const { x, y } = body;
    if (typeof x !== 'number' || typeof y !== 'number') return c.json<ErrorResponse>({ status: 'error', message: 'Coordinates must be numbers' }, 400);
    if (!Number.isFinite(x) || !Number.isFinite(y) || x < 0 || x > 1 || y < 0 || y > 1) {
      return c.json<ErrorResponse>({ status: 'error', message: 'x and y must be in 0..1' }, 400);
    }
    const username = (await reddit.getCurrentUsername()) ?? '';
    if (!username) return c.json<ErrorResponse>({ status: 'error', message: 'Sign in to Reddit to play' }, 401);
    const day = dayNumber();
    const puzzle = todayPuzzle();
    const key = `lock:${username}:${day}`;
    const acquired = await redis.set(key, 'busy', { nx: true, expiration: new Date(Date.now() + 30000) });
    if (acquired !== 'OK') return c.json<ErrorResponse>({ status: 'error', message: 'A tap is already being processed. Try again shortly.' }, 409);
    lockKey = key;
    const taps = await getTaps(username, day);
    if (taps.length >= MAX_TAPS) {
      return c.json<ErrorResponse>({ status: 'error', message: 'No attempts left today' }, 400);
    }
    const now = Date.now();
    const tap: Tap = { x, y, t: now };
    const next = [...taps, tap];
    await redis.set(guessKey(username, day), JSON.stringify(next), { expiration: new Date(Date.now() + 35 * 86400000) });

    // Heatmap: increment the cell.
    const idx = gridIndex(x, y);
    await redis.hIncrBy(heatKey(day), String(idx), 1);

    const scored = scoreTap(tap, puzzle);
    const finished = next.length >= MAX_TAPS;

    if (finished) {
      // Update streak + leaderboard + flair on finish.
      const best = bestOfTaps(next, puzzle);
      const s = await getStreak(username);
      const found = best?.found ?? false;
      const previousDay = Number(await redis.get(`last-play:${username}`));
      const streak = found ? (previousDay === day - 1 ? s.streak + 1 : 1) : 0;
      await redis.set(`last-play:${username}`, String(day));
      const bestStreak = Math.max(s.best, streak);
      await redis.set(
        streakKey(username),
        JSON.stringify({ streak, best: bestStreak, finds: s.finds + (found ? 1 : 0), plays: s.plays + 1 })
      );
      try {
        await redis.zAdd(boardKey(day), { member: username, score: best?.points ?? 0 });
      } catch {
        // zAdd may not exist in all Devvit envs — leaderboard is best-effort.
      }
      try {
        const flair = found ? 'Sharp Eye' : 'Missed it';
        await reddit.setUserFlair({ subredditName: context.subredditName, username, text: flair });
      } catch {
        // Flair is best-effort (needs mod perms in some subs).
      }
    }

    return c.json<GuessResponse>({
      type: 'guess',
      points: scored.points,
      distance: scored.distance,
      found: scored.found,
      bullseye: scored.bullseye,
      grade: scored.grade,
      attemptsUsed: next.length,
      attemptsLeft: MAX_TAPS - next.length,
      finished,
    });
  } catch (e) {
    console.error('guess error', e);
    return c.json<ErrorResponse>({ status: 'error', message: 'Failed to submit guess' }, 500);
  } finally {
    if (lockKey) await redis.del(lockKey);
  }
});

/** GET /api/results — reveal after finishing. */
api.get('/results', async (c) => {
  try {
    const username = (await reddit.getCurrentUsername()) ?? '';
    if (!username) return c.json<ErrorResponse>({ status: 'error', message: 'Sign in to Reddit to play' }, 401);
    const day = dayNumber();
    const puzzle = todayPuzzle();
    const taps = await getTaps(username, day);
    if (taps.length < MAX_TAPS) {
      return c.json<ErrorResponse>({ status: 'error', message: 'Finish your 3 taps to see results' }, 400);
    }
    const best = bestOfTaps(taps, puzzle);
    const s = await getStreak(username);
    const entries = await redis.zRange(boardKey(day), 0, -1, { by: 'rank' });
    const scores = entries.map(e => e.score);
    const totalPlayers = scores.length;
    const foundCount = scores.filter(v => v >= 600).length;
    const percentile = percentileOf(best?.points ?? 0, scores);
    return c.json<ResultsResponse>({
      type: 'results',
      puzzle,
      taps,
      bestPoints: best?.points ?? 0,
      percentile,
      totalPlayers,
      foundCount,
      streak: s.streak,
      bestStreak: s.best,
      flair: best?.found ? 'sharp-eye' : 'missed',
    });
  } catch (e) {
    console.error('results error', e);
    return c.json<ErrorResponse>({ status: 'error', message: 'Failed to load results' }, 500);
  }
});

/** GET /api/heatmap — crowd taps for the reveal bloom. */
api.get('/heatmap', async (c) => {
  try {
    const username = (await reddit.getCurrentUsername()) ?? '';
    if (!username) return c.json<ErrorResponse>({ status: 'error', message: 'Sign in to Reddit to play' }, 401);
    const day = dayNumber();
    const puzzle = todayPuzzle();
    const taps = await getTaps(username, day);
    if (taps.length < MAX_TAPS) return c.json<ErrorResponse>({ status: 'error', message: 'Finish your taps before revealing the heatmap' }, 403);
    const cells = await redis.hGetAll(heatKey(day));
    const grid = Array.from({ length: HEATMAP_GRID * HEATMAP_GRID }, (_, i) => Number(cells[String(i)] ?? 0));
    const totalTaps = grid.reduce((a, b) => a + b, 0);
    return c.json<HeatmapResponse>({ type: 'heatmap', grid, totalTaps, anomaly: puzzle.anomaly });
  } catch (e) {
    console.error('heatmap error', e);
    return c.json<ErrorResponse>({ status: 'error', message: 'Failed to load heatmap' }, 500);
  }
});

/** GET /api/streak */
api.get('/streak', async (c) => {
  try {
    const username = (await reddit.getCurrentUsername()) ?? '';
    const s = await getStreak(username);
    return c.json<StreakResponse>({ type: 'streak', streak: s.streak, bestStreak: s.best, totalFinds: s.finds, totalPlays: s.plays });
  } catch (e) {
    console.error('streak error', e);
    return c.json<ErrorResponse>({ status: 'error', message: 'Failed to load streak' }, 500);
  }
});

/** GET /api/leaderboard */
api.get('/leaderboard', async (c) => {
  try {
    const username = (await reddit.getCurrentUsername()) ?? '';
    if (!username) return c.json<ErrorResponse>({ status: 'error', message: 'Sign in to Reddit to play' }, 401);
    const day = dayNumber();
    const entries = await redis.zRange(boardKey(day), 0, 9, { by: 'rank', reverse: true });
    return c.json<LeaderboardResponse>({ type: 'leaderboard', entries: entries.map(e => ({ username: e.member, points: e.score })) });
  } catch (e) {
    console.error('leaderboard error', e);
    return c.json<ErrorResponse>({ status: 'error', message: 'Failed to load leaderboard' }, 500);
  }
});
