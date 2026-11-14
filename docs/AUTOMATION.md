# How this profile maintains itself

This repository powers [my GitHub profile](https://github.com/RANJITHROSAN17). The dashboard is generated from the live GitHub REST and GraphQL APIs **once a day at 00:17 UTC (05:47 IST)**. GitHub can delay scheduled workflows; the timestamp in the README is the last successful data refresh, not a promised execution time.

## What changed in the visual audit

The previous README had useful contribution receipts, but its charts depended on separate third-party renderers, its footer claimed a two-hour refresh while the displayed date was stale, and the workflow committed only `README.md`. That setup could not reliably publish self-hosted chart files or keep their caches fresh.

The dashboard now uses one coordinated visual system, generated in this repository:

| Visualization | Real data source | What it shows |
|---|---|---|
| **Live profile signal** | REST profile, repositories and complete PR search | Merged upstream PRs, open PRs, distinct landed projects, stars on original repositories, followers, and actual merge counts for the last 12 calendar months. |
| **Contribution calendar** | GraphQL `contributionsCollection.contributionCalendar` | 365 daily public contribution counts, GitHub's own intensity quartiles, active days, and current/longest streaks within that window. |
| **Upstream outcomes** | Complete external PR search | Merged, open and closed-unmerged outcomes, plus the five most active upstream repositories. Closed-unmerged work is not hidden from the outcome total. |
| **Repository language mix** | REST `/repos/{owner}/{repo}/languages` for every original public repository | GitHub Linguist byte shares, top five languages plus Other. Forks, archived repositories and the profile repository are excluded. |
| **Six selected project cards** | REST repository metadata | Live stars, forks, primary language and last push; each card links to its repository. The full featured table and unfeatured-repository list remain below the cards. |

All charts have separate light/dark SVGs, descriptive alternative text, visible metric definitions, and no JavaScript, remote fonts or embedded remote images. SVGs are self-hosted under `assets/generated/`. README image URLs include a content hash, so GitHub's image proxy fetches new artwork when the data changes.

## Architecture

| Piece | Role |
|---|---|
| `README.md` | Hand-written introduction plus machine-generated content between `<!-- DYNAMIC:name:START/END -->` markers. |
| `.github/scripts/update_profile.py` | Fetches and validates GitHub data, generates README sections, and publishes all files together. Standard library only. |
| `.github/scripts/profile_visuals.py` | Pure aggregation helpers and deterministic light/dark SVG rendering. No network calls or runtime dependencies. |
| `.github/scripts/test_*.py` | Offline tests for metric definitions, complete pagination, calendar integrity, XML safety, cache inputs, history and publication rollback. |
| `.github/workflows/update-profile.yml` | Daily schedule, manual dispatch, and regeneration when updater code lands on `main`. Tests run before any API refresh. |
| `data/profile-snapshot.json` | The dated public data behind the current dashboard, source URLs and metric definitions. |
| `data/profile-history.json` | One real aggregate observation per UTC day, capped at 366 observations. A same-day rerun replaces that day's observation. It never invents historical values. |
| `assets/banner.svg` | Static identity artwork. Decorative only; it contains no invented performance score. |

## Generated README sections

- `VISUAL_PULSE`, `CONTRIBUTION_GRAPH`, `INSIGHT_CHARTS` — the self-hosted dashboard.
- `PROJECT_CARDS` — six linked, live repository cards.
- `OSS_SUMMARY`, `OSS_SNAPSHOT`, `OSS_TABLE`, `OSS_DETAILS`, `RECENT_PRS` — verifiable upstream contribution receipts.
- `PROJECTS`, `MORE_REPOS` — the complete featured comparison and other original public repositories.
- `EXPERIENCE_OSS` — generated merged/in-review organisation line.
- `UPDATED` — the actual successful refresh timestamp and data scope.

Every expected marker must occur exactly once. A missing or duplicated marker fails the refresh instead of silently skipping a chart.

## Metric definitions and honesty rules

1. **Merged** requires `pull_request.merged_at`. An open PR is **in review**, never evidence of upstream acceptance. Monthly merge bars use the merge timestamp, not `updated_at`.
2. External PR metrics exclude the profile account and the configured personal organisations (`Quasynvo`, `pinchfoundry`). Proof links use the same exclusions.
3. Search pagination must complete, reconcile with `total_count`, and report `incomplete_results: false`. GitHub Search exposes at most 1,000 results; exceeding that window fails the refresh rather than publishing a partial count.
4. **Original repositories** means public, non-fork, non-archived repositories owned by the user, excluding the profile repository. Organisation projects can be featured separately but do not inflate personal repository stars or language bytes.
5. Language percentages are **repository bytes**, not authored lines, time spent or proficiency. Notebooks are included and explicitly labelled.
6. The contribution calendar is the public activity visible to the built-in Actions token. Private activity is not included. Streaks are limited to the displayed 365-day window; an empty today can leave a current streak ending yesterday.
7. The daily history starts with the first successful new-system refresh. It does not backfill follower/star history or manufacture a trend line from missing observations.
8. A required API, validation or rendering failure exits non-zero before publication. The previous README, charts and data remain intact. Filesystem publication stages all changes and rolls back replacements if a write fails.
9. A renamed, private or missing featured repository fails closed so a broken curated claim is noticed. Update the curation rather than silently presenting an empty card.

## Running and maintaining it

The scheduled workflow must be on the default branch (`main`). After merging a change, open **Actions → Update profile README → Run workflow** to refresh immediately.

Local refresh using the GitHub CLI's existing authentication (no token is printed or saved):

```bash
GITHUB_TOKEN="$(gh auth token)" python .github/scripts/update_profile.py
python -m unittest discover -s .github/scripts -p 'test_*.py' -v
git diff -- README.md assets/generated data
```

In Actions, the automatically supplied, short-lived `GITHUB_TOKEN` is sufficient for these public-data reads and repository writes. No personal access token or additional secret is required.

- **Change the visual project shortlist:** edit `VISUAL_PROJECTS`; every key must also exist in `FEATURED_PROJECTS`.
- **Add a featured project or upstream focus:** edit `FEATURED_PROJECTS` or `CURATED`. Keep descriptions factual; live numbers are filled by the updater.
- **Change the schedule:** edit the cron expression and the README's generated schedule wording together.
- **Inspect a suspicious number:** open `data/profile-snapshot.json`, follow its source links, then compare the relevant GitHub search or repository endpoint.

The workflow has `contents: write` only, a per-ref concurrency group, a timeout, and no third-party write action. Generated data commits do not match its push-path trigger, so the bot cannot trigger an update loop. Never commit or paste authentication tokens.
