# How this profile maintains itself

This repository is my GitHub profile (`github.com/RANJITHROSAN17`). The README you see there is **regenerated from live GitHub API data every day** — nobody hand-edits the numbers.

## Architecture

| Piece | Role |
|---|---|
| `README.md` | Profile content. Anything between `<!-- DYNAMIC:name:START/END -->` markers is machine-generated; everything else is hand-written. |
| `.github/scripts/update_profile.py` | Standard-library-only Python updater (no `pip install`, so nothing can break from a dependency release). |
| `.github/scripts/test_update_profile.py` | Unit tests for the updater's helpers. CI runs them *before* regenerating, so a broken change can't publish a broken profile. |
| `.github/workflows/update-profile.yml` | Daily 03:17 UTC + manual dispatch. Uses only the built-in `GITHUB_TOKEN` — no personal access token exists anywhere in this repo. Commits only when the data actually changed. |
| `assets/banner.svg` | Self-hosted hero banner (hand-authored SVG — a computer-vision bounding box over a neural network). No external image service involved. |
| `.github/dependabot.yml` | Keeps the GitHub Actions themselves patched. |

## Generated sections

- `IMPACT_BADGES` — hero counters (external PRs, merged upstream, in review, external projects)
- `OSS_SUMMARY` / `OSS_SNAPSHOT` — one-line totals and "merged in / in review at" organisation lists
- `OSS_TABLE` — contributions by company/organisation, with upstream stars, per-org merged/in-review counts and latest PR
- `OSS_DETAILS` — expandable list of *every* featured PR, grouped by organisation
- `RECENT_PRS` — latest 12 merged/in-review PRs, capped at 3 per repo so one project can't crowd out the rest
- `PROJECT_CARDS` / `PROJECTS` — visual cards plus a detailed table (live stars, language, last-updated) for featured projects
- `STATS_CARDS` — stats / top-languages / streak cards. The top-languages URL is generated with **all of my forks excluded** (`exclude_repo=...`), so forking `microsoft/vscode` to send it a PR can never make TypeScript look like my most-used language.
- `UPDATED` — last-run stamp

## Honesty rules (enforced in code, not intentions)

1. A PR counts as **Merged** only if the API reports `pull_request.merged_at`. Closed-unmerged PRs are counted in totals, never featured.
2. Open PRs are labelled **In review**. Organisations are never claimed as "contributed to" on the strength of an open PR.
3. Open-source counters exclude my own repositories (`-user:me` in the linked search queries), so self-merges can't pad the numbers. Every headline number links to the live search that proves it.
4. On any API failure the script exits non-zero **without touching the README** — a bad day at `api.github.com` degrades to yesterday's profile, never to an empty one.
5. External widget endpoints are only embedded after being health-checked (a popular activity-graph service was dropped after it started returning HTTP 402).

## Extending it

- **New organisation:** add one entry to `CURATED` in the updater (repo, display name, one factual line on what the PRs touch). Counts, avatar, stars and the detail list fill in automatically. Any repo reaching ≥2 merged or ≥3 open PRs is also auto-discovered.
- **New featured project:** add one entry to `FEATURED_PROJECTS`.
- **Run locally:** `GITHUB_TOKEN=<any valid token> python .github/scripts/update_profile.py` — then `git diff README.md`. Re-running on the same day with unchanged data is a no-op by design.

## Security

The workflow runs with the default, short-lived `GITHUB_TOKEN` and the minimum permission it needs (`contents: write`, to commit the README). There are no stored secrets, no third-party write actions, and no personal tokens. If you copy this setup: **never** commit a token, and never paste one into chat, issues, or code.
