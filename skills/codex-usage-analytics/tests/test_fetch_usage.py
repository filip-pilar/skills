from __future__ import annotations

import datetime as dt
import importlib.util
import json
import sys
import tempfile
import unittest
import urllib.request
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "fetch_usage.py"
SPEC = importlib.util.spec_from_file_location("fetch_usage", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
fetch_usage = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = fetch_usage
SPEC.loader.exec_module(fetch_usage)


class FakeClient:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def get(self, path, params=None):
        self.calls.append((path, params))
        response = self.responses[path]
        return response(params) if callable(response) else response


class FetchUsageTests(unittest.TestCase):
    def test_date_windows_are_inclusive_non_overlapping_and_bounded(self):
        start = dt.date(2025, 1, 1)
        end = dt.date(2026, 1, 1)
        windows = fetch_usage.date_windows(start, end)
        self.assertEqual(
            windows,
            [
                (dt.date(2025, 1, 1), dt.date(2025, 12, 31)),
                (dt.date(2026, 1, 1), dt.date(2026, 1, 1)),
            ],
        )

    def test_collect_metric_aggregates_and_detects_complete_results(self):
        client = FakeClient(
            {
                fetch_usage.SKILL_PATH: {
                    "data_freshness_ts": "2026-09-02T08:00:00Z",
                    "data": [
                        {
                            "date": "2026-09-01",
                            "skill_usage_overviews": [
                                {
                                    "skill_name": "alpha",
                                    "display_name": "Alpha",
                                    "skill_ids": ["a1"],
                                    "invocation_counts": 2,
                                }
                            ],
                        },
                        {
                            "date": "2026-09-02",
                            "skill_usage_overviews": [
                                {
                                    "skill_name": "alpha",
                                    "display_name": "Alpha",
                                    "skill_ids": ["a1"],
                                    "invocation_counts": 3,
                                },
                                {
                                    "skill_name": "beta",
                                    "display_name": "Beta",
                                    "skill_ids": [],
                                    "invocation_counts": 1,
                                },
                            ],
                        },
                    ],
                }
            }
        )
        metric = fetch_usage.collect_metric(
            client, "skills", dt.date(2026, 9, 1), dt.date(2026, 9, 2)
        )
        self.assertEqual(metric["total_invocations"], 6)
        self.assertEqual(metric["active_days"], 2)
        self.assertEqual(metric["distinct_items"], 2)
        self.assertTrue(metric["complete_for_returned_days"])
        self.assertEqual(metric["items"][0]["count"], 5)
        self.assertEqual(metric["items"][0]["first_observed"], "2026-09-01")
        self.assertEqual(metric["items"][0]["last_observed"], "2026-09-02")
        self.assertEqual(metric["items"][0]["identifiers"], ["a1"])
        self.assertEqual(client.calls[0][1]["top_skill_limit"], 1000)

    def test_collect_metric_excludes_other_and_marks_truncation(self):
        client = FakeClient(
            {
                fetch_usage.PLUGIN_PATH: {
                    "data": [
                        {
                            "date": "2026-09-02",
                            "plugin_usage_overviews": [
                                {
                                    "display_name": "Browser",
                                    "plugin_id": "browser",
                                    "plugin_name": "browser",
                                    "marketplace": "bundled",
                                    "invocation_counts": 4,
                                },
                                {
                                    "display_name": "Other",
                                    "plugin_id": None,
                                    "plugin_name": None,
                                    "marketplace": None,
                                    "invocation_counts": 7,
                                },
                            ],
                        }
                    ]
                }
            }
        )
        metric = fetch_usage.collect_metric(
            client, "plugins", dt.date(2026, 9, 2), dt.date(2026, 9, 2)
        )
        self.assertFalse(metric["complete_for_returned_days"])
        self.assertEqual(metric["other_invocations"], 7)
        self.assertEqual(metric["distinct_items"], 1)
        self.assertEqual([item["name"] for item in metric["items"]], ["Browser"])

    def test_all_available_uses_profile_activity_start(self):
        profile = {
            "stats": {
                "cumulative_daily_usage_buckets": [
                    {"start_date": "2026-02-23"},
                    {"start_date": "2026-09-01"},
                ],
                "top_invocations": [],
                "unique_skills_used": 2,
                "total_skills_used": 3,
            }
        }

        def empty_skills(params):
            return {"data": [], "data_freshness_ts": "2026-09-02T00:00:00Z"}

        client = FakeClient(
            {
                fetch_usage.PROFILE_PATH: profile,
                fetch_usage.SKILL_PATH: empty_skills,
            }
        )
        report = fetch_usage.build_report(
            client,
            kind="skills",
            start=None,
            end=dt.date(2026, 9, 2),
            days=None,
            all_available=True,
        )
        self.assertEqual(report["requested_range"]["start"], "2026-02-23")
        skill_call = next(call for call in client.calls if call[0] == fetch_usage.SKILL_PATH)
        self.assertEqual(skill_call[1]["start_date"], "2026-02-23")

    def test_load_auth_does_not_include_secrets_in_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "auth.json"
            secret = "super-secret-refresh-token"
            path.write_text(
                json.dumps({"tokens": {"refresh_token": secret}}), encoding="utf-8"
            )
            with self.assertRaises(fetch_usage.UsageAnalyticsError) as raised:
                fetch_usage.load_auth(path)
        self.assertNotIn(secret, str(raised.exception))

    def test_client_refuses_arbitrary_endpoint(self):
        client = fetch_usage.ApiClient(
            fetch_usage.Auth(access_token="secret", account_id="account")
        )
        with self.assertRaises(fetch_usage.UsageAnalyticsError):
            client.get("/not-allowed")

    def test_redirect_handler_refuses_every_supported_redirect(self):
        handler = fetch_usage.RefuseRedirectHandler()
        request = urllib.request.Request(
            "https://chatgpt.com/backend-api/wham/profiles/me",
            headers={
                "Authorization": "Bearer secret",
                "ChatGPT-Account-Id": "account",
            },
        )

        for code in (301, 302, 303, 307, 308):
            with self.subTest(code=code):
                with self.assertRaises(fetch_usage.UsageAnalyticsError):
                    handler.redirect_request(
                        request,
                        None,
                        code,
                        "redirect",
                        {},
                        "https://example.invalid/capture",
                    )

    def test_warnings_flag_profile_and_daily_total_mismatch(self):
        warnings = fetch_usage.build_warnings(
            {"activity_start": "2026-09-01", "total_skills_used": 4},
            dt.date(2026, 9, 1),
            {
                "skills": {
                    "first_recorded_date": "2026-09-01",
                    "complete_for_returned_days": True,
                    "total_invocations": 5,
                }
            },
        )
        self.assertTrue(any("differs" in warning for warning in warnings))


if __name__ == "__main__":
    unittest.main()
