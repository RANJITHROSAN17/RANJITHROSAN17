import { useEffect, useRef } from 'react';
import { HEATMAP_GRID } from '../../shared/game';

type Props = {
  grid: number[];
  anomaly: { x: number; y: number };
  playerTaps: { x: number; y: number }[];
  imageRef: string;
};

/**
 * Renders the puzzle image + crowd heatmap bloom + player taps.
 * Heatmap: 20×20 grid → radial glows (cyan→amber), anomaly ring, player stars.
 */
export const HeatmapCanvas = ({ grid, anomaly, playerTaps, imageRef }: Props) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const W = 640;
    const H = 640;
    canvas.width = W;
    canvas.height = H;

    const img = new Image();
    img.onload = () => {
      ctx.drawImage(img, 0, 0, W, H);
      // Heatmap bloom
      const max = Math.max(1, ...grid);
      for (let gy = 0; gy < HEATMAP_GRID; gy++) {
        for (let gx = 0; gx < HEATMAP_GRID; gx++) {
          const v = grid[gy * HEATMAP_GRID + gx] ?? 0;
          if (v === 0) continue;
          const cx = ((gx + 0.5) / HEATMAP_GRID) * W;
          const cy = ((gy + 0.5) / HEATMAP_GRID) * H;
          const r = 18 + (v / max) * 42;
          const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, r);
          g.addColorStop(0, 'rgba(34,211,238,0.55)');
          g.addColorStop(0.6, 'rgba(245,158,11,0.35)');
          g.addColorStop(1, 'rgba(245,158,11,0)');
          ctx.fillStyle = g;
          ctx.beginPath();
          ctx.arc(cx, cy, r, 0, Math.PI * 2);
          ctx.fill();
        }
      }
      // Anomaly ring
      const ax = anomaly.x * W;
      const ay = anomaly.y * H;
      ctx.strokeStyle = '#f59e0b';
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.arc(ax, ay, 26, 0, Math.PI * 2);
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(ax, ay, 6, 0, Math.PI * 2);
      ctx.fillStyle = '#f59e0b';
      ctx.fill();
      // Player taps
      ctx.fillStyle = '#ffffff';
      ctx.strokeStyle = '#0a0e14';
      ctx.lineWidth = 2;
      for (const t of playerTaps) {
        const px = t.x * W;
        const py = t.y * H;
        ctx.beginPath();
        ctx.arc(px, py, 10, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
      }
    };
    img.onerror = () => {
      ctx.fillStyle = '#111827';
      ctx.fillRect(0, 0, W, H);
      ctx.fillStyle = '#94a3b8';
      ctx.font = '20px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Image unavailable', W / 2, H / 2);
    };
    img.src = imageRef;
  }, [grid, anomaly, playerTaps, imageRef]);

  return (
    <canvas
      ref={canvasRef}
      className="result-bloom h-auto w-full rounded-xl border border-slate-700"
      aria-label="Crowd heatmap reveal"
    />
  );
};
