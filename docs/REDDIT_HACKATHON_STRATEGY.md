# Reddit Game of the Day — Winning Strategy for Ranjith Rosan
**Hackathon:** Reddit's Game of the Day (Nov 11 – Dec 8, 2026) · **Prize pool:** $35,000 · **Deadline:** Dec 8, 6pm PT (Dec 9, 7:30am IST) · **You have:** ~10 days

> **One-line verdict:** Don't build another Wordle, GeoGuessr, or space shooter. Build **LENS — The Daily Anomaly Hunt**: one image, one hidden anomaly, 60 seconds, and a collective heatmap that turns every player into a forensic detective. It plays directly to your computer-vision unfair advantage, hits all four judging criteria, and has three stacked revenue engines.

---

## 1. Hackathon Decoded — What Judges Actually Score

You pasted the full rules. Here's the translation:

| What they say | What it means for you |
|---|---|
| **Devvit Web + Interactive Posts only** | Your game must run *inside* a Reddit post (feed preview → expanded game). Not a standalone website. Use React/three.js — you're already fluent. |
| **$35,000: Best Daily Game $15k, Best Ported $6k, 10× Honorable Mention $1k** | One prize per project. Ported category needs you to own the original IP — you don't have one for this, so **aim for Best Daily Game**. |
| **3,191 participants** | You are not competing on code volume. You win on *distinctiveness + polish in the demo post*. Judges score from your demo link — make it self-explanatory in 10 seconds. |
| **Do NOT publish the app** | Upload + playtest only. App Review is for launch-ready apps. Keep it private, install in a small public test sub (<200 members). |
| **Submit:** app listing link + demo post link + README + optional <1min video | The demo post *is* your submission. Everything else is supporting evidence. |
| **Bonus prizes:** Devvit Helper $500×6, Feedback $200×5 | Answer questions in r/Devvit + Discord daily (Helper). Fill the developer survey with actionable feedback (Feedback). Free money. |

### The 4 judging criteria (equally weighted)

1. **Delightful UX** — exciting layout/theme, easy + fun to discover. No wall-of-text instructions.
2. **Polish** — close to publishable, Devvit Rules compliant, understandable from example posts alone.
3. **Reddit-y** — community-minded, own identity, brings people together. *Not* "about Reddit/karma/Snoo" — it's about community intelligence, discussion, flair, comments.
4. **Daily Content** — recurring challenges, fresh content, calibrated difficulty.

### The 4 traps (instant score killers)

1. **AI slop** — generic UI, doesn't fit viewport, no unique identity. Fix: hand-tuned animations, bespoke visual identity, human-feeling copy.
2. **On-the-nose Reddit theming** — game *about* Reddit. Fix: game about *human perception* that happens to use Reddit features natively.
3. **Common ideas** — space shooters, Wordle clones, trivia, simple platformers, collaborative storytelling. Fix: new genre (see §3).
4. **Not on Reddit** — standalone web game. Fix: Devvit Web from Day 1, test in a real sub.

---

## 2. Your Unfair Advantage (Why You, Specifically, Can Win This)

Most of the 3,191 entrants will build a word game or a Phaser shooter. You have a stack almost nobody else in this hackathon has:

| Your asset | How it maps to a winning daily game |
|---|---|
| **Computer Vision Intern @ SeeWise.AI** (PPE/people/machinery detection) | You *think* in anomalies, saliency, and detection. A daily anomaly-hunt game is your home turf. |
| **Grounding DINO Auto-Labelling, YOLOv3, CardioLens 3D** | You can *generate* puzzles programmatically (inject anomalies, score difficulty with SSIM/saliency) — infinite daily content without hand-crafting 365 puzzles. |
| **React + three.js + Vite** (CardioLens) | Devvit Web's React template + canvas/three.js rendering is exactly your stack. Smooth heatmap bloom, 60fps taps. |
| **Python (OpenCV, scikit-learn, PyTorch) + FastAPI** | Offline puzzle pipeline + difficulty calibration. Judges see *authentic expertise*, not AI-generated filler. |
| **MCP security / Vexar** | Anti-cheat mindset: server-validated guesses, rate limits, streak verification via Devvit Journeys. |
| **Building in public** (profile README, documented repos) | You already know how to write the README judges read. Polish points. |

**Strategic conclusion:** Your game should *look like* a computer-vision product that happens to be a game. That's the moat.

---

## 3. The Idea: LENS — The Daily Anomaly Hunt

**Tagline:** *One image. One anomaly. 60 seconds.*

**Genre:** Daily visual forensics. A brand-new category on Devvit — not a clone of anything.

### The 60-second loop

```
  ┌─ FEED SPLASH (inline preview) ─────────────────┐
  │  LENS #42 · Today's image (blurred teaser)     │
  │  "Something's off. Can you spot it?"  [ Play ]  │
  └──────────────────┬─────────────────────────────┘
                     │ tap Play → expanded mode
  ┌─ GAME (full-screen) ───────────────────────────┐
  │  ⏱ 0:47   ●●○ attempts   Streak 🔥 7            │
  │  ┌──────────────────────────────────────┐      │
  │  │   [ Full-bleed daily image ]         │      │
  │  │   (satellite / microscopy /          │      │
  │  │    industrial / terrain texture)     │      │
  │  └──────────────────────────────────────┘      │
  │  Tap anywhere to mark the anomaly.             │
  │  3 taps max. Closer = more points.             │
  └──────────────────┬─────────────────────────────┘
                     │ after 3 taps or timeout
  ┌─ RESULT CARD ────────────────────────────────┐
  │  🎯 FOUND in 23s · 847 pts · Top 12%         │
  │  [ Heatmap bloom: crowd taps glow, yours ★ ] │
  │  "The anomaly: a missing crater at 62%, 31%" │
  │  🔥 Streak 7 · 🏅 Sharp Eye flair earned      │
  │  [ Share ] [ Discuss ↓ ] [ Subscribe ]        │
  └──────────────────────────────────────────────┘
```

**Scoring:** Points = f(distance to true anomaly, time remaining). Bullseye (<5% of image) = 1000 pts. Near miss = partial. Miss = 0. Percentile vs. today's players. One scored attempt per day (anti-cheat), unlimited practice on Archive.

**Difficulty curve (calibrated, not random):**
- **Mon–Tue (Warm-up):** large, high-contrast anomaly (color shift, extra object). ~90% find rate.
- **Wed–Thu (Standard):** medium (rotated patch, flipped tile, subtle texture break).
- **Fri–Sun (Expert):** small, low-contrast (single-pixel cluster, missing detail, camouflaged). ~30% find rate.
- **Weekly Master Lens (Sunday):** hand-picked hardest of the week + leaderboard.

**Daily content engine:** Seeded PRNG from UTC date → same puzzle for everyone, every timezone. Pre-generate a 365-day bank offline (see Architecture). Archive mode replays any past day. Seasonal events (Space Week, Deep Sea, Lab Week) reskin the same mechanic with themed image packs.

### Why this is genuinely new (competitive scan)

| Existing Devvit daily game | Mechanic | Overlap with LENS |
|---|---|---|
| r/HotAndCold | Guess a location via hot/cold hints | None — geography vs. visual forensics |
| r/ColorPuzzleGame | Color matching puzzle | None — color logic vs. anomaly spotting |
| r/Syllo, r/LetterSet, r/Ninigrams | Word/syllable puzzles | None — language vs. vision |
| r/PocketGrids | Grid logic | None — logic grid vs. image perception |
| r/Syllacrostic | Crossword-style | None |
| **LENS (yours)** | **Spot the 1 anomaly in 1 image + collective heatmap** | **New genre. No Devvit game does visual forensics + crowd heatmap.** |

It also dodges every "common idea" warning: not a shooter, not a Wordle clone, not trivia, not a platformer, not collaborative storytelling. It's a *perception* game — a category Reddit doesn't have yet.

### Why it wins each judging criterion

**1. Delightful UX** — Zero setup. Open post → tap Play → tap image. No tutorial screen, no wall of text. One contextual hint: *"Tap the odd one out."* The heatmap bloom on reveal is the delight moment — your dot lights up inside a glowing crowd cloud. Fits the viewport, accessible contrast, big tap targets.

**2. Polish** — Bespoke visual identity (dark lab aesthetic, lens-ring motif, monospace stats), hand-tuned spring animations, haptic-feel feedback (scale pulse on tap), result card with streak/percentile/subscribe — exactly the "clear end state + re-engagement loop" judges ask for. Devvit Rules compliant (no external tracking, no filesystem, TypeScript throughout).

**3. Reddit-y** — This is the killer feature: **the collective heatmap**. Every player's tap is aggregated into a crowd-intelligence visualization. Comments explode with *"I found it in 4 seconds, where is it?!"* Flair rewards (Sharp Eye / Missed / Streak 7), streaks, snoovatar on the share card, subreddit-specific packs (r/space gets Space Lens, r/microscopy gets Lab Lens). The game *creates* discussion — the definition of Reddit-y.

**4. Daily Content** — Seeded daily puzzle + 30-day Archive + Weekly Master Lens + seasonal packs + procedural generation = infinite fresh content with a calibrated difficulty curve. Players return for streaks, percentiles, and tomorrow's image.

---

## 4. The Revenue Machine (3 Stacked Engines)

This is not a "win $15k and stop" project. It's designed to earn *after* the hackathon.

### Engine 1 — Reddit Developer Funds (passive, engagement-based)
- Pays for apps installed in communities with **1,000+ members**, based on engagement milestones (historically up to **$167k per app** across the program).
- **Play:** Launch in your test sub → seed into 5–10 niche subs (r/space, r/microscopy, r/industrial, r/Maps, r/puzzles) → grow to 1k+ members → apply for Featuring Program → viral distribution.
- **Why it works:** Daily games are the stickiest Devvit category. Streaks + daily posts = DAU. DAU = Funds.

### Engine 2 — Payments Sandbox API (active, per-user)
- Users spend **Reddit Gold** on digital goods in your app; you earn **$0.01 per Gold**.
- **Freemium model:**
  - **Free:** 1 daily puzzle, streaks, heatmap, share card.
  - **Paid (Gold):** Hint Pack (reveal quadrant), Archive Pass (replay 30 days), Theme Packs (Space Lens, Deep Sea, Lab), Expert Mode (no timer, harder), Streak Freeze (protect your streak), Custom Flair.
- **Why it works:** 60-second loop = high conversion. Players who miss by 2% will pay for a hint. Streak Freeze is a proven mobile-game monetizer.

### Engine 3 — B2B Licensing (the real money)
- **White-label LENS for educators & museums:** science centers, schools, and training orgs license themed packs (e.g., "Industrial Safety Lens" — spot the missing PPE, directly from your SeeWise.AI domain).
- **Subreddit Pro for mods:** analytics dashboard, custom packs, pinned daily posts.
- **Why it works:** Your CV background makes this credible. A safety-training anomaly game is a product, not just a toy.

**Revenue math (conservative):** 10k DAU × 2% hint conversion × $1 avg spend = $200/day from Payments alone, plus Developer Funds milestones, plus one B2B license. The hackathon prize is the *seed*, not the ceiling.

---

## 5. Complete Architecture

### 5.1 Tech stack (Devvit Web canonical)

```
┌─────────────────────────────────────────────────────────┐
│  REDDIT (hosting, CDN, auth, Redis — all free)          │
│                                                         │
│  ┌─ Client (browser, in iframe) ───────────────────┐    │
│  │  React + Vite + TypeScript                    │    │
│  │  Canvas 2D (image + heatmap) + CSS springs    │    │
│  │  (three.js optional for 3D packs)             │    │
│  │  Entrypoints: splash.html (feed) + game.html  │    │
│  └──────────────────┬──────────────────────────────┘    │
│                     │ HTTPS + JSON (fetch)                │
│  ┌─ Server (Devvit serverless, Node + Hono) ──────┐    │
│  │  /api/daily  /api/guess  /api/results          │    │
│  │  /api/heatmap  /api/streak  /api/leaderboard   │    │
│  │  Scheduler: daily-post (cron 0 0 * * *)        │    │
│  │  Triggers: onAppInstall → first post           │    │
│  │  Menu: moderator "Post today's Lens"           │    │
│  └──────────────────┬──────────────────────────────┘    │
│                     │ Redis (Devvit KV)                   │
│  ┌─ Storage ────────────────────────────────────┐    │
│  │  daily:{date}  guess:{user}:{date}           │    │
│  │  streak:{user}  heatmap:{date} (grid counts) │    │
│  │  leaderboard:{date}  puzzle-bank (JSON)      │    │
│  └──────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
         ▲ offline (not on Reddit)
┌─ Puzzle Generator (Python, GitHub Actions) ─────────────┐
│  OpenCV + Pillow + scikit-learn                         │
│  Base images (CC0/NASA) → inject anomaly → score        │
│  difficulty (SSIM + saliency) → emit 365-day bank JSON   │
└─────────────────────────────────────────────────────────┘
```

**Why this stack:** It's the official React template (`devvit-template-react`) + Hono + Redis — the exact pattern Reddit documents. No servers to pay for, no DB to manage, global CDN free. Your React/three.js skills transfer 1:1.

### 5.2 Client (what players touch)

| File | Role |
|---|---|
| `splash.html` / `Splash.tsx` | Feed preview: blurred teaser, title, Play button. Fetches `/api/daily` for today's state. |
| `game.html` / `Game.tsx` | Full game: image canvas, timer, 3-tap input, hint button. Calls `/api/guess` per tap. |
| `Result.tsx` | Heatmap bloom (canvas), stats, percentile, share card, streak, flair, subscribe CTA. |
| `Archive.tsx` | Replay past days (practice, unscored). |
| `Profile.tsx` | Streaks, total finds, accuracy, best time, flair collection. |
| `shared/api.ts` | Typed contract between client and server (endpoint names + request/response types). |

**Rendering:** Canvas 2D for image + heatmap (fast, small bundle). Heatmap = 20×20 grid of tap counts → radial-gradient bloom animation. Tap feedback = expanding ring + pulse. All animations CSS springs, no heavy libs. Bundle target: <300KB.

### 5.3 Server (Devvit serverless)

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/daily` | GET | Returns today's puzzle (image URL, difficulty, attempts left, streak). Seeded by UTC date. |
| `/api/guess` | POST | Validates tap (rate-limited, 1 scored attempt/day), computes distance + points, stores guess, increments heatmap grid. |
| `/api/results` | GET | Returns reveal data: true anomaly location, your percentile, crowd stats. Only after attempt used. |
| `/api/heatmap` | GET | Returns 20×20 grid counts for today's reveal animation. |
| `/api/streak` | GET/POST | Updates streak on find, verifies via Devvit Journeys event. |
| `/api/leaderboard` | GET | Today's top 100 by points/time. |
| `/internal/scheduler/daily-post` | POST (cron) | Creates today's post at 00:05 UTC via `reddit.submitCustomPost`. |
| `/internal/menu/post-create` | POST | Moderator manual post (for testing). |
| `/internal/triggers/on-app-install` | POST | Creates first post on install. |

**Anti-cheat (server is source of truth):**
- Server computes distance from stored anomaly coordinates — client never sends "I won".
- One scored attempt per user per day (Redis key `guess:{user}:{date}` with TTL).
- Rate limit: max 10 guesses/min per user.
- Timestamp validation: guess must be within today's UTC window.
- Streak verification via Devvit Journeys events (not client claims).

### 5.4 Puzzle pipeline (your moat — Python offline)

This is where you beat everyone. Most entrants hand-craft 10 puzzles. You generate 365+ calibrated ones.

```
  Base image bank (CC0 / NASA / Unsplash, 200+ images)
        │
        ▼
  Anomaly injector (OpenCV):
    • Copy-paste patch (texture break)
    • Color shift (single region)
    • Rotation / flip (one tile)
    • Object removal (inpainting)
    • Camouflage (low-contrast insert)
        │
        ▼
  Difficulty scorer:
    • SSIM (structural similarity) — lower = harder
    • Saliency map (scikit-learn) — anomaly prominence
    • Size / contrast of injected region
    → outputs difficulty 1–10
        │
        ▼
  Bank builder:
    • Assign difficulty by weekday (Mon easy → Sun expert)
    • Seed by UTC date (mulberry32 PRNG)
    • Emit puzzle-bank.json (image ref + anomaly x,y + difficulty)
        │
        ▼
  Upload to Redis / bundle as static JSON
```

**Image sources (rights-safe):** NASA Image Library (public domain), Unsplash/Pexels (free), Wikimedia Commons CC0, microscopy/satellite textures. Never use copyrighted game art. Document sources in README.

**Subreddit packs:** Same injector, themed base banks:
- **Space Lens** (NASA satellite/moon) → r/space, r/astronomy
- **Lab Lens** (microscopy/cells) → r/microscopy, r/biology
- **Safety Lens** (industrial/PPE scenes) → r/industrial, safety subs (your SeeWise.AI edge)
- **Terrain Lens** (topo/satellite earth) → r/Maps, r/geography

### 5.5 Data model (Redis keys)

```
daily:2026-11-28        → { puzzleId, anomalyX, anomalyY, difficulty, imageRef }
guess:u_abc123:2026-11-28 → { taps: [{x,y,t}], points, found, timeMs }
streak:u_abc123         → { current, best, lastPlayDate }
heatmap:2026-11-28      → { grid: [400 ints], totalTaps }
leaderboard:2026-11-28  → sorted set (user → points)
flair:u_abc123          → { sharpEye: true, missed: false, ... }
```

All keys with TTL (daily data expires in 35 days; streaks persist). No PII stored beyond Reddit user IDs.

### 5.6 Reddit integration (the "Reddit-y" layer)

| Feature | Implementation |
|---|---|
| **Daily post** | Scheduler creates post at 00:05 UTC: *"LENS #42 — Something's off. Spot it in 60s."* |
| **Flair** | On find: assign "Sharp Eye" flair. On miss: "Missed it". Streak milestones: "Streak 7 🔥". Via `reddit.setUserFlair`. |
| **Comments** | Result card links to post comments. Prompt: *"Where was it? Drop your guess before the reveal."* Debate = engagement. |
| **Snoovatar** | Share card renders player's snoovatar avatar + stats. |
| **Subscribe CTA** | Result card: *"Get tomorrow's Lens in your feed"* → subreddit subscribe prompt. |
| **Devvit Journeys** | Instrument: `game_start`, `guess_made`, `game_complete`, `streak_milestone`, `share_clicked` for analytics + streak verification. |
| **Demo sub** | Public test sub <200 members + install `devvit-dev-bot` so admins auto-join. Judges test here. |

### 5.7 Monetization wiring (post-hackathon, design now)

- **Payments API:** Define goods in `devvit.json` (`hint-pack`, `archive-pass`, `theme-space`, `streak-freeze`). Client checks entitlement via server before granting. Keep free loop intact — paywalls only on depth, never on the daily puzzle.
- **Developer Funds:** Track DAU + installs in 1k+ subs. Apply when eligible.
- **B2B:** Keep puzzle generator + theme packs modular so you can white-label without forking the core.

### 5.8 Testing & quality gates

- `npm run dev` → `devvit playtest` in your dev sub. Edit → refresh → live.
- `devvit logs r/<dev-sub>` in a second terminal for server logs.
- Test matrix: mobile (primary), desktop, dark/light mode, slow network, expired daily post, double-tap race, timezone edge (UTC midnight).
- Accessibility: keyboard tap alternative, colorblind-safe heatmap (blue→yellow, not red→green), text alternatives for image.

---

## 6. 10-Day Build Plan (Nov 28 → Dec 8)

| Day | Date | Focus | Deliverable |
|---|---|---|---|
| **1** | Nov 28 | Setup + puzzle pipeline | `npm create devvit --template=react lens`, devvit login, Python injector generates 30 test puzzles |
| **2** | Nov 29 | Core loop | Splash + Game + 3-tap input + timer. Playable with hardcoded puzzle. |
| **3** | Nov 30 | Server + Redis | `/api/daily`, `/api/guess`, `/api/results`, anti-cheat, heatmap grid |
| **4** | Dec 1 | Result + heatmap bloom | Result card, percentile, share card, streak, flair |
| **5** | Dec 2 | Daily post + packs | Scheduler cron, onInstall trigger, 4 theme packs, 365-day bank |
| **6** | Dec 3 | Reddit-y layer | Comments prompt, subscribe CTA, snoovatar, Journeys events |
| **7** | Dec 4 | Polish pass | Animations, accessibility, bundle size, mobile viewport, AI-slop audit |
| **8** | Dec 5 | Demo sub + playtest | Public test sub, devvit-dev-bot, 5 friends playtest, fix top 5 issues |
| **9** | Dec 6 | Submission assets | README.md, Devpost form, <1min video, app listing link, demo post link |
| **10** | Dec 7 | Buffer + Helper/Feedback | Submit draft, answer 3 questions in r/Devvit/Discord, fill feedback survey |
| **Deadline** | Dec 8, 6pm PT | **Submit** | Final Devpost submission. Do not publish the app. |

**Scope discipline:** If time runs short, cut Archive and Theme Packs first. Never cut: core loop, heatmap reveal, streak, daily post, demo sub. Those are the judging criteria.

---

## 7. Submission Playbook (Judges Score the Demo Post)

**Checklist (from rules):**
- [ ] App listing link: `developers.reddit.com/apps/{your-app-name}` (after upload)
- [ ] Demo post: public sub (<200 members) + post running the game. Install `devvit-dev-bot` for admin auto-join.
- [ ] README.md in repo root: game description, how to play, tech stack, image sources, how daily seeding works.
- [ ] Optional video <1min: screen-record feed → Play → tap → heatmap reveal → share. Upload to YouTube, link in form.
- [ ] Optional public repo link.
- [ ] Feedback survey (for $200 Feedback prize).
- [ ] Helper activity (for $500 Helper prize): answer questions in r/Devvit + Discord during the period.

**Demo post title:** `LENS #1 — Something's off. Spot the anomaly in 60 seconds.`
**Demo post body:** One line: *"Tap Play. Find the one thing that's wrong. The crowd heatmap reveals where everyone looked."* Judges should get it in 10 seconds.

**Video script (45 seconds):**
1. (0–5s) Feed scroll → LENS post. *"One image. One anomaly."*
2. (5–15s) Tap Play → image appears. *"60 seconds. Tap the odd one out."*
3. (15–25s) Tap → ring feedback → *"Closer… closer…"*
4. (25–40s) Heatmap bloom. *"Everyone's taps glow. Yours is the star."*
5. (40–45s) Share card + streak. *"Tomorrow, a new image. Same crowd."*

---

## 8. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Image copyright | CC0/NASA/Unsplash only. Document every source in README. |
| Bundle too large | Canvas 2D, no three.js in v1. Lazy-load theme packs. Target <300KB. |
| "AI slop" detection | Hand-tuned animations, bespoke copy, real puzzle pipeline (not AI-generated images). Show your CV expertise in README. |
| Daily post fails | Scheduler + moderator menu fallback + onInstall trigger. Test cron before submission. |
| Cheating (inspect element) | Server validates distance. Client never knows true coordinates until reveal. |
| Low initial players → empty heatmap | Seed heatmap with 20–50 synthetic taps (clearly labeled "early crowd") for demo. Real taps take over within hours. |
| Time runs out | Cut Archive/Packs, keep core loop + heatmap + streak. Submit early, iterate in buffer day. |

---

## 9. Post-Hackathon Roadmap (Revenue Machine Activation)

**Week 1 after judging:** Publish app (App Review) → apply for Featuring Program.
**Month 1:** Seed into 5 niche subs → grow to 1k+ members → Developer Funds eligibility.
**Month 2:** Ship Payments goods (Hint Pack, Archive Pass, Theme Packs) → first Gold revenue.
**Month 3:** Pitch 3 B2B pilots (safety training, science museum, school) using Safety Lens pack.
**Ongoing:** Weekly Master Lens + seasonal events → retention → DAU growth → more Funds + more Gold.

---

## 10. Naming & Identity

**Recommended:** **LENS — The Daily Anomaly Hunt**
- Short, visual, ownable. Lens-ring logo, dark lab aesthetic, monospace stats.
- Alternatives if taken: *Spotlight Daily*, *Odd One Out*, *Forensic*, *The Anomaly*.

**Visual identity (anti-AI-slop):**
- Palette: near-black `#0A0E14`, signal cyan `#22D3EE`, alert amber `#F59E0B`, paper white.
- Type: system sans for UI, monospace for stats/timer (lab-instrument feel).
- Motif: lens ring + crosshair. Every screen has it. Instantly recognizable in feed.

---

### Final word

You are not building "a game." You are building **a daily perception ritual with a crowd-intelligence reveal** — a category Reddit doesn't have, built on expertise only you have in this hackathon, with three revenue engines stacked behind it. The $15k prize is the least interesting outcome. The interesting outcome is a DAU-generating daily habit that pays you every day after.

**Build LENS. Ship it in 10 days. Let the heatmap do the talking.**

---

*Strategy prepared for Ranjith Rosan · Analyst @ Accenture · ML/CV · Chennai · Nov 28, 2026*
*Sources: Reddit Game of the Day Hackathon rules (Devpost), Devvit Web docs, Developer Program / Payments API docs, existing Devvit daily games (r/HotAndCold, r/ColorPuzzleGame, r/Syllo, r/PocketGrids).*
