#!/usr/bin/env python3
"""Unit tests for update_profile.py pure helpers (no network).

Run:  python -m unittest discover -s .github/scripts -p "test_*.py" -v
CI runs these before every scheduled regeneration, so a broken helper can
never publish a broken profile.
"""

import unittest

import update_profile as up


class TestHelpers(unittest.TestCase):
    def test_fmt_stars(self):
        self.assertEqual(up.fmt_stars(0), "0")
        self.assertEqual(up.fmt_stars(999), "999")
        self.assertEqual(up.fmt_stars(1500), "1.5k")
        self.assertEqual(up.fmt_stars(39023), "39k")
        self.assertEqual(up.fmt_stars(194266), "194k")

    def test_esc_keeps_markdown_tables_safe(self):
        self.assertEqual(up.esc("a|b"), "a\\|b")
        self.assertEqual(up.esc("line\nbreak"), "line break")
        self.assertEqual(up.esc(None), "")

    def test_is_merged_requires_merged_at(self):
        self.assertTrue(up.is_merged({"pull_request": {"merged_at": "2026-10-25T00:00:00Z"}}))
        self.assertFalse(up.is_merged({"pull_request": {"merged_at": None}, "state": "closed"}))
        self.assertFalse(up.is_merged({"pull_request": {}, "state": "open"}))
        self.assertFalse(up.is_merged({}))

    def test_repo_of(self):
        pr = {"repository_url": "https://api.github.com/repos/google-research/google-research"}
        self.assertEqual(up.repo_of(pr), "google-research/google-research")

    def test_search_url_external_excludes_own_repos(self):
        url = up.search_url("is:merged", external_only=True)
        self.assertIn("-user%3A", url)  # self-merges must not pad OSS numbers
        self.assertIn("is%3Amerged", url)

    def test_curation_is_consistent(self):
        repos = [c["repo"].lower() for c in up.CURATED]
        self.assertEqual(len(repos), len(set(repos)), "duplicate curated repos")
        for repo in repos:
            self.assertIn("/", repo)
        projects = [fp["repo"].lower() for fp in up.FEATURED_PROJECTS]
        self.assertEqual(len(projects), len(set(projects)), "duplicate featured projects")
        for fp in up.FEATURED_PROJECTS:
            for key in ("repo", "name", "demo", "highlight", "stack"):
                self.assertIn(key, fp, f"{fp.get('repo')} missing {key}")
            self.assertTrue(fp["highlight"].strip(), "empty highlight")

    def test_select_more_repos_excludes_forks_private_profile_and_featured(self):
        repos = [
            {"name": "kept", "fork": False, "pushed_at": "2026-01-01T00:00:00Z"},
            {"name": "newer", "fork": False, "pushed_at": "2026-05-01T00:00:00Z"},
            {"name": "forked", "fork": True, "pushed_at": "2026-06-01T00:00:00Z"},
            {"name": "private-repo", "fork": False, "private": True,
             "pushed_at": "2026-06-02T00:00:00Z"},
            {"name": "RANJITHROSAN17", "fork": False, "pushed_at": "2026-07-01T00:00:00Z"},
            {"name": "Featured", "fork": False, "pushed_at": "2026-08-01T00:00:00Z"},
        ]
        picked = up.select_more_repos(repos, ["featured"], "RANJITHROSAN17")
        self.assertEqual([r["name"] for r in picked], ["newer", "kept"])


if __name__ == "__main__":
    unittest.main()
