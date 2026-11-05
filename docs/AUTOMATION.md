# How this profile maintains itself

This repository is my GitHub profile (`github.com/RANJITHROSAN17`). The README you see there is **regenerated from live GitHub API data every 2 hours** — nobody hand-edits the numbers.

## Architecture

| Piece | Role |
|---|---|
| `README.md` | Profile content. Anything between `<!-- DYNAMIC:name:START/END -->` markers is machine-generated; everything else is hand-written. |
| `.github/scripts/update_profile.py` | Standard-library-only Python updater (no `pip install`, so nothing can break from a dependency release). |
| `.github/scripts/test_update_profile.py` | Unit tests for the updater's helpers. CI runs them *before* regenerating, so a broken change can't publish a broken profile. |
| `.github/workflows/update-profile.yml` | Every 2 hours (`17 */2 * * *`) + manual dispatch. Uses only the built-in `GITHUB_TOKEN` — no personal access token exists anywhere in this repo. Commits only when the data actually changed. |
| `assets/banner.svg` | Self-hosted hero banner (hand-authored SVG — a computer-vision bounding box over a neural network). No external image service involved. |
| `.github/dependabot.yml` | Keeps the GitHub Actions themselves patched. |

## Generated sections

- `IMPACT_BADGES` — hero counters (external PRs, merged upstream, in review, external projects)
- `OSS_SUMMARY` / `OSS_SNAPSHOT` — one-line totals and "merged in / in review at" organisation lists
- `OSS_TABLE` — contributions by company/organisation, with upstream stars, per-org merged/in-review counts and latest PR
- `OSS_DETAILS` — expandable list of *every* featured PR, grouped by organisation
- `RECENT_PRS` — latest 12 merged/in-review PRs, capped at 3 per repo so one project can't crowd out the rest
- `PROJECT_CARDS` / `PROJECTS` — GitHub OpenGraph repository cards plus a detailed table (live stars, language, last-updated) for featured projects. Owner-qualified entries such as `Quasynvo/Quasnooze` support projects in personal organisations.
- `MORE_REPOS` — every public, non-fork repo **not** in the featured list, rendered with live stars and language. A new project can be momentarily unfeatured but never invisible.
- `EXPERIENCE_OSS` — the Experience section's "merged upstream / in review" line. It used to be typed by hand, which is how it drifted into claiming organisations whose PRs had been closed unmerged; it is generated now, so it can only state what the API currently says.
- `STATS_CARDS` — account stats and top languages computed by the updater itself. It sums each original public repository's GitHub language-byte map, with **all forks excluded**, so forking `microsoft/vscode` can never make TypeScript look like my most-used language. No third-party stats or streak-card service is involved.
- `UPDATED` — last-run stamp

## Honesty rules (enforced in code, not intentions)

1. A PR counts as **Merged** only if the API reports `pull_request.merged_at`. Closed-unmerged PRs are counted in totals, never featured.
2. Open PRs are labelled **In review**. Organisations are never claimed as "contributed to" on the strength of an open PR.
3. Open-source counters exclude my user account **and personal organisations** (`Quasynvo`, including its former `pinchfoundry` name). The API results are filtered locally and every proof link applies the matching `-user:` / `-org:` filters, so self-merges can't pad the numbers.
4. A curated organisation with no merged and no open PRs renders nothing — and is removed from `CURATED` at the next audit, because an unused entry is a claim waiting to become false.
5. On any API failure the script exits non-zero **without touching the README** — a bad day at `api.github.com` degrades to the previous profile, never to an empty one.
6. Project cards use GitHub's own OpenGraph images. Account statistics and language shares are rendered as Markdown/HTML from API data, so a paused third-party card service cannot leave broken images in those sections.

## Extending it

- **New organisation:** add one entry to `CURATED` in the updater (repo, display name, one factual line on what the PRs touch). Counts, avatar, stars and the detail list fill in automatically. Any repo reaching ≥2 merged or ≥3 open PRs is also auto-discovered.
- **New featured project:** add one entry to `FEATURED_PROJECTS`. Use the repository name alone for a user-owned repo, or `owner/repo` for a project in a personal organisation.
- **Run locally:** `GITHUB_TOKEN=<any valid token> python .github/scripts/update_profile.py` — then `git diff README.md`. Re-running on the same day with unchanged data is a no-op by design.

## Security

The workflow runs with the default, short-lived `GITHUB_TOKEN` and the minimum permission it needs (`contents: write`, to commit the README). There are no stored secrets, no third-party write actions, and no personal tokens. If you copy this setup: **never** commit a token, and never paste one into chat, issues, or code.

If a branch ruleset requires pull requests on `main`, `contents: write` alone does not let the updater make its final direct push. Add the GitHub Actions integration (`actor_id: 15368`, `actor_type: Integration`) to that ruleset's bypass actors rather than disabling branch protection or introducing a personal access token. Keep the bypass scoped to GitHub Actions; all other contributors remain subject to the ruleset.
