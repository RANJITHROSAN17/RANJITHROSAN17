#!/usr/bin/env python3
"""Deterministic, dependency-free SVG charts for the profile README.

All values come from a validated GitHub API snapshot. No random activity,
placeholder metrics, remote fonts, scripts, or third-party chart services.
Each chart is rendered as a separate light/dark SVG for GitHub's <picture>.
"""
from __future__ import annotations

import calendar
import re
import textwrap
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from xml.sax.saxutils import escape

THEMES = {
    "dark": {
        "bg": "#0B1220", "panel": "#111D31", "border": "#263750",
        "text": "#F2F6FC", "muted": "#A5B4CB", "faint": "#7F91AB",
        "teal": "#2DD4BF", "violet": "#A78BFA", "amber": "#FBBF24",
        "blue": "#60A5FA", "rose": "#FB7185", "track": "#203049",
        "heat": ["#172338", "#123D43", "#146C69", "#16A394", "#5EEAD4"],
    },
    "light": {
        "bg": "#F8FAFC", "panel": "#FFFFFF", "border": "#DCE5EF",
        "text": "#102039", "muted": "#52657D", "faint": "#64748B",
        "teal": "#0F766E", "violet": "#7C3AED", "amber": "#B45309",
        "blue": "#2563EB", "rose": "#BE123C", "track": "#E8EEF5",
        "heat": ["#E8EEF5", "#CCFBF1", "#99F6E4", "#2DD4BF", "#0F766E"],
    },
}
FONT = "Inter, Segoe UI, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Consolas, monospace"
LANGUAGE_COLORS = {
    "Python": "#3572A5", "TypeScript": "#3178C6", "JavaScript": "#F1E05A",
    "Jupyter Notebook": "#DA5B0B", "HTML": "#E34C26", "CSS": "#A074C4",
    "Rust": "#DEA584", "Shell": "#89E051", "C++": "#F34B7D",
    "Go": "#00ADD8", "Java": "#B07219", "Other": "#94A3B8",
}
LEVELS = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]


def xml(value: object) -> str:
    return escape(str(value), {'"': "&quot;", "'": "&apos;"})


def short(value: str, length: int) -> str:
    value = " ".join(str(value).split())
    return value if len(value) <= length else value[:length - 1].rstrip() + "…"


def number(value: int) -> str:
    return f"{value:,}"


def human_bytes(value: int) -> str:
    if value >= 1024 ** 2:
        return f"{value / 1024 ** 2:.1f} MiB"
    if value >= 1024:
        return f"{value / 1024:.1f} KiB"
    return f"{value} B"


def text(x: float, y: float, value: object, c: dict, size: float = 14,
         color: str = "text", weight: int = 400, anchor: str = "start",
         mono: bool = False, spacing: float = 0) -> str:
    return (
        f'<text x="{x:.2f}" y="{y:.2f}" fill="{c[color]}" font-size="{size}" '
        f'font-family="{MONO if mono else FONT}" font-weight="{weight}" '
        f'text-anchor="{anchor}" letter-spacing="{spacing}">{xml(value)}</text>'
    )


def rect(x: float, y: float, w: float, h: float, fill: str, rx: float = 0,
         stroke: str | None = None, opacity: float = 1) -> str:
    border = f' stroke="{stroke}"' if stroke else ""
    return (f'<rect x="{x:.2f}" y="{y:.2f}" width="{max(0, w):.2f}" '
            f'height="{max(0, h):.2f}" rx="{rx}" fill="{fill}"'
            f'{border} opacity="{opacity}"/>')


def line(x1: float, y1: float, x2: float, y2: float, color: str) -> str:
    return f'<path d="M{x1:.2f} {y1:.2f}H{x2:.2f}" fill="none" stroke="{color}"/>' if y1 == y2 else (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}"/>'
    )


def dot(x: float, y: float, color: str, r: float = 4) -> str:
    return f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r}" fill="{color}"/>'


def document(width: int, height: int, title: str, description: str,
             body: str, theme: str) -> str:
    c = THEMES[theme]
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">'
        f'<title id="title">{xml(title)}</title><desc id="desc">{xml(description)}</desc>'
        f'{rect(0.5, 0.5, width - 1, height - 1, c["bg"], 18, c["border"])}'
        f'{body}</svg>\n'
    )


def header(c: dict, eyebrow: str, title: str, subtitle: str, width: int = 580) -> str:
    return (text(24, 30, eyebrow, c, 10, "teal", 700, mono=True, spacing=1.5)
            + text(24, 60, title, c, 23, weight=700)
            + text(24, 83, subtitle, c, 12, "muted"))


def pulse(snapshot: dict, theme: str) -> str:
    c, m = THEMES[theme], snapshot["metrics"]
    landed = snapshot.get("merge_months", [])
    description = (
        f'Public GitHub snapshot at {snapshot["as_of"]}: {m["merged_prs"]} external PRs merged, '
        f'{m["open_prs"]} open, {m["merged_projects"]} upstream projects with merged work, '
        f'{m["original_stars"]} stars across {m["original_repos"]} original repositories, '
        f'{m["followers"]} followers. Actual monthly upstream merges: '
        + ", ".join(f'{p["month"]}: {p["count"]}' for p in landed) + "."
    )
    body = text(32, 32, "GITHUB / LIVE PROFILE SIGNAL", c, 11, "teal", 700, mono=True, spacing=1.4)
    body += text(1168, 32, f'AS OF {snapshot["as_of"]} · UTC', c, 11, "muted", anchor="end", mono=True)
    body += text(32, 65, "Proof of work, not placeholder numbers.", c, 25, weight=700)
    tiles = [
        ("MERGED UPSTREAM", m["merged_prs"], "Confirmed by merged_at", "violet"),
        ("IN REVIEW", m["open_prs"], "Open, not yet merged", "teal"),
        ("PROJECTS LANDED", m["merged_projects"], "Distinct upstream repositories", "blue"),
        ("REPOSITORY STARS", m["original_stars"], f'{m["original_repos"]} original public repos', "amber"),
        ("FOLLOWERS", m["followers"], "Public GitHub community", "rose"),
    ]
    for i, (label, value, detail, color) in enumerate(tiles):
        x = 32 + i * 230
        body += rect(x, 86, 214, 103, c["panel"], 12, c["border"])
        body += rect(x + 14, 99, 22, 3, c[color], 1.5)
        body += text(x + 14, 120, label, c, 10, "muted", 700, spacing=0.7)
        body += text(x + 14, 158, number(value), c, 34, weight=750)
        body += text(x + 14, 177, detail, c, 10.5, "muted")
    body += text(32, 218, "UPSTREAM MERGES", c, 10, "muted", 700, mono=True)
    body += text(32, 235, "Last 12 calendar months", c, 10, "faint")
    maximum = max([p["count"] for p in landed] + [1])
    for i, point in enumerate(landed):
        x = 278 + i * 72
        height = 30 * point["count"] / maximum
        body += f'<g><title>{xml(point["month"])}: {point["count"]} upstream merges</title>'
        body += rect(x, 210, 42, 30, c["track"], 4)
        if height:
            body += rect(x, 240 - height, 42, height, c["violet"], 4)
            body += text(x + 21, 205, point["count"], c, 10, "muted", anchor="middle")
        else:
            body += text(x + 21, 205, "0", c, 9, "faint", anchor="middle")
        body += '</g>'
        month = calendar.month_abbr[int(point["month"][5:7])]
        body += text(x + 21, 253, month, c, 9, "muted", anchor="middle", mono=True)
    return document(1200, 270, "Ranjith Rosan — live GitHub impact", description, body, theme)


def upstream(snapshot: dict, theme: str) -> str:
    c, m = THEMES[theme], snapshot["metrics"]
    repos = snapshot["upstream_repos"][:5]
    body = header(c, "01 / OPEN SOURCE", "Upstream outcomes",
                  f'{m["external_prs"]} PRs · {m["external_projects"]} external projects')
    total = m["external_prs"]
    x = 24.0
    for key, color in [("merged_prs", c["violet"]), ("open_prs", c["teal"]),
                       ("closed_unmerged_prs", c["track"])]:
        width = 532 * m[key] / total if total else 0
        if width:
            body += rect(x, 102, width, 10, color, 3)
            x += width
    for x, label, key, color in [
        (24, "Merged", "merged_prs", c["violet"]),
        (190, "In review", "open_prs", c["teal"]),
        (365, "Closed unmerged", "closed_unmerged_prs", c["faint"]),
    ]:
        body += dot(x + 4, 132, color)
        body += text(x + 15, 136, f'{label} · {m[key]}', c, 11, "muted")
    body += text(24, 166, "MOST ACTIVE PROJECTS", c, 10, "muted", 700, mono=True, spacing=0.7)
    body += text(556, 166, "MERGED / OPEN", c, 9, "faint", anchor="end", mono=True)
    maximum = max([r["merged"] + r["open"] for r in repos] + [1])
    for i, repo in enumerate(repos):
        y = 190 + i * 29
        body += text(24, y, short(repo["repo"], 30), c, 11.5)
        body += rect(240, y - 9, 238, 9, c["track"], 3)
        merged_w = 238 * repo["merged"] / maximum
        open_w = 238 * repo["open"] / maximum
        if merged_w:
            body += rect(240, y - 9, merged_w, 9, c["violet"], 3)
        if open_w:
            body += rect(240 + merged_w, y - 9, open_w, 9, c["teal"], 3)
        body += text(556, y, f'{repo["merged"]} / {repo["open"]}', c, 11, "muted", anchor="end", mono=True)
    if not repos:
        body += text(24, 220, "No merged or open external PRs in this snapshot.", c, 13, "muted")
    body += text(24, 342, "Personal accounts and organisations excluded. Open ≠ merged.", c, 10, "faint")
    desc = (f'{m["merged_prs"]} merged, {m["open_prs"]} open and {m["closed_unmerged_prs"]} '
            f'closed-unmerged external pull requests. Top repositories: '
            + "; ".join(f'{r["repo"]}: {r["merged"]} merged, {r["open"]} open' for r in repos))
    return document(580, 360, "Upstream pull-request outcomes", desc, body, theme)


def languages(snapshot: dict, theme: str) -> str:
    c, data = THEMES[theme], snapshot["languages"]
    items, total = data["items"], data["total_bytes"]
    rows = items[:5]
    if len(items) > 5:
        rows = rows + [{"name": "Other", "bytes": sum(i["bytes"] for i in items[5:])}]
    body = header(c, "02 / CODE FOOTPRINT", "Repository language mix",
                  f'{data["repositories"]} original repos · {human_bytes(total)} detected')
    for i, item in enumerate(rows):
        y = 116 + i * 32
        percent = 100 * item["bytes"] / total if total else 0
        color = LANGUAGE_COLORS.get(item["name"], LANGUAGE_COLORS["Other"])
        body += dot(28, y - 4, color)
        body += text(40, y, item["name"], c, 12.5, weight=600)
        body += text(440, y, human_bytes(item["bytes"]), c, 10.5, "muted", anchor="end")
        body += text(556, y, f"{percent:.1f}%", c, 12, weight=700, anchor="end", mono=True)
        body += rect(24, y + 7, 532, 5, c["track"], 2.5)
        if percent:
            body += rect(24, y + 7, 532 * percent / 100, 5, color, 2.5)
    if not total:
        body += text(24, 180, "GitHub has not detected language bytes in these repositories.", c, 13, "muted")
    body += text(24, 326, "GitHub byte share, not proficiency. Notebooks included.", c, 10.5, "faint")
    body += text(24, 343, "Forks, archived repositories and the profile README excluded.", c, 10.5, "faint")
    desc = "Language bytes aggregated from original, non-archived public repositories, excluding forks and the profile repository. "
    desc += "; ".join(f'{i["name"]}: {i["bytes"]} bytes' for i in rows)
    return document(580, 360, "Repository language mix", desc, body, theme)


def contribution_calendar(snapshot: dict, theme: str) -> str:
    c, m, data = THEMES[theme], snapshot["metrics"], snapshot["contributions"]
    first = date.fromisoformat(data["from"])
    last = date.fromisoformat(data["to"])
    weeks = ((last - first).days + first.weekday() + 1 + 6) // 7
    # Monday-first display; GitHub supplies Sunday-first weeks.
    offset = (first.weekday() + 1) % 7
    body = text(32, 32, "03 / CONSISTENCY", c, 10, "teal", 700, mono=True, spacing=1.5)
    body += text(32, 64, "A year of building, one day at a time.", c, 24, weight=700)
    body += text(32, 86, f'{data["from"]} → {data["to"]} · public GitHub contribution calendar', c, 11.5, "muted")
    month_seen = set()
    for day in data["days"]:
        d = date.fromisoformat(day["date"])
        key = (d.year, d.month)
        if d.day <= 7 and key not in month_seen:
            index = ((d - first).days + offset) // 7
            body += text(64 + index * 17, 108, calendar.month_abbr[d.month], c, 10, "muted", mono=True)
            month_seen.add(key)
    for label, row in [("Mon", 0), ("Wed", 2), ("Fri", 4)]:
        body += text(25, 124 + row * 17, label, c, 9, "faint", mono=True)
    for day in data["days"]:
        d = date.fromisoformat(day["date"])
        index = (d - first).days + offset
        col, row = index // 7, index % 7
        level = LEVELS.index(day["level"])
        x, y = 64 + col * 17, 114 + row * 17
        body += (f'<g><title>{xml(day["date"])}: {day["count"]} contributions</title>'
                 + rect(x, y, 13, 13, c["heat"][level], 2.5) + '</g>')
    body += text(64, 254, "Less", c, 10, "muted")
    for i, color in enumerate(c["heat"]):
        body += rect(97 + i * 17, 244, 12, 12, color, 2)
    body += text(187, 254, "More", c, 10, "muted")
    body += text(245, 254, "Intensity uses GitHub's contribution quartiles.", c, 10, "faint")
    body += text(32, 280, "Commits, pull requests, issues and reviews · private activity is not included with the Actions token.", c, 10, "faint")
    body += f'<line x1="974" y1="105" x2="974" y2="258" stroke="{c["border"]}"/>'
    body += text(1000, 132, number(data["total"]), c, 34, weight=750)
    body += text(1000, 153, "public contributions", c, 11, "muted")
    body += text(1000, 188, str(m["active_days"]), c, 23, weight=700)
    body += text(1000, 207, "active days", c, 11, "muted")
    body += text(1000, 240, str(m["current_streak"]), c, 23, weight=700)
    body += text(1000, 259, "current streak · days", c, 11, "muted")
    body += text(1000, 280, f'Longest: {m["longest_streak"]} days', c, 10, "faint")
    desc = (f'{data["total"]} public GitHub contributions over {len(data["days"])} days, '
            f'{m["active_days"]} active days, current streak {m["current_streak"]} days, '
            f'longest streak {m["longest_streak"]} days. A current streak may end yesterday if today has no activity yet.')
    return document(1200, 300, "A year of public GitHub contributions", desc, body, theme)


def project_card(project: dict, theme: str) -> str:
    c = THEMES[theme]
    accent = c[project.get("accent", "teal")]
    body = rect(20, 22, 3, 24, accent, 1.5)
    body += text(34, 42, short(project["name"], 38), c, 22, weight=700)
    body += text(24, 66, project["repo"], c, 10.5, "muted", mono=True)
    lines = textwrap.wrap(project["tagline"], width=73, break_long_words=False)[:2]
    for i, value in enumerate(lines):
        body += text(24, 92 + i * 19, value, c, 13, "muted")
    body += line(24, 128, 556, 128, c["border"])
    language = project.get("language") or "Mixed"
    body += dot(28, 151, LANGUAGE_COLORS.get(language, LANGUAGE_COLORS["Other"]))
    body += text(40, 155, short(language, 17), c, 11, "muted")
    body += text(213, 155, f'★ {number(project["stars"])}', c, 12, "amber", 600)
    body += (f'<path d="M288 145v5c0 3 8 3 8 0v-5M292 152v5" fill="none" '
             f'stroke="{c["muted"]}" stroke-width="1.4"/>'
             + ''.join(dot(x, y, c["muted"], 1.8) for x, y in [(288, 144), (296, 144), (292, 158)]))
    body += text(303, 155, number(project["forks"]), c, 12, "muted")
    pushed = (project.get("pushed_at") or "")[:10]
    body += text(556, 155, f'Pushed {pushed}', c, 10.5, "faint", anchor="end", mono=True)
    desc = (f'{project["name"]} ({project["repo"]}). {project["tagline"]} '
            f'{project["stars"]} stars, {project["forks"]} forks, primary language {language}, last push {pushed}.')
    return document(580, 176, f'{project["name"]} — live repository card', desc, body, theme)


def merge_month_buckets(prs: list[dict], today: date, months: int = 12) -> list[dict]:
    """Count actual merge dates in calendar months; never use updated_at."""
    keys = []
    year, month = today.year, today.month
    for _ in range(months):
        keys.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    keys.reverse()
    counts = dict.fromkeys(keys, 0)
    for pr in prs:
        merged_at = (pr.get("pull_request") or {}).get("merged_at")
        if merged_at and merged_at[:7] in counts:
            counts[merged_at[:7]] += 1
    return [{"month": key, "count": count} for key, count in counts.items()]


def streak_metrics(days: list[dict], today: date) -> dict:
    """Active-day streaks over the supplied window, not fabricated all-time data."""
    by_date = {d["date"]: d["count"] for d in days}
    longest = running = 0
    cursor = date.fromisoformat(days[0]["date"])
    while cursor <= today:
        running = running + 1 if by_date.get(cursor.isoformat(), 0) > 0 else 0
        longest = max(longest, running)
        cursor = date.fromordinal(cursor.toordinal() + 1)
    cursor = today
    if by_date.get(cursor.isoformat(), 0) == 0:
        cursor = date.fromordinal(cursor.toordinal() - 1)
    current = 0
    while by_date.get(cursor.isoformat(), 0) > 0:
        current += 1
        cursor = date.fromordinal(cursor.toordinal() - 1)
    return {"active_days": sum(count > 0 for count in by_date.values()),
            "current_streak": current, "longest_streak": longest}


def validate_calendar(data: dict, first: date, last: date) -> None:
    days = data.get("days", [])
    expected = [(date.fromordinal(first.toordinal() + i)).isoformat()
                for i in range((last - first).days + 1)]
    if [d.get("date") for d in days] != expected:
        raise ValueError("Contribution calendar is incomplete, duplicated or out of order")
    if any(type(d.get("count")) is not int or d["count"] < 0 or d.get("level") not in LEVELS for d in days):
        raise ValueError("Contribution calendar contains invalid counts or intensity levels")
    if data.get("total") != sum(d["count"] for d in days):
        raise ValueError("Contribution calendar total does not match its daily counts")
    if data.get("from") != first.isoformat() or data.get("to") != last.isoformat():
        raise ValueError("Contribution calendar date range does not match the request")


def validate_snapshot(snapshot: dict) -> None:
    """Reject inconsistent aggregates before they can reach an image or README."""
    if snapshot.get("schema_version") != 1:
        raise ValueError("Unsupported snapshot schema")
    date.fromisoformat(snapshot["as_of"])
    m = snapshot["metrics"]
    required = ("external_prs", "external_projects", "merged_prs", "open_prs",
                "closed_unmerged_prs", "merged_projects", "original_repos",
                "original_stars", "followers", "contributions", "active_days",
                "current_streak", "longest_streak")
    if any(type(m.get(key)) is not int or m[key] < 0 for key in required):
        raise ValueError("Snapshot metrics must be non-negative integers")
    if m["external_prs"] != m["merged_prs"] + m["open_prs"] + m["closed_unmerged_prs"]:
        raise ValueError("External PR outcomes do not sum to the total")
    if m["merged_projects"] > m["external_projects"]:
        raise ValueError("More landed projects than external projects")
    if m["contributions"] != snapshot["contributions"]["total"]:
        raise ValueError("Calendar and headline contribution totals disagree")
    if sum(r["merged"] for r in snapshot["upstream_repos"]) != m["merged_prs"] or sum(
            r["open"] for r in snapshot["upstream_repos"]) != m["open_prs"]:
        raise ValueError("Upstream chart does not reconcile with headline PR counts")
    languages = snapshot["languages"]
    if languages["total_bytes"] != sum(i["bytes"] for i in languages["items"]):
        raise ValueError("Language bytes do not sum to the total")
    if any(type(i["bytes"]) is not int or i["bytes"] < 0 for i in languages["items"]):
        raise ValueError("Language bytes must be non-negative integers")
    slugs = [p["slug"] for p in snapshot["projects"]]
    if len(slugs) != len(set(slugs)) or any(not re.fullmatch(r"[a-z0-9-]+", s) for s in slugs):
        raise ValueError("Project card filenames must be unique, safe slugs")
    if any(type(p.get(k)) is not int or p[k] < 0 for p in snapshot["projects"] for k in ("stars", "forks")):
        raise ValueError("Project stars and forks must be non-negative integers")
    if any(type(p.get("count")) is not int or p["count"] < 0 for p in snapshot["merge_months"]):
        raise ValueError("Monthly merge counts must be non-negative integers")


def render_all(snapshot: dict) -> dict[str, bytes]:
    validate_snapshot(snapshot)
    today = date.fromisoformat(snapshot["as_of"])
    validate_calendar(snapshot["contributions"], date.fromisoformat(snapshot["contributions"]["from"]), today)
    assets = {}
    for theme in THEMES:
        for name, renderer in [("pulse", pulse), ("upstream", upstream),
                               ("languages", languages), ("contributions", contribution_calendar)]:
            svg = renderer(snapshot, theme)
            ET.fromstring(svg)
            assets[f"assets/generated/{name}.{theme}.svg"] = svg.encode("utf-8")
        for project in snapshot["projects"]:
            svg = project_card(project, theme)
            ET.fromstring(svg)
            assets[f'assets/generated/project-{project["slug"]}.{theme}.svg'] = svg.encode("utf-8")
    return assets


def update_history(history: dict | None, snapshot: dict, limit: int = 366) -> dict:
    """Keep one real aggregate observation per UTC day; never backfill guesses."""
    if history is None:
        history = {"schema_version": 1, "days": []}
    if history.get("schema_version") != 1 or not isinstance(history.get("days"), list):
        raise ValueError("Unsupported profile history format")
    seen = set()
    fields = ("followers", "original_stars", "original_repos", "merged_prs", "open_prs", "contributions")
    for day in history["days"]:
        value_date = date.fromisoformat(day["date"])
        if value_date.isoformat() in seen or any(type(day.get(k)) is not int or day[k] < 0 for k in fields):
            raise ValueError("Profile history contains duplicate dates or invalid metrics")
        seen.add(value_date.isoformat())
    if limit < 1:
        raise ValueError("History limit must be positive")
    m = snapshot["metrics"]
    point = {"date": snapshot["as_of"], **{key: m[key] for key in (
        "followers", "original_stars", "original_repos", "merged_prs", "open_prs", "contributions"
    )}}
    days = [d for d in history["days"] if d.get("date") != point["date"]]
    days.append(point)
    days.sort(key=lambda d: d["date"])
    return {"schema_version": 1, "days": days[-limit:]}
