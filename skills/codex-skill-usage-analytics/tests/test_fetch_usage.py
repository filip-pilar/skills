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
SPEC = importlib.util.spec_from_file_location("codex_skill_usage_analytics", SCRIPT)
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


def skill_overview(name, count, *identifiers):
    return {
        "skill_name": name,
        "display_name": name.title(),
        "skill_ids": list(identifiers),
        "invocation_counts": count,
    }


def skill_day(date, *overviews):
    return {"date": date, "skill_usage_overviews": list(overviews)}


def empty_profile(start="2026-01-01", total=0):
    return {
        "stats": {
            "cumulative_daily_usage_buckets": [{"start_date": start}],
            "top_invocations": [],
            "unique_skills_used": 0,
            "total_skills_used": total,
        }
    }


def installation(name, path, source="user", namespace=None):
    return {
        "name": name,
        "base_name": name.rsplit(":", 1)[-1],
        "namespace": namespace,
        "source": source,
        "path": str(path),
        "marketplace": "market" if source == "plugin" else None,
        "plugin_identifier": None,
        "version": None,
    }


def inventory_item(name, paths, source="user", namespace=None):
    installs = [installation(name, path, source, namespace) for path in paths]
    return {
        "name": name,
        "base_name": name.rsplit(":", 1)[-1],
        "namespace": namespace,
        "source": source,
        "sources": [source],
        "installation_count": len(installs),
        "duplicate_installation": len(installs) > 1,
        "installations": installs,
    }


def inventory(*items):
    return {
        "enabled": True,
        "current_skill_count": len(items),
        "installation_count": sum(item["installation_count"] for item in items),
        "current_skills": list(items),
        "duplicate_installations": [
            item for item in items if item["duplicate_installation"]
        ],
        "warnings": [],
    }


def write_skill(path: Path, name: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\nname: {name}\ndescription: Test skill.\n---\n\n# {name}\n",
        encoding="utf-8",
    )


def write_plugin(root: Path, name: str, version: str, skill_names):
    package = root / version
    manifest = package / ".codex-plugin" / "plugin.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps({"name": name, "version": version, "skills": "./skills"}),
        encoding="utf-8",
    )
    for skill_name in skill_names:
        write_skill(package / "skills" / skill_name / "SKILL.md", skill_name)


class FetchUsageTests(unittest.TestCase):
    def test_date_windows_are_inclusive_non_overlapping_and_bounded(self):
        start = dt.date(2025, 1, 1)
        end = dt.date(2026, 1, 1)
        self.assertEqual(
            fetch_usage.date_windows(start, end),
            [
                (dt.date(2025, 1, 1), dt.date(2025, 12, 31)),
                (dt.date(2026, 1, 1), dt.date(2026, 1, 1)),
            ],
        )

    def test_collect_metric_preserves_daily_and_calculates_recent_periods(self):
        client = FakeClient(
            {
                fetch_usage.SKILL_PATH: {
                    "data_freshness_ts": "2026-09-02T08:00:00Z",
                    "data": [
                        skill_day("2026-06-04", skill_overview("alpha", 1, "a1")),
                        skill_day("2026-06-05", skill_overview("alpha", 2, "a1")),
                        skill_day("2026-08-03", skill_overview("alpha", 3, "a1")),
                        skill_day("2026-08-04", skill_overview("alpha", 4, "a1")),
                        skill_day("2026-08-26", skill_overview("alpha", 5, "a1")),
                        skill_day("2026-08-27", skill_overview("alpha", 6, "a1")),
                        skill_day("2026-09-02", skill_overview("alpha", 7, "a1")),
                    ],
                }
            }
        )
        metric = fetch_usage.collect_metric(
            client, "skills", dt.date(2026, 6, 4), dt.date(2026, 9, 2)
        )
        item = metric["items"][0]
        self.assertEqual(item["count"], 28)
        self.assertEqual(item["first_observed"], "2026-06-04")
        self.assertEqual(item["last_observed"], "2026-09-02")
        self.assertEqual(item["active_days"], 7)
        self.assertEqual(item["days_since_last_use"], 0)
        self.assertEqual(item["uses_per_active_day"], 4.0)
        self.assertEqual(item["uses_per_week_since_first_observed"], 2.1538)
        self.assertEqual(item["uses_last_7_days"], 13)
        self.assertEqual(item["uses_last_30_days"], 22)
        self.assertEqual(item["uses_last_90_days"], 27)
        self.assertEqual(item["daily"][0], {
            "date": "2026-06-04",
            "count": 1,
            "identifiers": ["a1"],
        })
        self.assertEqual(metric["returned_start_date"], "2026-06-04")
        self.assertEqual(metric["returned_end_date"], "2026-09-02")
        self.assertEqual(metric["returned_day_count"], 7)
        self.assertEqual(client.calls[0][1]["top_skill_limit"], 1000)

    def test_identity_flags_cover_multiple_ids_and_shared_id_names(self):
        client = FakeClient(
            {
                fetch_usage.SKILL_PATH: {
                    "data": [
                        skill_day("2026-09-01", skill_overview("alpha", 2, "shared")),
                        skill_day(
                            "2026-09-02",
                            skill_overview("alpha", 3, "new-id"),
                            skill_overview("beta", 1, "shared"),
                        ),
                    ]
                }
            }
        )
        metric = fetch_usage.collect_metric(
            client, "skills", dt.date(2026, 9, 1), dt.date(2026, 9, 2)
        )
        by_name = {item["name"]: item for item in metric["items"]}
        self.assertIn("multiple_identifiers_for_name", by_name["alpha"]["identity_flags"])
        self.assertIn(
            "identifier_observed_with_multiple_names",
            by_name["alpha"]["identity_flags"],
        )
        self.assertEqual(
            by_name["beta"]["possible_renames"],
            [{"name": "alpha", "evidence": "shared_telemetry_identifier", "identifier": "shared"}],
        )

    def test_collect_metric_excludes_other_and_preserves_other_daily(self):
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
        self.assertEqual(metric["other_daily"][0]["date"], "2026-09-02")
        self.assertEqual([item["name"] for item in metric["items"]], ["Browser"])

    def test_inventory_discovery_handles_empty_roots(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            discovered = fetch_usage.discover_inventory(
                codex_home=root / "codex",
                agents_skills_dir=root / "agents",
                config_path=root / "codex" / "config.toml",
            )
        self.assertEqual(discovered["current_skill_count"], 0)
        self.assertEqual(discovered["installation_count"], 0)
        self.assertEqual(discovered["current_skills"], [])

    def test_inventory_uses_enabled_plugins_markers_and_disabled_skill_config(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            codex_home = root / "codex"
            agents = root / "agents"
            write_skill(agents / "duplicate" / "SKILL.md", "duplicate")
            write_skill(codex_home / "skills" / "duplicate" / "SKILL.md", "duplicate")
            write_skill(codex_home / "skills" / "disabled" / "SKILL.md", "disabled")
            manual_path = agents / "manual" / "SKILL.md"
            write_skill(manual_path, "manual")
            metadata = manual_path.parent / "agents" / "openai.yaml"
            metadata.parent.mkdir(parents=True, exist_ok=True)
            metadata.write_text(
                "policy:\n  allow_implicit_invocation: false\n",
                encoding="utf-8",
            )
            active = codex_home / "plugins" / "cache" / "market" / "active"
            stale = codex_home / "plugins" / "cache" / "market" / "stale"
            remote = codex_home / "plugins" / "cache" / "remote" / "remote-plugin"
            write_plugin(active, "active", "1.0.0", ["tool"])
            write_plugin(active, "active", "2.0.0", ["tool-new"])
            write_plugin(stale, "stale", "1.0.0", ["stale-tool"])
            write_plugin(remote, "remote-plugin", "1.0.0", ["remote-tool"])
            (remote / ".codex-remote-plugin-install.json").write_text(
                json.dumps({"remote_plugin_id": "remote-id"}), encoding="utf-8"
            )
            config = codex_home / "config.toml"
            config.parent.mkdir(parents=True, exist_ok=True)
            config.write_text(
                """
[plugins."active@market"]
enabled = true

[[skills.config]]
name = "disabled"
enabled = false
""",
                encoding="utf-8",
            )
            discovered = fetch_usage.discover_inventory(
                codex_home=codex_home,
                agents_skills_dir=agents,
                config_path=config,
            )
        by_name = {item["name"]: item for item in discovered["current_skills"]}
        self.assertEqual(by_name["duplicate"]["installation_count"], 2)
        self.assertTrue(by_name["duplicate"]["duplicate_installation"])
        self.assertIn("active:tool-new", by_name)
        self.assertNotIn("active:tool", by_name)
        self.assertIn("remote-plugin:remote-tool", by_name)
        self.assertNotIn("stale:stale-tool", by_name)
        self.assertNotIn("disabled", by_name)
        self.assertEqual(by_name["manual"]["invocation_mode"], "manual_only")
        self.assertEqual(by_name["manual"]["distribution"], "standalone_user")
        self.assertEqual(by_name["manual"]["source_paths"], [str(manual_path)])
        self.assertEqual(
            by_name["active:tool-new"]["distribution"], "configured_plugin"
        )

    def test_inventory_merge_adds_zero_historical_duplicate_and_possible_predecessor(self):
        client = FakeClient(
            {
                fetch_usage.SKILL_PATH: {
                    "data": [
                        skill_day(
                            "2026-09-02",
                            skill_overview("current", 3, "c1"),
                            skill_overview("old:tool", 2, "o1"),
                        )
                    ]
                }
            }
        )
        metric = fetch_usage.collect_metric(
            client, "skills", dt.date(2026, 9, 1), dt.date(2026, 9, 2)
        )
        current = inventory_item("current", ["/one", "/two"])
        replacement = inventory_item("new:tool", ["/new"], "plugin", "new")
        unused = inventory_item("unused", ["/unused"])
        fetch_usage.merge_skill_inventory(
            metric, inventory(current, replacement, unused)
        )
        by_name = {item["name"]: item for item in metric["items"]}
        self.assertEqual(by_name["current"]["inventory_status"], "current_observed")
        self.assertTrue(by_name["current"]["duplicate_installation"])
        self.assertEqual(by_name["unused"]["count"], 0)
        self.assertEqual(
            by_name["unused"]["observation_status"],
            "no_invocation_returned_during_coverage",
        )
        self.assertEqual(
            by_name["new:tool"]["observation_status"],
            "not_observed_under_current_name",
        )
        self.assertEqual(
            by_name["new:tool"]["possible_renames"],
            [{"name": "old:tool", "evidence": "same_normalized_base_name"}],
        )
        self.assertEqual(by_name["old:tool"]["inventory_status"], "historical")
        self.assertEqual(metric["inventory_summary"]["current_unobserved_count"], 2)

    def test_inventory_merge_preserves_declared_package_rename(self):
        client = FakeClient(
            {
                fetch_usage.SKILL_PATH: {
                    "data": [
                        skill_day(
                            "2026-09-02",
                            skill_overview("codex-usage-analytics", 4, "old-id"),
                        )
                    ]
                }
            }
        )
        metric = fetch_usage.collect_metric(
            client, "skills", dt.date(2026, 9, 1), dt.date(2026, 9, 2)
        )
        renamed = inventory_item(
            "codex-skill-usage-analytics", ["/renamed"]
        )
        fetch_usage.merge_skill_inventory(metric, inventory(renamed))
        by_name = {item["name"]: item for item in metric["items"]}
        self.assertEqual(
            by_name["codex-skill-usage-analytics"]["possible_renames"],
            [
                {
                    "name": "codex-usage-analytics",
                    "evidence": "declared_package_rename",
                }
            ],
        )
        self.assertEqual(
            by_name["codex-usage-analytics"]["possible_renames"],
            [
                {
                    "name": "codex-skill-usage-analytics",
                    "evidence": "declared_package_rename",
                }
            ],
        )

    def test_all_available_uses_profile_activity_start(self):
        profile = empty_profile("2026-02-23")

        def empty_skills(params):
            return {"data": [], "data_freshness_ts": "2026-09-02T00:00:00Z"}

        client = FakeClient(
            {fetch_usage.PROFILE_PATH: profile, fetch_usage.SKILL_PATH: empty_skills}
        )
        report = fetch_usage.build_report(
            client,
            kind="skills",
            start=None,
            end=dt.date(2026, 9, 2),
            days=None,
            all_available=True,
            inventory=inventory(),
        )
        self.assertEqual(report["schema_version"], 3)
        self.assertEqual(report["requested_range"]["start"], "2026-02-23")
        self.assertEqual(report["selected_view"]["view"], "current")
        skill_call = next(call for call in client.calls if call[0] == fetch_usage.SKILL_PATH)
        self.assertEqual(skill_call[1]["start_date"], "2026-02-23")

    def test_warnings_only_include_actionable_report_problems(self):
        warnings = fetch_usage.build_warnings(
            {"activity_start": "2026-01-01", "total_skills_used": 4},
            dt.date(2026, 1, 1),
            {
                "skills": {
                    "first_recorded_date": None,
                    "returned_start_date": None,
                    "returned_end_date": None,
                    "complete_for_returned_days": False,
                    "total_invocations": 5,
                }
            },
            dt.date(2026, 9, 2),
        )
        self.assertEqual(len(warnings), 2)
        self.assertTrue(any("no dated rows" in warning for warning in warnings))
        self.assertTrue(any("truncated" in warning for warning in warnings))

    def test_markdown_default_is_current_compact_and_excludes_historical(self):
        client = FakeClient(
            {
                fetch_usage.PROFILE_PATH: empty_profile(total=1),
                fetch_usage.SKILL_PATH: {
                    "data": [skill_day("2026-09-02", skill_overview("historical", 1))]
                },
            }
        )
        report = fetch_usage.build_report(
            client,
            kind="skills",
            start=dt.date(2026, 9, 1),
            end=dt.date(2026, 9, 2),
            days=None,
            all_available=False,
            inventory=inventory(inventory_item("unobserved", ["/unused"])),
        )
        markdown = fetch_usage.markdown_report(report)
        self.assertIn("| unobserved |", markdown)
        self.assertNotIn("| historical |", markdown)
        self.assertIn("| Name | Source | Uses | Active days | Last used | 30d | Invocation | Source path |", markdown)
        self.assertNotIn("Coverage and limitations", markdown)
        all_markdown = fetch_usage.markdown_report(report, view="all")
        self.assertIn("| historical |", all_markdown)

    def test_timeline_views_aggregate_daily_weekly_and_monthly(self):
        items = [
            {
                "name": "alpha",
                "daily": [
                    {"date": "2026-08-31", "count": 2, "identifiers": []},
                    {"date": "2026-09-01", "count": 3, "identifiers": []},
                ],
            }
        ]
        self.assertEqual(
            fetch_usage._timeline_rows(items, "daily"),
            [("2026-08-31", "alpha", 2), ("2026-09-01", "alpha", 3)],
        )
        self.assertEqual(
            fetch_usage._timeline_rows(items, "weekly"),
            [("2026-W36", "alpha", 5)],
        )
        self.assertEqual(
            fetch_usage._timeline_rows(items, "monthly"),
            [("2026-08", "alpha", 2), ("2026-09", "alpha", 3)],
        )

    def test_view_filters_and_recency_sort_are_explicit(self):
        end = dt.date(2026, 9, 2)
        current = {
            "name": "current",
            "count": 1,
            "last_used": "2026-09-02",
            "daily": [{"date": "2026-09-02", "count": 1}],
            "current_available": True,
            "inventory_status": "current_observed",
            "duplicate_installation": False,
            "possible_renames": [],
        }
        unobserved = {
            "name": "unobserved",
            "count": 0,
            "last_used": None,
            "daily": [],
            "current_available": True,
            "inventory_status": "current_unobserved",
            "duplicate_installation": False,
            "possible_renames": [],
        }
        self.assertEqual(
            [item["name"] for item in fetch_usage._view_items([current, unobserved], "unobserved", 30, end)],
            ["unobserved"],
        )
        self.assertEqual(
            [item["name"] for item in fetch_usage._view_items([current, unobserved], "current", 30, end)],
            ["current", "unobserved"],
        )
        self.assertEqual(
            [item["name"] for item in fetch_usage._sort_items([unobserved, current], "most-recent")],
            ["current", "unobserved"],
        )

    def test_default_arguments_focus_on_current_skills(self):
        args = fetch_usage.parse_args([])
        self.assertEqual(args.kind, "skills")
        self.assertEqual(args.view, "current")

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


if __name__ == "__main__":
    unittest.main()
