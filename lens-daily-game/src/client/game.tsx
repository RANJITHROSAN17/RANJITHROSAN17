import './index.css';
import { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import type { DailyResponse, GuessResponse, ResultsResponse, HeatmapResponse } from '../shared/api';
import { HeatmapCanvas } from './components/HeatmapCanvas';

async function api<T>(path: string, body?: object): Promise<T> {
  const r = await fetch(`/api/${path}`, body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : undefined);
  const data = await r.json();
  if (!r.ok) throw new Error(data.message ?? 'Request failed');
  return data;
}
export function App() {
  const [daily, setDaily] = useState<DailyResponse | null>(null);
  const [result, setResult] = useState<ResultsResponse | null>(null);
  const [heat, setHeat] = useState<HeatmapResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [feedback, setFeedback] = useState('Find the one broken pattern. Tap its centre.');
  const [seconds, setSeconds] = useState(60);
  async function reveal() {
    const [r, h] = await Promise.all([api<ResultsResponse>('results'), api<HeatmapResponse>('heatmap')]);
    setResult(r); setHeat(h);
  }
  useEffect(() => { void api<DailyResponse>('daily').then(async d => { setDaily(d); if (d.anomalyRevealed) await reveal(); }).catch(e => setError(String(e))); }, []);
  useEffect(() => {
    if (!daily || result) return;
    const timer = setInterval(() => setSeconds(n => Math.max(0, n - 1)), 1000);
    return () => clearInterval(timer);
  }, [daily, result]);
  async function guess(x: number, y: number) {
    if (busy || !daily || result) return;
    setBusy(true); setError('');
    try {
      const g = await api<GuessResponse>('guess', { x, y });
      setDaily({ ...daily, attemptsUsed: g.attemptsUsed });
      setFeedback(`${g.grade.toUpperCase()} · ${g.points} points · ${g.attemptsLeft} taps left`);
      if (g.finished) await reveal();
    } catch (e) { setError(String(e)); } finally { setBusy(false); }
  }
  return <main className="mx-auto max-w-xl space-y-5 px-5 py-6">
    <header className="flex items-center justify-between"><h1 className="text-xl font-bold tracking-[.25em] text-cyan-300">◎ LENS</h1><span className="text-xs text-slate-400">DAILY ANOMALY HUNT</span></header>
    <h2 className="text-2xl font-bold">{result ? 'Here’s where everyone looked.' : daily?.puzzle.label ?? 'Loading today’s Lens…'}</h2>
    {error && <p role="alert" className="rounded bg-red-950 p-3 text-red-200">{error} <button onClick={() => { void api<DailyResponse>('daily').then(setDaily).catch(e => setError(String(e))); }}>Retry</button></p>}
    {daily && !result && <>
      <div className="flex justify-between text-sm text-slate-300"><span className="capitalize">{daily.puzzle.pack} · {daily.puzzle.difficulty}/10</span><span>{3 - daily.attemptsUsed} taps · {seconds}s {seconds === 0 && '(practice time)'}</span></div>
      <button disabled={busy} aria-label="Puzzle image: tap the anomaly" className="block w-full overflow-hidden rounded-xl border border-slate-700 disabled:opacity-70" onClick={e => { const rect = e.currentTarget.getBoundingClientRect(); void guess((e.clientX - rect.left) / rect.width, (e.clientY - rect.top) / rect.height); }}>
        <img src={daily.puzzle.imageRef} alt="Find the one shape that breaks the pattern" className="aspect-square w-full" draggable={false}/>
      </button>
      <p aria-live="polite" className="text-center text-cyan-200">{busy ? 'Checking your tap…' : feedback}</p>
      <p className="text-xs text-slate-400">60 seconds is a challenge target in this prototype, not a hard limit. Use all three taps to reveal the crowd.</p>
    </>}
    {result && heat && <section className="space-y-4">
      <HeatmapCanvas grid={heat.grid} anomaly={result.puzzle.anomaly} playerTaps={result.taps} imageRef={result.puzzle.imageRef}/>
      <p className="text-sm text-slate-300">Amber ring: anomaly · White dots: your taps · Glow: crowd</p>
      <h3 className="text-xl font-semibold">{result.puzzle.reveal}</h3>
      <div className="grid grid-cols-3 gap-3 text-center">{[[result.bestPoints, 'POINTS'], [result.streak, 'STREAK'], [result.totalPlayers, 'PLAYERS']].map(([v,l]) => <div key={l} className="rounded-xl bg-slate-900 p-4"><strong className="block text-2xl text-cyan-300">{v}</strong><small>{l}</small></div>)}</div>
      <button className="rounded-full bg-cyan-300 px-5 py-3 font-bold text-slate-950" onClick={() => { void navigator.clipboard.writeText(`◎ ${result.puzzle.label}\n${result.bestPoints}/1000 · ${result.streak} day streak\nOne image. One anomaly. #LENS`).then(() => setFeedback('Copied!')).catch(() => setFeedback('Clipboard unavailable.')); }}>Copy spoiler-free score</button>
      <p aria-live="polite" className="text-sm text-slate-400">{feedback}</p><p>Come back tomorrow for a new Lens.</p>
    </section>}
  </main>;
}
createRoot(document.getElementById('root')!).render(<App/>);
