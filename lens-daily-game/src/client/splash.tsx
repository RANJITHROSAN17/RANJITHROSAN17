import './index.css';

import { context, requestExpandedMode } from '@devvit/web/client';
import { StrictMode, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import type { DailyResponse } from '../shared/api';

export const Splash = () => {
  const [data, setData] = useState<DailyResponse | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetch('/api/daily')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((d: DailyResponse) => setData(d))
      .catch(() => setError(true));
  }, []);

  const finished = data ? data.attemptsUsed >= 3 : false;

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-[#0a0e14] px-4 py-6 text-[#f8fafc]">
      <div className="flex items-center gap-2">
        <span className="inline-flex h-8 w-8 items-center justify-center rounded-full border-2 border-[#22d3ee] text-sm font-bold text-[#22d3ee]">
          ◎
        </span>
        <span className="text-sm font-semibold tracking-[0.2em] text-[#22d3ee]">LENS</span>
        <span className="text-xs text-slate-400">The Daily Anomaly Hunt</span>
      </div>

      <h1 className="max-w-md text-center text-2xl font-bold leading-tight">
        {data ? data.puzzle.label : 'One image. One anomaly.'}
      </h1>
      <p className="max-w-md text-center text-sm text-slate-300">
        {error
          ? 'Could not load today\'s Lens. Check your connection and try again.'
          : finished
            ? 'You played today. See where the crowd looked.'
            : 'Something\'s off. Tap Play and spot it in 60 seconds.'}
      </p>

      {data && (
        <div className="flex items-center gap-3 text-xs text-slate-300">
          <span className="rounded-full bg-[#111827] px-3 py-1 capitalize">{data.puzzle.pack} pack</span>
          <span className="rounded-full bg-[#111827] px-3 py-1 font-mono-num">
            Difficulty {data.puzzle.difficulty}/10
          </span>
          <span className="rounded-full bg-[#111827] px-3 py-1 font-mono-num">🔥 Streak {data.streak}</span>
        </div>
      )}

      <button
        className="mt-2 inline-flex h-12 items-center justify-center rounded-full bg-[#22d3ee] px-8 text-base font-bold text-[#0a0e14] transition hover:bg-[#67e8f9] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#22d3ee]"
        onClick={(e) => requestExpandedMode(e.nativeEvent, 'game')}
      >
        {finished ? 'See results' : '▶ Play today\'s Lens'}
      </button>

      <p className="text-center text-xs text-slate-500">
        Hey {context.username ?? 'detective'} — 3 taps. Everyone plays the same image today.
      </p>
    </div>
  );
};

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Splash />
  </StrictMode>
);
