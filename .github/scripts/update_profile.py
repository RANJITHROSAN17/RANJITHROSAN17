#!/usr/bin/env python3
"""
Auto-update the GitHub profile README (RANJITHROSAN17/RANJITHROSAN17).

Runs daily via .github/workflows/update-profile.yml using only the Python
standard library (no pip installs). It refreshes self-hosted SVG visualizations,
a machine-readable snapshot, daily metric history and these README sections
from the live GitHub REST + GraphQL APIs:

  * DYNAMIC:VISUAL_PULSE   - verified impact counters and monthly merge rhythm
  * DYNAMIC:CONTRIBUTION_GRAPH - real public contribution calendar and streaks
  * DYNAMIC:INSIGHT_CHARTS - upstream outcomes and repository language bytes
  * DYNAMIC:OSS_SUMMARY    - total / merged / in-review PR counters
  * DYNAMIC:OSS_SNAPSHOT   - one-line "merged in / in review at" org lists
  * DYNAMIC:OSS_TABLE      - contributions grouped by company / organisation
  * DYNAMIC:OSS_DETAILS    - every featured PR, grouped by organisation
  * DYNAMIC:RECENT_PRS     - latest merged & in-review pull requests
  * DYNAMIC:PROJECTS       - featured own projects with live stars/language
  * DYNAMIC:MORE_REPOS     - every public repo not featured above, so no
                             project can fall off the profile unnoticed
  * DYNAMIC:EXPERIENCE_OSS - the Experience section's merged/in-review line
                             (generated, so a stale hand-typed claim cannot
                             survive here again)
  * assets/generated/*.svg - coordinated light/dark charts, no widget host
  * data/profile-snapshot.json - the exact public data behind the charts
  * data/profile-history.json - one real aggregate observation per UTC day

Honesty rules baked in:
  * A PR is only counted as "Merged" if pull_request.merged_at is set.
  * Open PRs are labelled "In review" - they are NOT claimed as merged
    contributions to Google / Microsoft / OpenAI etc.
  * Everything is linked to a live GitHub search query so any visitor
    can verify the numbers in one click.

Auth: reads GITHUB_TOKEN (provided automatically in GitHub Actions) or
GH_TOKEN / PROFILE_TOKEN from the environment. Never commit a token.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import urllib.error
from collections import defaultdict
from datetime import datetime, timezone, timedelta, date
from pathlib import Path

import profile_visuals as visuals

USER = os.environ.get("GH_USERNAME", "RANJITHROSAN17")
SELF_ORGS = ("Quasynvo", "pinchfoundry")
SELF_OWNERS = {USER.lower()} | {org.lower() for org in SELF_ORGS}
TOKEN = (
    os.environ.get("GITHUB_TOKEN")
    or os.environ.get("GH_TOKEN")
    or os.environ.get("PROFILE_TOKEN")
    or ""
)
ROOT = Path(__file__).resolve().parents[2]
README_PATH = ROOT / "README.md"
if len(sys.argv) > 1:  # allow: update_profile.py /path/to/README.md
    README_PATH = Path(sys.argv[1])
    ROOT = README_PATH.resolve().parent

IST = timezone(timedelta(hours=5, minutes=30))

# --------------------------------------------------------------- curation
# Featured organisations/projects (order = display order). "focus" is a
# short, factual description of what the PRs touch - edit it as work evolves.
#
# NOTE (Oct 2026 audit): Google Research, Microsoft/vscode, OpenAI cookbook,
# NSA Ghidra, Nous Research and Costura AI were removed from this list. Their
# PRs are all closed-and-unmerged, so per the honesty rules below they must
# never be presented as contributions - add_row() would skip them anyway, but
# a curated entry that claims an org implies work that does not exist. Any of
# them that lands >=2 merged PRs is picked up again automatically by the
# auto-discovery pass further down, so nothing is lost by removing them.
CURATED = [
    {
        "repo": "CrossGL/crosstl",
        "org": "CrossGL",
        "focus": "Shader transpiler (GLSL/HLSL/Metal/SPIR-V/Slang/WGSL) - "
                 "backend lowering, resource binding & provenance, conformance harness",
    },
    {
        "repo": "kubeflow/mcp-server",
        "org": "Kubeflow",
        "focus": "MCP server for Kubeflow Trainer - rate-limit/circuit-breaker & "
                 "RED metrics, schedulable-GPU counting, training lifecycle fixes",
    },
    {
        "repo": "ultralytics/yolov3",
        "org": "Ultralytics",
        "focus": "YOLOv3 object detection - requirements fix",
    },
    {
        "repo": "aws-samples/step-functions-workflows-collection",
        "org": "Amazon Web Services",
        "focus": "AWS Step Functions workflow collection - template update",
    },
    {
        "repo": "prakhar1605/Opencollab-mcp",
        "org": "Opencollab MCP",
        "focus": "Contribution-matchmaking MCP - shared GitHub paginator, "
                 "closing-PR vs. plain-mention detection",
    },
    {
        "repo": "golang-cafe/job-board",
        "org": "Golang Cafe",
        "focus": "Go job board - golangci-lint workflow updates",
    },
]
CURATED_REPOS = {c["repo"].lower(): c for c in CURATED}

# Early (2023) one-file dependency bumps etc. They still count in the totals
# at the top (nothing is hidden from the numbers) but featuring them next to
# Google/Microsoft would only dilute the signal, so they are not table rows.
EXCLUDE_FROM_TABLE = {
    "firstcontributions/first-contributions",
}

# Featured own projects (order = display order). Stars/language/updated are
# filled in live; "highlight" is yours to edit. Anything public that is NOT
# listed here still shows up automatically in the MORE_REPOS line below the
# cards, so an unlisted project is never an invisible one.
FEATURED_PROJECTS = [
    {
        "repo": "cardiolens-3d-risk",
        "name": "CardioLens 3D",
        "demo": "https://ranjithrosan17.github.io/cardiolens-3d-risk/",
        "highlight": "Research-only coronary-artery visualisation - interactive "
                     "three.js schematic + scikit-learn baseline served from FastAPI, "
                     "with a model card and documented limits (not for clinical use)",
        "stack": "React - three.js - FastAPI - scikit-learn",
    },
    {
        "repo": "Quasynvo/Quasnooze",
        "name": "Quasnooze",
        "demo": "",
        "highlight": "A private, local-first personal AI assistant for Telegram, "
                     "Discord, Slack, WhatsApp and the phone browser - permission-gated "
                     "tools, reminders and token streaming",
        "stack": "Node.js - Ollama - MCP - PWA - zero runtime deps",
    },
    {
        "repo": "Vexar-MCP",
        "name": "Vexar-MCP",
        "demo": "https://ranjithrosan17.github.io/Vexar-MCP/",
        "highlight": "Security, schema and token-cost scanner for MCP servers - static "
                     "analysis that never runs your code, CI policy gates, SARIF output, "
                     "and an explicit 'n/a' when a scan could not read a file",
        "stack": "Python - MCP - SARIF - GitHub Actions",
    },
    {
        "repo": "vexar-autofix",
        "name": "vexar-autofix",
        "demo": "https://ranjithrosan17.github.io/vexar-autofix/",
        "highlight": "An MCP security agent that has to prove its own patches: the finding "
                     "must drop, nothing else may break, the target's pytest suite must "
                     "still pass (Nebius x NVIDIA hackathon build)",
        "stack": "Python - NVIDIA Nemotron - Nebius Token Factory - MCP",
    },
    {
        "repo": "Wrytrove",
        "name": "Wrytrove",
        "demo": "https://ranjithrosan17.github.io/Wrytrove/",
        "highlight": "A calm, open-source Windows text and code editor with "
                     "optional local AI suggestions; unsigned early preview",
        "stack": "TypeScript - Rust - local AI",
    },
    {
        "repo": "dsa-mastery-plan-2026",
        "name": "DSA Mastery Plan 2026",
        "demo": "https://ranjithrosan17.github.io/dsa-mastery-plan-2026/",
        "highlight": "Pattern-first DSA roadmap - verified free LeetCode problems, "
                     "pattern playbooks and a browser-only progress tracker",
        "stack": "vanilla JS - GitHub Pages",
    },
    {
        "repo": "GroundingDino",
        "name": "Grounding DINO Auto-Labelling",
        "demo": "",
        "highlight": "Zero-shot labelling for object-detection datasets - describe "
                     "classes in English, review detections, export Pascal VOC",
        "stack": "PyTorch - Grounding DINO - supervision",
    },
    {
        "repo": "yolov3",
        "name": "YOLOv3 Custom Training",
        "demo": "",
        "highlight": "Step-by-step guide + notebook for training YOLOv3 on your own "
                     "dataset with Darknet in Google Colab",
        "stack": "Darknet - YOLOv3 - Colab",
    },
]

# A compact visual shortlist; the complete featured table remains below it.
VISUAL_PROJECTS = {
    "vexar-mcp": ("Static MCP security checks, CI policy gates and SARIF — without running your code.", "teal"),
    "vexar-autofix": ("Reviewable security patches, checked against findings and the target's tests.", "violet"),
    "quasynvo/quasnooze": ("A local-first AI assistant across web, desktop and the chat apps you already use.", "blue"),
    "wrytrove": ("A calm Windows code editor with optional local AI. Early preview, limits documented.", "amber"),
    "dsa-mastery-plan-2026": ("A pattern-first roadmap for practicing data structures and algorithms.", "rose"),
    "cardiolens-3d-risk": ("Interactive coronary visualisation and a research-only baseline. Not clinical advice.", "teal"),
}


def select_more_repos(own_repos: list[dict], featured: list[str], username: str) -> list[dict]:
    """Public, non-fork, non-archived repos of mine that are not featured yet.

    Newest push first. This is what keeps an unlisted project from becoming an
    invisible one: everything I own shows up somewhere on the profile.
    """
    skip = {name.lower() for name in featured} | {username.lower()}
    picked = [
        repo for repo in own_repos
        if not repo.get("fork")
        and not repo.get("archived")
        and not repo.get("private", False)
        and repo.get("name", "").lower() not in skip
    ]
    # Most-starred first, then most recently pushed: the best work leads, but
    # a brand-new repo still shows up immediately.
    return sorted(
        picked,
        key=lambda repo: (repo.get("stargazers_count", 0), repo.get("pushed_at") or ""),
        reverse=True,
    )


# ------------------------------------------------------------- GitHub API
def api_request(url: str, payload: dict | None = None):
    """Request complete JSON, retrying transient failures without logging auth."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{USER}-profile-updater",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    for attempt in range(3):
        req = urllib.request.Request(url, headers=headers, data=body)
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if payload is not None and (data.get("errors") or not data.get("data")):
                raise RuntimeError("GitHub GraphQL returned errors or no data")
            return data
        except urllib.error.HTTPError as exc:
            retryable = exc.code == 429 or exc.code >= 500 or (
                exc.code == 403 and exc.headers.get("x-ratelimit-remaining") == "0"
            )
            if not retryable or attempt == 2:
                raise
            delay = min(60, max(2 ** attempt, int(exc.headers.get("retry-after", "1") or 1)))
        except (urllib.error.URLError, TimeoutError):
            if attempt == 2:
                raise
            delay = 2 ** attempt
        time.sleep(delay)
    raise RuntimeError("GitHub API retries exhausted")


def api_get(url: str):
    return api_request(url)


def api_get_all(url: str, max_pages: int = 20):
    """Paginate completely; a truncated result must never become a real metric."""
    out = []
    total = None
    for page in range(1, max_pages + 1):
        sep = "&" if "?" in url else "?"
        data = api_get(f"{url}{sep}per_page=100&page={page}")
        if isinstance(data, dict) and "items" in data:
            if data.get("incomplete_results"):
                raise RuntimeError("GitHub search results are incomplete; preserving the previous snapshot")
            if total is None:
                total = data.get("total_count")
                if not isinstance(total, int) or total > 1000:
                    raise RuntimeError("GitHub search exceeds the complete 1,000-result API window")
            if data["total_count"] != total:
                raise RuntimeError("GitHub search changed during pagination; retry the workflow")
            out.extend(data["items"])
            if len(out) >= total:
                if len({p["id"] for p in out}) != total:
                    raise RuntimeError("GitHub search pagination contained duplicates or missing items")
                return out
            if not data["items"]:
                break
        elif isinstance(data, list):
            out.extend(data)
            if len(data) < 100:
                return out
        else:
            raise RuntimeError("Unexpected GitHub API pagination response")
    raise RuntimeError("GitHub pagination did not reach a complete result")


def search_prs(extra: str = "") -> list[dict]:
    q = urllib.parse.quote(f"type:pr author:{USER} {extra}".strip())
    # Creation order is stable while PRs are being updated during a refresh.
    return api_get_all(f"https://api.github.com/search/issues?q={q}&sort=created&order=asc")


def fetch_contributions(first: date, last: date) -> dict:
    """Use GitHub's actual contribution calendar, not the limited events feed."""
    if not TOKEN:
        raise RuntimeError("GITHUB_TOKEN is required for the GraphQL contribution calendar")
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            totalContributions
            weeks { contributionDays { date contributionCount contributionLevel } }
          }
        }
      }
    }
    """
    payload = api_request("https://api.github.com/graphql", {
        "query": query,
        "variables": {"login": USER, "from": f"{first.isoformat()}T00:00:00Z",
                      "to": f"{last.isoformat()}T23:59:59Z"},
    })
    user = payload["data"].get("user")
    if not user:
        raise RuntimeError("GitHub returned no contribution calendar for this user")
    calendar = user["contributionsCollection"]["contributionCalendar"]
    days = sorted((day for week in calendar["weeks"] for day in week["contributionDays"]),
                  key=lambda day: day["date"])
    result = {"from": first.isoformat(), "to": last.isoformat(),
              "total": calendar["totalContributions"],
              "days": [{"date": d["date"], "count": d["contributionCount"], "level": d["contributionLevel"]}
                       for d in days]}
    visuals.validate_calendar(result, first, last)
    return result


def repo_of(pr: dict) -> str:
    # repository_url: https://api.github.com/repos/OWNER/REPO
    return pr["repository_url"].split("/repos/", 1)[-1]


def is_external_pr(pr: dict) -> bool:
    owner = repo_of(pr).split("/", 1)[0].lower()
    return owner not in SELF_OWNERS


def is_merged(pr: dict) -> bool:
    return bool((pr.get("pull_request") or {}).get("merged_at"))


def pr_date(pr: dict) -> str:
    """Merge date for landed work; last-update date for work still in review."""
    return (pr.get("pull_request") or {}).get("merged_at") or pr.get("updated_at", "")


def fmt_stars(n: int) -> str:
    if n >= 1000:
        return f"{n / 1000:.0f}k" if n >= 10000 else f"{n / 1000:.1f}k"
    return str(n)


def esc(text: str) -> str:
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def xml_attr(text: str) -> str:
    return visuals.xml(text)


def search_url(extra: str, external_only: bool = False) -> str:
    # Exclude both my user account and personal orgs from the proof links.
    suffix = ""
    if external_only:
        suffix = f" -user:{USER}" + "".join(f" -org:{org}" for org in SELF_ORGS)
    q = urllib.parse.quote(f"type:pr author:{USER} {extra}{suffix}".strip())
    return f"https://github.com/search?q={q}&type=pullrequests"


# ---------------------------------------------------------------- blocks
def build_profile() -> tuple[dict[str, str], dict[str, bytes], dict]:
    now = datetime.now(timezone.utc)
    today = now.date()
    user = api_get(f"https://api.github.com/users/{USER}")
    own_repos = api_get_all(f"https://api.github.com/users/{USER}/repos?type=owner&sort=full_name")
    own_by_name = {r["name"].lower(): r for r in own_repos}
    featured_meta = []
    for fp in FEATURED_PROJECTS:
        if "/" in fp["repo"]:
            meta = api_get(f"https://api.github.com/repos/{fp['repo']}")
        else:
            meta = own_by_name.get(fp["repo"].lower())
        if not meta or meta.get("private") or meta.get("fork"):
            raise RuntimeError(f'Featured project is unavailable, private or forked: {fp["repo"]}')
        featured_meta.append((fp, meta))

    prs_all = search_prs()
    merged = [p for p in prs_all if is_merged(p)]
    open_prs = [p for p in prs_all if p.get("state") == "open"]
    external = [p for p in prs_all if is_external_pr(p)]
    ext_merged = [p for p in external if is_merged(p)]
    ext_open = [p for p in external if p.get("state") == "open"]
    external_repos = sorted({repo_of(p) for p in external}, key=str.lower)
    ext_closed = [p for p in external if not is_merged(p) and p.get("state") != "open"]
    if len(external) != len(ext_merged) + len(ext_open) + len(ext_closed):
        raise RuntimeError("External PR states do not reconcile; refusing to publish")

    original_repos = [r for r in own_repos if not r.get("fork") and not r.get("archived")
                      and not r.get("private", False) and r["name"].lower() != USER.lower()]
    language_bytes: dict[str, int] = defaultdict(int)
    for repo in original_repos:
        detected = api_get(f'https://api.github.com/repos/{repo["full_name"]}/languages')
        if not isinstance(detected, dict) or any(type(v) is not int or v < 0 for v in detected.values()):
            raise RuntimeError(f'Invalid language response for {repo["full_name"]}')
        for language, count in detected.items():
            language_bytes[language] += count
    contributions = fetch_contributions(today - timedelta(days=364), today)
    streaks = visuals.streak_metrics(contributions["days"], today)
    metrics = {
        "external_prs": len(external), "external_projects": len(external_repos),
        "merged_prs": len(ext_merged), "open_prs": len(ext_open),
        "closed_unmerged_prs": len(ext_closed),
        "merged_projects": len({repo_of(p).lower() for p in ext_merged}),
        "original_repos": len(original_repos),
        "original_stars": sum(r.get("stargazers_count", 0) for r in original_repos),
        "followers": user["followers"], "contributions": contributions["total"], **streaks,
    }
    snapshot = {
        "schema_version": 1, "generated_at": now.isoformat(timespec="seconds"),
        "as_of": today.isoformat(), "username": USER, "metrics": metrics,
        "contributions": contributions,
        "languages": {"repositories": len(original_repos), "total_bytes": sum(language_bytes.values()),
                      "items": [{"name": name, "bytes": count} for name, count in
                                sorted(language_bytes.items(), key=lambda item: (-item[1], item[0]))]},
        "merge_months": visuals.merge_month_buckets(ext_merged, today),
        "upstream_repos": [], "projects": [],
        "sources": {
            "profile": f"https://api.github.com/users/{USER}",
            "repositories": f"https://api.github.com/users/{USER}/repos?type=owner",
            "contributions": "https://api.github.com/graphql",
            "external_prs": search_url("", external_only=True),
            "merged_prs": search_url("is:merged", external_only=True),
            "open_prs": search_url("is:open", external_only=True),
        },
        "definitions": {
            "merged_prs": "External PRs with pull_request.merged_at set; personal account and organisations excluded.",
            "open_prs": "External PRs currently open; not a claim of upstream acceptance.",
            "original_repos": "Public, non-fork, non-archived repositories owned by the user, excluding the profile repository.",
            "original_stars": "Current stars on the original repositories defined above; organisation repositories excluded.",
            "languages": "Sum of GitHub Linguist language bytes on default branches; not authored lines or skill proficiency.",
            "contributions": "Public GitHub calendar visible to the built-in Actions token; not a private-activity total.",
            "streaks": "Consecutive active days within the displayed 365-day window; a zero-count today may end the current streak yesterday.",
        },
    }

    # --- group external PRs by repo ---
    by_repo: dict[str, dict] = defaultdict(
        lambda: {"merged": 0, "open": 0, "prs": []}
    )
    for pr in external:
        r = repo_of(pr)
        if is_merged(pr):
            by_repo[r]["merged"] += 1
        elif pr.get("state") == "open":
            by_repo[r]["open"] += 1
        else:
            continue  # closed-unmerged: counted in totals, not featured
        by_repo[r]["prs"].append(pr)

    # upstream star counts (for credibility context) - curated only
    stars: dict[str, int] = {}
    for c in CURATED:
        meta = api_get(f"https://api.github.com/repos/{c['repo']}")
        stars[c["repo"].lower()] = meta["stargazers_count"]

    now_ist = now.astimezone(IST).strftime("%d %b %Y")
    snapshot["upstream_repos"] = [
        {"repo": repo, **stats} for repo, stats in sorted(
            by_repo.items(), key=lambda item: (-(item[1]["merged"] + item[1]["open"]),
                                               -item[1]["merged"], item[0].lower()))
    ]
    # Keep the audit snapshot compact: PR details are already linked in README.
    for entry in snapshot["upstream_repos"]:
        entry.pop("prs", None)

    # --- OSS summary ---
    summary = (
        f"> **{len(external)} pull requests to {len(external_repos)} external projects** · "
        f"[**{len(ext_merged)} merged upstream**]({search_url('is:merged', external_only=True)}) · "
        f"[**{len(ext_open)} in review right now**]({search_url('is:open', external_only=True)}) · "
        f"auto-updated {now_ist} - every number below links to a live search you can verify.\n"
        f">\n"
        f"> Status key: 🟣 **Merged** = merged upstream &nbsp;·&nbsp; "
        f"🟢 **In review** = open PR, not yet merged - I don't claim orgs I haven't landed in (yet)."
    )

    # Charts are rendered only after every required API response is complete.

    # --- OSS table ---
    rows = [
        "| Organisation | Project | What my PRs touch | 🟣 Merged | 🟢 In review | Latest PR |",
        "|---|---|---|---:|---:|---|",
    ]
    featured_keys = set()
    snapshot_merged: list[str] = []
    snapshot_review: list[str] = []
    detail_sections: list[str] = []
    def add_row(repo: str, org: str, focus: str):
        stats = by_repo.get(repo) or next(
            (v for k, v in by_repo.items() if k.lower() == repo.lower()), None
        )
        if not stats or (stats["merged"] == 0 and stats["open"] == 0):
            return
        featured_keys.add(repo.lower())
        star_txt = f" (★{fmt_stars(stars[repo.lower()])})" if repo.lower() in stars else ""
        latest = sorted(stats["prs"], key=pr_date, reverse=True)[0]
        latest_no = latest["html_url"].rstrip("/").split("/")[-1]
        state_icon = "🟣" if is_merged(latest) else "🟢"
        owner = repo.split("/")[0]
        avatar = (f'<img src="https://github.com/{owner}.png?size=40" '
                  f'width="18" height="18" alt="{owner} logo" /> ')
        if stats["merged"]:
            snapshot_merged.append(f"[{esc(org)}](https://github.com/{repo})")
        if stats["open"]:
            snapshot_review.append(f"[{esc(org)}](https://github.com/{repo})")
        prs_sorted = sorted(stats["prs"], key=pr_date, reverse=True)
        prs_sorted = sorted(prs_sorted, key=is_merged, reverse=True)  # merged first
        bullets = [
            f"- {'🟣 Merged' if is_merged(pr) else '🟢 In review'} · {pr_date(pr)[:10]} · "
            f"[{esc(pr['title'])}]({pr['html_url']})"
            for pr in prs_sorted
        ]
        detail_sections.append(
            f"#### {avatar}{esc(org)} — [{repo}](https://github.com/{repo}) · "
            f"{stats['merged']} merged · {stats['open']} in review\n\n" + "\n".join(bullets)
        )
        rows.append(
            f"| {avatar}**{esc(org)}** | [{repo}](https://github.com/{repo}){star_txt} "
            f"| {esc(focus)} | {stats['merged'] or '·'} | {stats['open'] or '·'} "
            f"| {state_icon} [#{latest_no}]({latest['html_url']}) |"
        )

    for c in CURATED:
        add_row(c["repo"], c["org"], c["focus"])

    # auto-discover future work: new repos with >=2 merged or >=3 open PRs
    for repo, stats in sorted(by_repo.items(), key=lambda kv: (-kv[1]["merged"], -kv[1]["open"])):
        rl = repo.lower()
        if rl in featured_keys or rl in CURATED_REPOS or rl in EXCLUDE_FROM_TABLE:
            continue
        if stats["merged"] >= 2 or stats["open"] >= 3:
            add_row(repo, repo.split("/")[0], "Auto-discovered from recent PR activity")

    other_merged = len(ext_merged) - sum(
        stats["merged"] for repo, stats in by_repo.items() if repo.lower() in featured_keys
    )
    oss_table = "\n".join(rows)
    if other_merged > 0:
        oss_table += (
            f"\n\n<sub>Plus {other_merged} earlier merged PRs in smaller projects - "
            f"[see every upstream-merged PR]({search_url('is:merged', external_only=True)}).</sub>"
        )

    merged_line = " · ".join(snapshot_merged) or "No featured merged PRs right now"
    if other_merged > 0:
        merged_line += f" · +{other_merged} merged PRs in other projects"
    oss_snapshot = (
        f"**🟣 Merged upstream in:** {merged_line}\n\n"
        f"**🟢 Currently in review at:** {' · '.join(snapshot_review) or 'No featured open PRs right now'}"
    )
    oss_details = (
        "<details>\n<summary><strong>📂 Expand — every featured PR, "
        "grouped by organisation (auto-updated)</strong></summary>\n\n"
        + "\n\n".join(detail_sections)
        + "\n\n</details>"
    )

    # --- Experience section line (generated, never hand-typed) ---
    # A hand-written "Merged: X · In review: Y" cell drifted out of date
    # silently in the past; generating it means the Experience table can only
    # ever state what the API currently says.
    exp_bits = []
    if snapshot_merged:
        merged_text = " · ".join(snapshot_merged)
        if other_merged > 0:
            merged_text += f" · +{other_merged} earlier in smaller projects"
        exp_bits.append("🟣 **Merged upstream:** " + merged_text)
    if snapshot_review:
        exp_bits.append("🟢 **In review:** " + " · ".join(snapshot_review))
    else:
        exp_bits.append("🟢 **In review:** nothing open at the moment")
    experience_oss = (
        "<sub>" + " &nbsp;·&nbsp; ".join(exp_bits)
        + ' &nbsp;→&nbsp; <a href="#open-source">full breakdown</a></sub>'
    )

    # --- recent PRs ---
    recent_src = [
        p for p in external
        if is_merged(p) or p.get("state") == "open"
    ]
    recent_src.sort(key=pr_date, reverse=True)
    # Diversity cap: max 3 per repo, so a same-day burst in one project
    # (e.g. 6 CrossGL PRs) doesn't crowd out the breadth across orgs.
    per_repo: dict[str, int] = defaultdict(int)
    recent_picked: list[dict] = []
    for pr in recent_src:
        r = repo_of(pr)
        if per_repo[r] >= 3:
            continue
        per_repo[r] += 1
        recent_picked.append(pr)
        if len(recent_picked) >= 12:
            break
    recent_lines = []
    for pr in recent_picked:
        icon = "🟣 Merged" if is_merged(pr) else "🟢 In review"
        date = pr_date(pr)[:10]
        recent_lines.append(
            f"- {icon} · {date} · [{esc(pr['title'])}]({pr['html_url']}) "
            f"in [{repo_of(pr)}](https://github.com/{repo_of(pr)})"
        )
    recent = "\n".join(recent_lines)

    # --- featured projects ---
    proj_rows = [
        "| Project | What it is | Stack | ★ | Language | Last push |",
        "|---|---|---|---:|---|---|",
    ]
    for fp, meta in featured_meta:
        name = f"**[{fp['name']}]({meta['html_url']})**"
        if fp.get("demo"):
            name += f" · [live demo]({fp['demo']})"
        proj_rows.append(
            f"| {name} | {esc(fp['highlight'])} | {esc(fp['stack'])} "
            f"| {meta.get('stargazers_count', 0)} | {esc(meta.get('language') or '·')} "
            f"| {(meta.get('pushed_at') or '')[:10]} |"
        )
    projects = "\n".join(proj_rows)

    # --- self-hosted visual project cards ---
    for fp, meta in featured_meta:
        key = fp["repo"].lower()
        if key not in VISUAL_PROJECTS:
            continue
        tagline, accent = VISUAL_PROJECTS[key]
        snapshot["projects"].append({
            "slug": re.sub(r"[^a-z0-9-]+", "-", meta["full_name"].lower()),
            "name": fp["name"], "repo": meta["full_name"], "url": meta["html_url"],
            "demo": fp.get("demo", ""), "tagline": tagline, "accent": accent,
            "stars": meta["stargazers_count"], "forks": meta["forks_count"],
            "language": meta.get("language"), "pushed_at": meta.get("pushed_at"),
        })
    visual_order = {key: index for index, key in enumerate(VISUAL_PROJECTS)}
    snapshot["projects"].sort(key=lambda p: visual_order.get(
        next((fp["repo"].lower() for fp, meta in featured_meta if meta["full_name"] == p["repo"]), ""), 999))
    assets = visuals.render_all(snapshot)

    def asset_url(name: str, theme: str) -> str:
        path = f"assets/generated/{name}.{theme}.svg"
        # Content-hashed URLs defeat GitHub's image proxy cache only when art changes.
        digest = hashlib.sha256(assets[path]).hexdigest()[:12]
        return f"./{path}?v={digest}"

    def picture(name: str, alt: str, width: str = "100%") -> str:
        return (f'<picture><source media="(prefers-color-scheme: dark)" '
                f'srcset="{asset_url(name, "dark")}" />'
                f'<img width="{width}" alt="{xml_attr(alt)}" src="{asset_url(name, "light")}" /></picture>')

    m = snapshot["metrics"]
    visual_pulse = picture("pulse", (
        f'{m["merged_prs"]} external PRs merged; {m["open_prs"]} in review; '
        f'{m["merged_projects"]} upstream projects landed; {m["original_stars"]} stars '
        f'on {m["original_repos"]} original repositories; {m["followers"]} followers. '
        f'Snapshot {snapshot["as_of"]}.'))
    contribution_graph = picture("contributions", (
        f'{m["contributions"]} public contributions in the last 365 days; '
        f'{m["active_days"]} active days; current streak {m["current_streak"]} days; '
        f'longest streak in this window {m["longest_streak"]} days.'))
    insight_charts = '<p align="center">\n' + "\n".join([
        picture("upstream", f'Upstream PR outcomes: {m["merged_prs"]} merged, {m["open_prs"]} open, {m["closed_unmerged_prs"]} closed unmerged.', "49%"),
        picture("languages", "GitHub language bytes across original public repositories; forks and archived repositories excluded. Byte share is not skill proficiency.", "49%"),
    ]) + "\n</p>"
    cards = []
    for project in snapshot["projects"]:
        name = f'project-{project["slug"]}'
        alt = f'{project["name"]}: {project["stars"]} stars, {project["forks"]} forks, {project["language"] or "mixed language"}, pushed {(project["pushed_at"] or "")[:10]}.'
        cards.append(f'<a href="{project["url"]}">{picture(name, alt, "49%")}</a>')
    project_cards = '<p align="center">\n' + "\n".join(cards) + "\n</p>"

    # --- everything else I own (so no project is silently missing) ---
    featured_names = [fp["repo"].split("/")[-1] for fp in FEATURED_PROJECTS]
    more = select_more_repos(own_repos, featured_names, USER)
    more_bits = []
    for repo in more:
        stars = repo.get("stargazers_count", 0)
        language = repo.get("language") or "no language"
        meta = f"{language} · ★{stars}" if stars else language
        more_bits.append(f"[{repo['name']}]({repo['html_url']}) ({meta})")
    more_repos = (
        "<sub>**Also public on this profile, just not featured above:** "
        + " · ".join(more_bits) + "</sub>"
    ) if more_bits else ""

    updated = (
        f"<sub>Scheduled to refresh **daily at 00:17 UTC** by "
        f"[GitHub Actions](https://github.com/{USER}/{USER}/actions/workflows/update-profile.yml). "
        f"Last successful data snapshot: **{now.strftime('%d %b %Y, %H:%M UTC')}**. "
        f"On GitHub since {user.get('created_at', '')[:4]} · "
        f"{user['public_repos']} public repositories (including forks and this profile). "
        f"Charts use GitHub REST + GraphQL; no third-party chart service.</sub>"
    )

    blocks = {
        "VISUAL_PULSE": visual_pulse,
        "CONTRIBUTION_GRAPH": contribution_graph,
        "INSIGHT_CHARTS": insight_charts,
        "OSS_SNAPSHOT": oss_snapshot,
        "OSS_DETAILS": oss_details,
        "PROJECT_CARDS": project_cards,
        "OSS_SUMMARY": summary,
        "OSS_TABLE": oss_table,
        "RECENT_PRS": recent,
        "PROJECTS": projects,
        "MORE_REPOS": more_repos,
        "EXPERIENCE_OSS": experience_oss,
        "UPDATED": updated,
    }
    return blocks, assets, snapshot


def replace_blocks(readme: str, blocks: dict[str, str]) -> str:
    """Require every marker exactly once; never silently skip a broken chart."""
    new = readme
    for name, content in blocks.items():
        pattern = re.compile(
            rf"(<!-- DYNAMIC:{re.escape(name)}:START -->)\n?.*?\n?(<!-- DYNAMIC:{re.escape(name)}:END -->)",
            re.DOTALL,
        )
        if len(pattern.findall(new)) != 1:
            raise ValueError(f"Expected exactly one pair of markers for {name}")
        new = pattern.sub(lambda m: f"{m.group(1)}\n{content}\n{m.group(2)}", new)
    return new


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as temp:
            temp_name = Path(temp.name)
            temp.write(content)
            temp.flush()
            os.fsync(temp.fileno())
        os.replace(temp_name, path)
    finally:
        if temp_name and temp_name.exists():
            temp_name.unlink()


def publish_transaction(files: dict[Path, bytes]) -> list[Path]:
    """Stage every file before replacing any; roll back replacements on failure."""
    changed = {path: content for path, content in files.items()
               if not path.exists() or path.read_bytes() != content}
    if not changed:
        return []
    previous = {path: path.read_bytes() if path.exists() else None for path in changed}
    staged = {}
    replaced = []
    try:
        for path, content in changed.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as temp:
                staged[path] = Path(temp.name)
                temp.write(content)
                temp.flush()
                os.fsync(temp.fileno())
        for path, temp in staged.items():
            os.replace(temp, path)
            replaced.append(path)
    except Exception:
        for path in reversed(replaced):
            if previous[path] is None:
                path.unlink(missing_ok=True)
            else:
                atomic_write(path, previous[path])
        raise
    finally:
        for temp in staged.values():
            if temp.exists():
                temp.unlink()
    return list(changed)


def main() -> int:
    if not README_PATH.exists():
        print(f"README not found at {README_PATH}", file=sys.stderr)
        return 1
    try:
        readme = README_PATH.read_text(encoding="utf-8")
        history_path = ROOT / "data/profile-history.json"
        history = json.loads(history_path.read_text(encoding="utf-8")) if history_path.exists() else None
        blocks, assets, snapshot = build_profile()
        new = replace_blocks(readme, blocks)
        history = visuals.update_history(history, snapshot)
        files = {ROOT / path: content for path, content in assets.items()}
        files[README_PATH] = new.encode("utf-8")
        files[ROOT / "data/profile-snapshot.json"] = (json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        files[history_path] = (json.dumps(history, indent=2) + "\n").encode("utf-8")
        changed = publish_transaction(files)
    except Exception as exc:
        # Authentication values are never included in exception messages or logs.
        print(f"Refresh failed ({type(exc).__name__}: {exc}); previous profile preserved.", file=sys.stderr)
        return 1
    if changed:
        print(f"Profile refreshed: {len(changed)} files changed; {len(snapshot['contributions']['days'])} real calendar days.")
    else:
        print("No changes - profile already up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
