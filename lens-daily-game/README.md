# ◎ LENS — The Daily Anomaly Hunt

One image. One anomaly. Three taps. A community reveal.

## Status: initial MVP, not a hackathon-ready release

This isolated Devvit Web project lives in the profile repository because Arena tracks this session's branch here. Creating `RANJITHROSAN17/lens-daily-game` was attempted but GitHub's integration denied repository creation. No separate repository or Reddit app has been created, uploaded, or published.

### Implemented

- React inline splash and expanded mobile-friendly puzzle view.
- 28 deterministic, original SVG puzzles: spot the sideways instrument needle.
- UTC-date selection, three server-scored guesses, server-side coordinate validation.
- Anonymous writes rejected. Results and heatmap require completing all taps.
- Redis per-user short-lived guess lease, atomic crowd-cell increments, sorted-set scores.
- Consecutive UTC-day streak calculation and best-effort user flair.
- Canvas crowd heatmap, answer ring, player markers, spoiler-free clipboard score.
- Moderator post action, install trigger, and daily cron configuration.
- Offline standard-library Python generator; no downloaded imagery or AI assets.

**Prototype limits:** The 60-second timer is a UI challenge target, not enforced on the server. Puzzle themes are palettes, not photographic scenes. The bank repeats after 28 days; generating 365 geometric layouts does not create 365 distinct mechanics. Difficulty values are heuristic, not playtest-calibrated. Archive, payments, analytics, OpenCV/photo generation, and B2B functionality are not implemented. The original strategy is an aspiration, not a claim of feature completion or guaranteed novelty/revenue.

## Local checks

Requires Node 22.18+ (Node 24 recommended), npm, Python 3. No Python packages required.

```sh
cd lens-daily-game
npm ci
npm run test:types
npm run test:unit
npm run lint
npm run build
```

Generate a larger bank (writes SVGs and the **server-imported** answer bank):

```sh
npm run generate   # 365 puzzles
# or: python3 tools/generate_puzzles.py --count 28
```

## Reddit setup / playtest

1. Register a Devvit app in your Reddit developer account. `lens-daily-game` in `devvit.json` is a proposed app name, not a registered identity; replace it with the actual available name.
2. Run `npm run login` interactively.
3. Create a small test subreddit you moderate and run `npm run dev` to select a playtest subreddit.
4. Exercise install/moderator post creation, three-tap persistence across reloads, simultaneous tabs, flair permissions, cron, and the reveal.
5. `npm run deploy` runs types and lint then **uploads**, not publishes. Do not publish without checking the actual hackathon rules.

No Reddit-hosted integration or browser end-to-end playtest has been performed in this environment. A plain Vite preview is not a substitute: the backend depends on Reddit context and Redis.

## Structure

- `src/client/`: splash, game, Canvas reveal.
- `src/server/`: Hono routes, daily puzzle selection, Reddit post creation.
- `src/shared/game.ts`: pure scoring, UTC date, grid and PRNG helpers.
- `src/shared/puzzle-bank.json`: answer metadata, imported only by the server.
- `public/puzzles/`: generated images; these are intentionally public, like any visual puzzle.
- `tools/generate_puzzles.py`: reproducible content pipeline.

## Remaining hardening before launch

- The guess lease prevents ordinary simultaneous submissions, but multi-key writes are not transactional. A crash between tap persistence and streak/leaderboard updates can leave partial state; implement idempotent finalization/reconciliation and token-owned leases before production.
- Add server-enforced start/deadline and replay-safe request IDs; expire old heatmap/leaderboard data and use stable user IDs for persisted identity.
- Pin puzzles to post dates (current MVP always selects **today**, including older posts), idempotent daily post creation, and post-scoped isolation as needed.
- Add route integration/concurrency tests with a Redis adapter and real-device playtesting; add explicit keyboard coordinate selection for the puzzle.
- Improve shape variety, difficulty calibration, and photo anomaly quality. Do not claim an unverified competitive scan proves uniqueness.
- `npm audit --omit=dev` currently reports 6 findings (2 high) in the Devvit CLI dependency tree, including `isomorphic-git` and `tmp`. Review with the Devvit SDK maintainers before deployment; do not force an untested major CLI upgrade. No app HTTP/file-upload path calls these CLI packages.

Original template: reddit/devvit-template-react, BSD-3-Clause (see LICENSE).
