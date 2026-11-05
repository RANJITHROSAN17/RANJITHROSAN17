#!/usr/bin/env python3
"""
Auto-update the GitHub profile README (RANJITHROSAN17/RANJITHROSAN17).

Runs every 2 hours via .github/workflows/update-profile.yml using only the
Python standard library (no pip installs). It refreshes, from the live GitHub
API:

  * DYNAMIC:IMPACT_BADGES  - hero counters (external PRs / merged / review)
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
  * DYNAMIC:STATS_CARDS    - self-computed account stats and top languages,
                             with forked repos excluded and no dependency on
                             a third-party stats-card service

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
# Repositories in these organisations are my own projects, not upstream
# open-source contributions. Keep the former org name as well so old links
# and searches cannot reintroduce self-merged PRs after the rename.
SELF_ORGS = ("Quasynvo", "pinchfoundry")
SELF_OWNERS = {USER.lower()} | {org.lower() for org in SELF_ORGS}
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
        "repo": "Quasynvo/Quasnooze",
        "name": "Quasnooze",
        "demo": "https://quasynvo.github.io/Quasnooze/",
        "highlight": "A private, local-first personal AI voice assistant for the browser, "
                     "Windows, Telegram, Discord, Slack and WhatsApp - Ollama + MCP tools, "
                     "Fluid Motion audio visuals and permission-first controls",
        "stack": "Node.js - Ollama - MCP - PWA - zero runtime deps",
    },
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
        "repo": "warden",
        "name": "Grace",
        "demo": "",
        "highlight": "Agentic-payments judge - scores an agent's payment against the "
                     "business's own PayPal payment history and cites the payments it "
                     "reasoned from (PayPal AI Hackathon, sandbox only)",
        "stack": "Python - PayPal Orders API - payment graph",
    },
    {
        "repo": "Kannada-Digital",
        "name": "Kannada Saathi",
        "demo": "https://ranjithrosan17.github.io/Kannada-Digital/",
        "highlight": "Offline-first, installable Kannada companion for everyday situations "
                     "- 111 reviewed phrases with audio, strict TypeScript, 133 tests, "
                     "0 audit vulnerabilities (Kannada Digital Innovation Hackathon 2026)",
        "stack": "React - TypeScript - Vite - PWA",
    },
    {
        "repo": "dsa-mastery-plan-2026",
        "name": "DSA Mastery Plan 2026",
        "demo": "https://ranjithrosan17.github.io/dsa-mastery-plan-2026/",
        "highlight": "150-day, pattern-first DSA roadmap - 466 verified free LeetCode "
                     "problems, 33 pattern playbooks, browser-only progress tracker",
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


def is_external_pr(pr: dict) -> bool:
    """Return False for PRs in my user account or personal organisations."""
    owner = repo_of(pr).split("/", 1)[0].lower()
    return owner not in SELF_OWNERS


def is_merged(pr: dict) -> bool:
    return bool(pr.get("pull_request", {}).get("merged_at"))


def fmt_stars(n: int) -> str:
    if n >= 1000:
        return f"{n / 1000:.0f}k" if n >= 10000 else f"{n / 1000:.1f}k"
    return str(n)


def esc(text: str) -> str:
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def search_url(extra: str, external_only: bool = False) -> str:
    # Proof links must apply exactly the same ownership exclusions as the
    # API-side counters: both my user account and my personal organisations.
    suffix = ""
    if external_only:
        suffix = f" -user:{USER}" + "".join(f" -org:{org}" for org in SELF_ORGS)
    q = urllib.parse.quote(f"type:pr author:{USER} {extra}{suffix}".strip())
    return f"https://github.com/search?q={q}&type=pullrequests"


def summarise_languages(
    language_maps: list[dict[str, int]], limit: int = 8
) -> list[tuple[str, int, float]]:
    """Combine GitHub language-byte maps and return sorted language shares."""
    totals: dict[str, int] = defaultdict(int)
    for languages in language_maps:
        for language, byte_count in languages.items():
            totals[language] += byte_count
    total_bytes = sum(totals.values())
    if not total_bytes:
        return []
    ranked = sorted(totals.items(), key=lambda item: (-item[1], item[0].lower()))
    return [
        (language, byte_count, byte_count * 100 / total_bytes)
        for language, byte_count in ranked[:limit]
    ]


# ---------------------------------------------------------------- blocks
def build_blocks() -> dict[str, str]:
    user = api_get(f"https://api.github.com/users/{USER}")
    own_repos = api_get_all(f"https://api.github.com/users/{USER}/repos?type=owner&sort=updated")
    own_by_name = {r["name"].lower(): r for r in own_repos}

    # Featured projects normally belong to the profile user. Owner-qualified
    # entries also support projects in personal orgs (for example Quasnooze).
    featured_meta: list[tuple[dict, dict]] = []
    for fp in FEATURED_PROJECTS:
        if "/" in fp["repo"]:
            meta = api_get(f"https://api.github.com/repos/{fp['repo']}")
        else:
            meta = own_by_name.get(fp["repo"].lower())
        if meta:
            featured_meta.append((fp, meta))

    prs_all = search_prs()
    external = [p for p in prs_all if is_external_pr(p)]
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

    # --- hero impact badges (numbers regenerate every two hours) ---
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

    # Subtract every rendered row (including auto-discovered rows), otherwise
    # those PRs would be counted a second time in the "smaller projects" tail.
    other_merged = len(ext_merged) - sum(
        stats["merged"] for repo, stats in by_repo.items()
        if repo.lower() in featured_keys
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
    for fp, meta in featured_meta:
        name = f"**[{fp['name']}]({meta['html_url']})**"
        if fp.get("demo"):
            name += f" · [live demo]({fp['demo']})"
        proj_rows.append(
            f"| {name} | {esc(fp['highlight'])} | {esc(fp['stack'])} "
            f"| {meta.get('stargazers_count', 0)} | {esc(meta.get('language') or '·')} "
            f"| {meta.get('updated_at', '')[:10]} |"
        )
    projects = "\n".join(proj_rows)

    # --- visual project cards (GitHub's own OpenGraph images, no widget host) ---
    cards = []
    for fp, meta in featured_meta:
        full_name = meta.get("full_name") or f"{USER}/{meta['name']}"
        image = f"https://opengraph.githubassets.com/1/{full_name}"
        cards.append(
            f'<a href="{meta["html_url"]}">'
            f'<img width="49%" alt="{esc(fp["name"])} repository card" src="{image}" />'
            f'</a>'
        )
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

    # --- self-computed stats (no third-party card service to pause or fail) ---
    original_repos = [r for r in own_repos if not r.get("fork")]
    language_maps = [
        api_get(repo["languages_url"])
        for repo in original_repos if repo.get("languages_url")
    ]
    languages = summarise_languages(language_maps)
    if languages:
        language_rows = [
            "| Language | Share of code |",
            "|---|---:|",
        ]
        for language, _byte_count, share in languages:
            filled = round(share / 10)
            bar = "█" * filled + "░" * (10 - filled)
            share_text = "&lt;0.1%" if share < 0.1 else f"{share:.1f}%"
            language_rows.append(f"| {esc(language)} | `{bar}` {share_text} |")
        language_table = "\n".join(language_rows)
    else:
        language_table = "<sub>No language data is available yet.</sub>"

    total_stars = sum(r.get("stargazers_count", 0) for r in original_repos)
    stats_cards = f"""<table align="center">
  <tr>
    <th>Public repos</th>
    <th>Original public repos</th>
    <th>Stars on original repos</th>
    <th>Followers</th>
  </tr>
  <tr align="center">
    <td><strong>{user.get('public_repos', len(own_repos))}</strong></td>
    <td><strong>{len(original_repos)}</strong></td>
    <td><strong>{total_stars}</strong></td>
    <td><strong>{user.get('followers', 0)}</strong></td>
  </tr>
</table>

**Top languages in my original public repositories**

{language_table}"""

    updated = (
        f"<sub>🤖 This profile is **auto-updated every 2 hours** by "
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
        "MORE_REPOS": more_repos,
        "EXPERIENCE_OSS": experience_oss,
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
