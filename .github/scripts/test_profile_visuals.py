#!/usr/bin/env python3
"""Offline regression tests for real-data aggregation and SVG publication."""
import copy
import json
import tempfile
import unittest
import urllib.error
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import profile_visuals as pv
import update_profile as up


def snapshot_fixture():
    first = date(2026, 1, 1)
    days = [{"date": (first + timedelta(days=i)).isoformat(), "count": 1 if i >= 11 else 0,
             "level": "FIRST_QUARTILE" if i >= 11 else "NONE"} for i in range(14)]
    return {
        "schema_version": 1, "as_of": "2026-01-14", "generated_at": "2026-01-14T00:17:00+00:00",
        "username": "test-user",
        "metrics": {"external_prs": 3, "external_projects": 2, "merged_prs": 1, "open_prs": 1,
                    "closed_unmerged_prs": 1, "merged_projects": 1, "original_repos": 1,
                    "original_stars": 7, "followers": 4, "contributions": 3,
                    "active_days": 3, "current_streak": 3, "longest_streak": 3},
        "contributions": {"from": "2026-01-01", "to": "2026-01-14", "total": 3, "days": days},
        "languages": {"repositories": 1, "total_bytes": 100,
                      "items": [{"name": "Python", "bytes": 75}, {"name": "Shell", "bytes": 25}]},
        "merge_months": [{"month": "2026-01", "count": 1}],
        "upstream_repos": [{"repo": "upstream/project", "merged": 1, "open": 1}],
        "projects": [{"slug": "test-user-demo", "name": "Demo", "repo": "test-user/demo",
                      "url": "https://github.com/test-user/demo", "tagline": "A useful, tested project.",
                      "accent": "teal", "stars": 7, "forks": 2, "language": "Python",
                      "pushed_at": "2026-01-14T00:00:00Z"}],
    }


class TestVisualData(unittest.TestCase):
    def test_streak_allows_today_to_be_empty(self):
        days = [{"date": f"2026-01-{i:02d}", "count": count} for i, count in enumerate([0, 1, 1, 0, 1, 1, 0], 1)]
        self.assertEqual(pv.streak_metrics(days, date(2026, 1, 7)),
                         {"active_days": 4, "current_streak": 2, "longest_streak": 2})

    def test_streak_today_active_and_zero_window(self):
        days = [{"date": "2026-01-01", "count": 0}, {"date": "2026-01-02", "count": 2}]
        self.assertEqual(pv.streak_metrics(days, date(2026, 1, 2))["current_streak"], 1)
        self.assertEqual(pv.streak_metrics([{"date": "2026-01-01", "count": 0}], date(2026, 1, 1)),
                         {"active_days": 0, "current_streak": 0, "longest_streak": 0})

    def test_merge_buckets_use_merge_date_not_update_date(self):
        prs = [{"pull_request": {"merged_at": "2026-01-31T23:00:00Z"}, "updated_at": "2026-02-01T00:00:00Z"},
               {"pull_request": {"merged_at": None}, "updated_at": "2026-02-01T00:00:00Z"}]
        buckets = pv.merge_month_buckets(prs, date(2026, 2, 14), months=2)
        self.assertEqual(buckets, [{"month": "2026-01", "count": 1}, {"month": "2026-02", "count": 0}])

    def test_calendar_rejects_missing_duplicate_negative_and_wrong_total(self):
        data = snapshot_fixture()["contributions"]
        for bad in [dict(data, days=data["days"][:-1]), dict(data, days=data["days"] + [data["days"][-1]]),
                    dict(data, total=999), dict(data, days=[dict(data["days"][0], count=-1)] + data["days"][1:])]:
            with self.assertRaises(ValueError):
                pv.validate_calendar(bad, date(2026, 1, 1), date(2026, 1, 14))

    def test_snapshot_rejects_non_reconciling_totals(self):
        for field, value in [("external_prs", 99), ("contributions", 99), ("followers", -1)]:
            bad = snapshot_fixture()
            bad["metrics"][field] = value
            with self.assertRaises(ValueError):
                pv.validate_snapshot(bad)
        bad = snapshot_fixture()
        bad["languages"]["total_bytes"] = 999
        with self.assertRaises(ValueError):
            pv.validate_snapshot(bad)

    def test_all_svgs_parse_have_alt_text_and_no_active_content(self):
        assets = pv.render_all(snapshot_fixture())
        self.assertEqual(len(assets), 10)
        for path, content in assets.items():
            root = ET.fromstring(content)
            self.assertTrue(path.endswith((".dark.svg", ".light.svg")))
            self.assertTrue(root.find("{http://www.w3.org/2000/svg}title").text)
            self.assertTrue(root.find("{http://www.w3.org/2000/svg}desc").text)
            self.assertNotIn(b"<script", content)
            self.assertNotIn(b"foreignObject", content)
            self.assertNotIn(b"<image", content)

    def test_api_text_is_xml_escaped(self):
        data = snapshot_fixture()
        data["projects"][0]["name"] = '<script>alert("x")</script>'
        data["projects"][0]["tagline"] = "A & B < C"
        assets = pv.render_all(data)
        svg = assets["assets/generated/project-test-user-demo.dark.svg"].decode()
        self.assertNotIn("<script>", svg)
        self.assertIn("&lt;script&gt;", svg)
        self.assertIn("A &amp; B &lt; C", svg)

    def test_zero_metrics_render_without_division_errors(self):
        data = snapshot_fixture()
        for key in data["metrics"]:
            data["metrics"][key] = 0
        data["contributions"]["total"] = 0
        for day in data["contributions"]["days"]:
            day.update(count=0, level="NONE")
        data["languages"].update(total_bytes=0, items=[])
        data["upstream_repos"] = []
        data["merge_months"] = []
        self.assertEqual(len(pv.render_all(data)), 10)

    def test_history_replaces_same_day_and_never_backfills(self):
        data = snapshot_fixture()
        history = pv.update_history(None, data)
        self.assertEqual(len(history["days"]), 1)
        changed = copy.deepcopy(data)
        changed["metrics"]["followers"] = 10
        history = pv.update_history(history, changed)
        self.assertEqual(len(history["days"]), 1)
        self.assertEqual(history["days"][0]["followers"], 10)
        changed["as_of"] = "2026-01-15"
        history = pv.update_history(history, changed, limit=1)
        self.assertEqual([d["date"] for d in history["days"]], ["2026-01-15"])

    def test_corrupt_history_is_rejected(self):
        with self.assertRaises(ValueError):
            pv.update_history({"schema_version": 1, "days": [{"date": "bad"}]}, snapshot_fixture())


class TestPublicationSafety(unittest.TestCase):
    def test_missing_or_duplicate_markers_fail(self):
        text = "<!-- DYNAMIC:X:START -->\nold\n<!-- DYNAMIC:X:END -->"
        self.assertEqual(up.replace_blocks(text, {"X": "new"}),
                         "<!-- DYNAMIC:X:START -->\nnew\n<!-- DYNAMIC:X:END -->")
        for bad in ["", text + "\n" + text]:
            with self.assertRaises(ValueError):
                up.replace_blocks(bad, {"X": "new"})

    def test_failed_refresh_touches_no_published_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            readme = root / "README.md"
            readme.write_text("last valid profile")
            chart = root / "assets/generated/pulse.dark.svg"
            chart.parent.mkdir(parents=True)
            chart.write_bytes(b"last valid chart")
            with patch.object(up, "ROOT", root), patch.object(up, "README_PATH", readme), \
                 patch.object(up, "build_profile", side_effect=RuntimeError("API unavailable")):
                self.assertEqual(up.main(), 1)
            self.assertEqual(readme.read_text(), "last valid profile")
            self.assertEqual(chart.read_bytes(), b"last valid chart")
            self.assertFalse((root / "data").exists())

    def test_transaction_rolls_back_after_partial_replace(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            a, b = root / "a", root / "b"
            a.write_bytes(b"old-a")
            real_replace = up.os.replace
            calls = 0
            def fail_second(src, dst):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("simulated disk failure")
                return real_replace(src, dst)
            with patch.object(up.os, "replace", side_effect=fail_second):
                with self.assertRaises(OSError):
                    up.publish_transaction({a: b"new-a", b: b"new-b"})
            self.assertEqual(a.read_bytes(), b"old-a")
            self.assertFalse(b.exists())
            self.assertEqual(list(root.iterdir()), [a])

    def test_incomplete_search_never_becomes_a_metric(self):
        with patch.object(up, "api_get", return_value={"items": [], "total_count": 1, "incomplete_results": True}):
            with self.assertRaises(RuntimeError):
                up.api_get_all("https://api.github.com/search/issues?q=test")

    def test_search_over_api_window_fails_closed(self):
        with patch.object(up, "api_get", return_value={"items": [], "total_count": 1001, "incomplete_results": False}):
            with self.assertRaises(RuntimeError):
                up.api_get_all("https://api.github.com/search/issues?q=test")

    def test_transient_api_failure_retries(self):
        response = unittest.mock.MagicMock()
        response.__enter__.return_value.read.return_value = b'{"ok": true}'
        error = urllib.error.HTTPError("https://api.github.com", 502, "Bad gateway", {}, None)
        with patch.object(up.urllib.request, "urlopen", side_effect=[error, response]) as request, \
             patch.object(up.time, "sleep"):
            self.assertEqual(up.api_request("https://api.github.com/test"), {"ok": True})
            self.assertEqual(request.call_count, 2)

    def test_graphql_errors_fail_closed(self):
        response = unittest.mock.MagicMock()
        response.__enter__.return_value.read.return_value = b'{"data": null, "errors": [{"message": "no"}]}'
        with patch.object(up.urllib.request, "urlopen", return_value=response):
            with self.assertRaises(RuntimeError):
                up.api_request("https://api.github.com/graphql", {"query": "query {}"})

    def test_visual_shortlist_matches_featured_config(self):
        featured = {p["repo"].lower() for p in up.FEATURED_PROJECTS}
        self.assertTrue(set(up.VISUAL_PROJECTS).issubset(featured))
        self.assertEqual(len(up.VISUAL_PROJECTS), 6)

    def test_pr_date_uses_actual_merge_date(self):
        self.assertEqual(up.pr_date({"updated_at": "2026-02-01", "pull_request": {"merged_at": "2026-01-01"}}), "2026-01-01")
        self.assertEqual(up.pr_date({"updated_at": "2026-02-01", "pull_request": None}), "2026-02-01")


if __name__ == "__main__":
    unittest.main()
