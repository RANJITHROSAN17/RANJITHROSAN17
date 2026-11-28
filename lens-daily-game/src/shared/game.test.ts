import { test } from 'node:test';
import assert from 'node:assert/strict';
import { dayNumber, gridIndex, scoreTap, bestOfTaps, mulberry32, fallbackPuzzle, difficultyForDay } from './game.ts';

test('UTC day boundary is shared across offsets', () => {
  assert.equal(dayNumber(new Date('2026-11-28T01:00:00Z')), dayNumber(new Date('2026-11-28T09:00:00+08:00')));
  assert.equal(dayNumber(new Date('2026-11-29T00:00:00Z')) - dayNumber(new Date('2026-11-28T23:59:59Z')), 1);
});
test('exact centre is a bullseye and far taps miss', () => {
  const p = fallbackPuzzle(100);
  assert.equal(scoreTap(p.anomaly, p).points, 1000);
  assert.equal(scoreTap({x: -1, y: -1}, p).found, false);
  assert.equal(bestOfTaps([], p), null);
  assert.equal(bestOfTaps([{...p.anomaly, t: 0}], p)?.points, 1000);
});
test('grid clips boundaries to 20 by 20', () => {
  assert.equal(gridIndex(0, 0), 0);
  assert.equal(gridIndex(1, 1), 399);
  assert.equal(gridIndex(-1, -1), 0);
});
test('seeded generator and difficulty are stable and bounded', () => {
  const a = mulberry32(42), b = mulberry32(42);
  for (let i = 0; i < 100; i++) assert.equal(a(), b());
  for (let day = 20000; day < 20400; day++) {
    const d = difficultyForDay(day, mulberry32(day));
    assert.ok(d >= 1 && d <= 10);
  }
});
