#!/usr/bin/env python3
"""
Auto-update the GitHub profile README (RANJITHROSAN17/RANJITHROSAN17).

Runs daily via .github/workflows/update-profile.yml using only the Python
standard library (no pip installs). It refreshes, from the live GitHub API:

  * DYNAMIC:OSS_SUMMARY   - total / merged / in-review PR counters
  * DYNAMIC:OSS_TABLE     - contributions grouped by company / organisation
  * DYNAMIC:RECENT_PRS    - latest merged & in-review pull requests
  * DYNAMIC:PROJECTS      - featured own projects with live stars/language
  * DYNAMIC:STATS_CARDS   - stats cards with forked repos excluded from
                            the "top languages" calculation (important once
                            you start forking big upstreams like vscode!)

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

import json
import os
import re
import sys
import urllib.parse
import urllib.request
import urllib.error
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

USER = os.environ.get("GH_USERNAME", "RANJITHROSAN17")
TOKEN = (
    os.environ.get("GITHUB_TOKEN")
    or os.environ.get("GH_TOKEN")
    or os.environ.get("PROFILE_TOKEN")
    or ""
)
README_PATH = Path(__file__).resolve().parents[2] / "README.md"
if len(sys.argv) > 1:  # allow: update_profile.py /path/to/README.md
    README_PATH = Path(sys.argv[1])

IST = timezone(timedelta(hours=5, minutes=30))

# --------------------------------------------------------------- curation
# Featured organisations/projects (order = display order). "focus" is a
# short, factual description of what the PRs touch - edit it as work evolves.
CURATED = [
    {
        "repo": "google-research/google-research",
        "org": "Google Research",
        "focus": "ML research maintenance - snerg Flax->Optax migration, uflow "
                 "multi-dataset training, summae & distributed_shampoo fixes",
    },
    {
        "repo": "microsoft/vscode",
        "org": "Microsoft",
        "focus": "VS Code Git extension safety - literal-pathspec discard, "
                 "scp-like clone folder names",
    },
    {
        "repo": "openai/openai-cookbook",
        "org": "OpenAI",
        "focus": "Data-analyst cookbook - schema-scoped table-context lookups",
    },
    {
        "repo": "NationalSecurityAgency/ghidra",
        "org": "NSA - Ghidra",
        "focus": "Reverse-engineering framework - AVR8 12-bit PC variant, "
                 "PackedDatabase unpack hardening, .eh_frame analysis",
    },
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
        "repo": "NousResearch/hermes-agent",
        "org": "Nous Research",
        "focus": "Hermes Agent - plugin Settings config_source, managed-worker "
                 "job scoping, desktop typecheck heap",
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
        "repo": "CosturaAI/costura",
        "org": "Costura AI",
        "focus": "AI spend attribution - invalid snooze-input test coverage",
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
# filled in live; "highlight" is yours to edit.
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
        "repo": "career-forge",
        "name": "Career Forge",
        "demo": "",
        "highlight": "Local-first resume vs. job-description studio - transparent ATS "
                     "score, keyword-gap radar, XYZ bullet rewrites, cover letters, "
                     "STAR interview prep",
        "stack": "Python - PyInstaller - GitHub Actions",
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
    {
        "repo": "musicgenre",
        "name": "Music Genre Classification",
        "demo": "",
        "highlight": "GTZAN genre classifier - librosa audio features + Keras MLP, "
                     "88.7% test accuracy on 3-second clips",
        "stack": "librosa - TensorFlow/Keras - scikit-learn",
    },
    {
        "repo": "dsa-mastery-plan-2026",
        "name": "DSA Mastery Plan 2026",
        "demo": "https://ranjithrosan17.github.io/dsa-mastery-plan-2026/",
        "highlight": "150-day, pattern-first DSA roadmap - 466 verified free LeetCode "
                     "problems, 33 pattern playbooks, browser-only progress tracker",
        "stack": "vanilla JS - GitHub Pages",
    },
]


# ------------------------------------------------------------- GitHub API
def api_get(url: str):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{USER}-profile-updater",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def api_get_all(url: str, max_pages: int = 10):
    """Follow pagination for both list endpoints and search endpoints."""
    out = []
    for page in range(1, max_pages + 1):
        sep = "&" if "?" in url else "?"
        data = api_get(f"{url}{sep}per_page=100&page={page}")
        if isinstance(data, dict) and "items" in data:
            out.extend(data["items"])
            if len(out) >= data.get("total_count", len(out)):
                break
            if not data["items"]:
                break
        elif isinstance(data, list):
            out.extend(data)
            if len(data) < 100:
                break
        else:
            return data
    return out


def search_prs(extra: str = "") -> list[dict]:
    q = urllib.parse.quote(f"type:pr author:{USER} {extra}".strip())
    items = api_get_all(f"https://api.github.com/search/issues?q={q}&sort=updated&order=desc")
    # Deduplicate across page boundaries if a PR updates mid-pagination.
    return list({p["id"]: p for p in items}.values())


def repo_of(pr: dict) -> str:
    # repository_url: https://api.github.com/repos/OWNER/REPO
    return pr["repository_url"].split("/repos/", 1)[-1]


def is_merged(pr: dict) -> bool:
    return bool(pr.get("pull_request", {}).get("merged_at"))


def fmt_stars(n: int) -> str:
    if n >= 1000:
        return f"{n / 1000:.0f}k" if n >= 10000 else f"{n / 1000:.1f}k"
    return str(n)


def esc(text: str) -> str:
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def search_url(extra: str, external_only: bool = False) -> str:
    # external_only adds "-user:<me>" so the link excludes PRs in my own
    # repositories (self-merges must never pad the open-source numbers).
    suffix = f" -user:{USER}" if external_only else ""
    q = urllib.parse.quote(f"type:pr author:{USER} {extra}{suffix}".strip())
    return f"https://github.com/search?q={q}&type=pullrequests"


# ---------------------------------------------------------------- blocks
def build_blocks() -> dict[str, str]:
    user = api_get(f"https://api.github.com/users/{USER}")
    own_repos = api_get_all(f"https://api.github.com/users/{USER}/repos?type=owner&sort=updated")
    own_by_name = {r["name"].lower(): r for r in own_repos}

    prs_all = search_prs()
    merged = [p for p in prs_all if is_merged(p)]
    open_prs = [p for p in prs_all if p.get("state") == "open"]
    external = [p for p in prs_all if repo_of(p).split("/")[0].lower() != USER.lower()]
    ext_merged = [p for p in external if is_merged(p)]
    ext_open = [p for p in external if p.get("state") == "open"]
    external_repos = sorted({repo_of(p) for p in external}, key=str.lower)

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
        try:
            meta = api_get(f"https://api.github.com/repos/{c['repo']}")
            stars[c["repo"].lower()] = meta.get("stargazers_count", 0)
        except Exception as e:  # keep going if one lookup fails
            print(f"warn: star lookup failed for {c['repo']}: {e}", file=sys.stderr)

    now_ist = datetime.now(IST).strftime("%d %b %Y")

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

    # --- hero impact badges (numbers regenerate daily) ---
    impact_badges = (
        '<p align="center">\n'
        f'  <a href="{search_url("", external_only=True)}"><img alt="{len(external)} external pull requests" src="https://img.shields.io/badge/External_PRs-{len(external)}-1f6feb?style=flat" /></a>\n'
        f'  <a href="{search_url("is:merged", external_only=True)}"><img alt="{len(ext_merged)} PRs merged upstream" src="https://img.shields.io/badge/Merged_upstream-{len(ext_merged)}-8250df?style=flat" /></a>\n'
        f'  <a href="{search_url("is:open", external_only=True)}"><img alt="{len(ext_open)} PRs in review" src="https://img.shields.io/badge/In_review-{len(ext_open)}-1f883d?style=flat" /></a>\n'
        f'  <img alt="{len(external_repos)} external projects" src="https://img.shields.io/badge/External_projects-{len(external_repos)}-555555?style=flat" />\n'
        '</p>'
    )

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
        latest = sorted(stats["prs"], key=lambda p: p["updated_at"], reverse=True)[0]
        latest_no = latest["html_url"].rstrip("/").split("/")[-1]
        state_icon = "🟣" if is_merged(latest) else "🟢"
        owner = repo.split("/")[0]
        avatar = (f'<img src="https://github.com/{owner}.png?size=40" '
                  f'width="18" height="18" alt="{owner} logo" /> ')
        if stats["merged"]:
            snapshot_merged.append(f"[{esc(org)}](https://github.com/{repo})")
        if stats["open"]:
            snapshot_review.append(f"[{esc(org)}](https://github.com/{repo})")
        prs_sorted = sorted(stats["prs"], key=lambda p: p["updated_at"], reverse=True)
        prs_sorted = sorted(prs_sorted, key=is_merged, reverse=True)  # merged first
        bullets = [
            f"- {'🟣 Merged' if is_merged(pr) else '🟢 In review'} · {pr['updated_at'][:10]} · "
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
        by_repo.get(c["repo"], {"merged": 0})["merged"] if c["repo"] in by_repo else
        next((v["merged"] for k, v in by_repo.items() if k.lower() == c["repo"].lower()), 0)
        for c in CURATED
    )
    oss_table = "\n".join(rows)
    if other_merged > 0:
        oss_table += (
            f"\n\n<sub>Plus {other_merged} earlier merged PRs in smaller projects - "
            f"[see every upstream-merged PR]({search_url('is:merged', external_only=True)}).</sub>"
        )

    merged_line = " · ".join(snapshot_merged)
    if other_merged > 0:
        merged_line += f" · +{other_merged} earlier in smaller projects"
    oss_snapshot = (
        f"**🟣 Merged upstream in:** {merged_line}\n\n"
        f"**🟢 Currently in review at:** {' · '.join(snapshot_review)}"
    )
    oss_details = (
        "<details>\n<summary><strong>📂 Expand — every featured PR, "
        "grouped by organisation (auto-updated)</strong></summary>\n\n"
        + "\n\n".join(detail_sections)
        + "\n\n</details>"
    )

    # --- recent PRs ---
    recent_src = [
        p for p in external
        if is_merged(p) or p.get("state") == "open"
    ]
    recent_src.sort(key=lambda p: p["updated_at"], reverse=True)
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
        date = pr["updated_at"][:10]
        recent_lines.append(
            f"- {icon} · {date} · [{esc(pr['title'])}]({pr['html_url']}) "
            f"in [{repo_of(pr)}](https://github.com/{repo_of(pr)})"
        )
    recent = "\n".join(recent_lines)

    # --- featured projects ---
    proj_rows = [
        "| Project | What it is | Stack | ★ | Language | Updated |",
        "|---|---|---|---:|---|---|",
    ]
    for fp in FEATURED_PROJECTS:
        meta = own_by_name.get(fp["repo"].lower())
        if not meta:
            continue
        name = f"**[{fp['name']}]({meta['html_url']})**"
        if fp.get("demo"):
            name += f" · [live demo]({fp['demo']})"
        proj_rows.append(
            f"| {name} | {esc(fp['highlight'])} | {esc(fp['stack'])} "
            f"| {meta.get('stargazers_count', 0)} | {esc(meta.get('language') or '·')} "
            f"| {meta.get('updated_at', '')[:10]} |"
        )
    projects = "\n".join(proj_rows)

    # --- visual project cards ---
    cards = []
    for fp in FEATURED_PROJECTS:
        meta = own_by_name.get(fp["repo"].lower())
        if not meta:
            continue
        rn = meta["name"]
        base = (f"https://github-readme-stats.vercel.app/api/pin/?username={USER}"
                f"&repo={rn}&hide_border=true&cache_seconds=1800")
        cards.append(
            f'<a href="{meta["html_url"]}"><picture>'
            f'<source media="(prefers-color-scheme: dark)" srcset="{base}&theme=github_dark" />'
            f'<img width="49%" alt="{esc(fp["name"])} repository card" src="{base}&theme=default" />'
            f'</picture></a>'
        )
    project_cards = '<p align="center">\n' + "\n".join(cards) + "\n</p>"

    # --- stats cards (exclude forks so top-languages reflects *my* code) ---
    fork_names = [r["name"] for r in own_repos if r.get("fork")]
    exclude = urllib.parse.quote(",".join(fork_names))
    u = USER
    stats_cards = f"""<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github-readme-stats.vercel.app/api?username={u}&show_icons=true&include_all_commits=true&hide_border=true&theme=github_dark&cache_seconds=1800" />
    <img height="170" alt="GitHub stats for {u}" src="https://github-readme-stats.vercel.app/api?username={u}&show_icons=true&include_all_commits=true&hide_border=true&theme=default&cache_seconds=1800" />
  </picture>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github-readme-stats.vercel.app/api/top-langs/?username={u}&layout=compact&langs_count=8&hide_border=true&theme=github_dark&exclude_repo={exclude}&cache_seconds=1800" />
    <img height="170" alt="Most used languages (my repos only, forks excluded)" src="https://github-readme-stats.vercel.app/api/top-langs/?username={u}&layout=compact&langs_count=8&hide_border=true&theme=default&exclude_repo={exclude}&cache_seconds=1800" />
  </picture>
</p>
<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://streak-stats.demolab.com?user={u}&theme=github-dark-blue&hide_border=true" />
    <img height="170" alt="Contribution streak" src="https://streak-stats.demolab.com?user={u}&theme=default&hide_border=true" />
  </picture>
</p>"""

    updated = (
        f"<sub>🤖 This profile is **auto-updated daily** by "
        f"[GitHub Actions](https://github.com/{USER}/{USER}/actions/workflows/update-profile.yml) - "
        f"last run **{datetime.now(IST).strftime('%d %b %Y')}**. "
        f"On GitHub since {user.get('created_at', '')[:4]} · "
        f"{user.get('public_repos')} public repos · {user.get('followers')} followers.</sub>"
    )

    return {
        "IMPACT_BADGES": impact_badges,
        "OSS_SNAPSHOT": oss_snapshot,
        "OSS_DETAILS": oss_details,
        "PROJECT_CARDS": project_cards,
        "OSS_SUMMARY": summary,
        "OSS_TABLE": oss_table,
        "RECENT_PRS": recent,
        "PROJECTS": projects,
        "STATS_CARDS": stats_cards,
        "UPDATED": updated,
    }


def main() -> int:
    if not README_PATH.exists():
        print(f"README not found at {README_PATH}", file=sys.stderr)
        return 1
    readme = README_PATH.read_text(encoding="utf-8")
    try:
        blocks = build_blocks()
    except urllib.error.URLError as e:
        print(f"GitHub API error - leaving README untouched: {e}", file=sys.stderr)
        return 1

    new = readme
    for name, content in blocks.items():
        pattern = re.compile(
            rf"(<!-- DYNAMIC:{name}:START -->)\n?.*?\n?(<!-- DYNAMIC:{name}:END -->)",
            re.DOTALL,
        )
        if not pattern.search(new):
            print(f"warn: markers for {name} not found, skipping", file=sys.stderr)
            continue
        new = pattern.sub(lambda m: f"{m.group(1)}\n{content}\n{m.group(2)}", new)

    if new != readme:
        README_PATH.write_text(new, encoding="utf-8")
        print("README updated ✅")
    else:
        print("No changes - profile already up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
