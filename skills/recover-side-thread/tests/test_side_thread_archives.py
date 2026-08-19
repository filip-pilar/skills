from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).parents[1]
SCRIPT = PACKAGE_ROOT / "scripts" / "side_thread_archives.py"
SKILL = PACKAGE_ROOT / "SKILL.md"


def record(kind: str, payload: dict, timestamp: str) -> dict:
    return {"timestamp": timestamp, "type": kind, "payload": payload}


class SideThreadArchiveScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name) / ".codex"
        self.archive = self.home / "archived_sessions"
        self.archive.mkdir(parents=True)

        self.archive_path = self.archive / (
            "rollout-2026-08-04T10-00-00-019test00-0000-0000-0000-000000000001.jsonl"
        )
        rows = [
            record(
                "session_meta",
                {
                    "id": "019test00-0000-0000-0000-000000000001",
                    "session_id": "019test00-0000-0000-0000-000000000001",
                    "timestamp": "2026-08-04T10:00:00Z",
                    "cwd": "/tmp/example-project",
                    "thread_source": "user",
                    "git": {"branch": "handover-test"},
                },
                "2026-08-04T10:00:00Z",
            ),
            record(
                "event_msg",
                {"type": "task_started", "turn_id": "turn-1"},
                "2026-08-04T10:00:01Z",
            ),
            record(
                "response_item",
                {
                    "type": "message",
                    "role": "developer",
                    "content": [{"type": "input_text", "text": "hidden-secret=do-not-export"}],
                },
                "2026-08-04T10:00:02Z",
            ),
            record(
                "event_msg",
                {
                    "type": "user_message",
                    "message": "Recover the handoff parser and preserve the failing test.",
                },
                "2026-08-04T10:00:03Z",
            ),
            record(
                "event_msg",
                {
                    "type": "agent_message",
                    "phase": "final",
                    "message": "The parser is partly fixed; the last check still fails with token=sk-test_abcdefghijklmnopqrstuvwxyz123456.",
                },
                "2026-08-04T10:00:04Z",
            ),
            record(
                "event_msg",
                {
                    "type": "task_complete",
                    "turn_id": "turn-1",
                    "completed_at": "2026-08-04T10:00:05Z",
                    "last_agent_message": "The parser is partly fixed; the last check still fails with token=sk-test_abcdefghijklmnopqrstuvwxyz123456.",
                },
                "2026-08-04T10:00:05Z",
            ),
        ]
        self.archive_path.write_text(
            "".join(json.dumps(row) + "\n" for row in rows),
            encoding="utf-8",
        )
        active = self.home / "sessions" / "2026" / "08" / "04"
        active.mkdir(parents=True)
        (active / "active.jsonl").write_text(
            "active thread should not be listed\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_list_uses_archive_only_and_exposes_selection_path(self) -> None:
        result = self.run_script(
            "list",
            "--codex-home",
            str(self.home),
            "--limit",
            "5",
            "--scan-limit",
            "5",
            "--format",
            "json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(len(report["candidates"]), 1)
        candidate = report["candidates"][0]
        self.assertEqual(candidate["thread_id"], "019test00-0000-0000-0000-000000000001")
        self.assertIn("Recover the handoff parser", candidate["title"])
        self.assertEqual(candidate["display_title"], "Recover the handoff parser and preserve the failing test.")
        self.assertEqual(candidate["workspace"], "example-project")
        self.assertEqual(candidate["path"], str(self.archive_path.resolve()))
        self.assertEqual(candidate["source_type"], "unverified")
        self.assertNotIn("active thread", result.stdout)

    def test_classify_returns_metadata_without_message_previews_or_paths(self) -> None:
        result = self.run_script(
            "classify",
            "--codex-home",
            str(self.home),
            "--thread-id",
            "019test00-0000-0000-0000-000000000001",
            "--scan-limit",
            "5",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["source_type"], "unverified")
        self.assertTrue(report["archive_exists"])
        self.assertNotIn("Recover the handoff parser", result.stdout)
        self.assertNotIn(str(self.archive_path), result.stdout)

    def register_main_task(self) -> None:
        database = self.home / "state_5.sqlite"
        connection = sqlite3.connect(database)
        connection.execute(
            """
            CREATE TABLE threads (
                id TEXT PRIMARY KEY,
                title TEXT,
                archived INTEGER,
                archived_at INTEGER,
                updated_at_ms INTEGER,
                cwd TEXT,
                thread_source TEXT,
                git_branch TEXT,
                rollout_path TEXT
            )
            """
        )
        connection.execute(
            """
            INSERT INTO threads (
                id, title, archived, archived_at, updated_at_ms, cwd,
                thread_source, git_branch, rollout_path
            ) VALUES (?, ?, 1, NULL, 1785837600000, ?, 'user', '', ?)
            """,
            (
                "019test00-0000-0000-0000-000000000001",
                "Registered main task",
                "/tmp/example-project",
                str(self.archive_path.resolve()),
            ),
        )
        connection.commit()
        connection.close()

    def test_default_discovery_excludes_registered_main_tasks(self) -> None:
        self.register_main_task()
        result = self.run_script(
            "list",
            "--codex-home",
            str(self.home),
            "--limit",
            "5",
            "--scan-limit",
            "5",
            "--format",
            "json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["candidates"], [])

        exact = self.run_script(
            "list",
            "--codex-home",
            str(self.home),
            "--thread-id",
            "019test00-0000-0000-0000-000000000001",
            "--scan-limit",
            "5",
            "--format",
            "json",
        )
        self.assertEqual(exact.returncode, 0, exact.stderr)
        candidate = json.loads(exact.stdout)["candidates"][0]
        self.assertEqual(candidate["source_type"], "main_task")

    def test_current_database_overrides_stale_database(self) -> None:
        stale_directory = self.home / "sqlite"
        stale_directory.mkdir()
        stale = sqlite3.connect(stale_directory / "state_5.sqlite")
        stale.execute(
            """
            CREATE TABLE threads (
                id TEXT PRIMARY KEY, title TEXT, archived INTEGER,
                archived_at INTEGER, updated_at_ms INTEGER, cwd TEXT,
                thread_source TEXT, git_branch TEXT, rollout_path TEXT
            )
            """
        )
        stale.commit()
        stale.close()
        self.register_main_task()

        result = self.run_script(
            "list",
            "--codex-home",
            str(self.home),
            "--thread-id",
            "019test00-0000-0000-0000-000000000001",
            "--scan-limit",
            "5",
            "--format",
            "json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        candidate = json.loads(result.stdout)["candidates"][0]
        self.assertEqual(candidate["source_type"], "main_task")

    def test_inspect_refuses_registered_main_task(self) -> None:
        self.register_main_task()
        result = self.run_script(
            "inspect",
            "--codex-home",
            str(self.home),
            "--path",
            str(self.archive_path),
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("main Codex task", result.stderr)

    def test_classify_identifies_registered_main_task(self) -> None:
        self.register_main_task()
        result = self.run_script(
            "classify",
            "--codex-home",
            str(self.home),
            "--thread-id",
            "019test00-0000-0000-0000-000000000001",
            "--scan-limit",
            "5",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["source_type"], "main_task")
        self.assertTrue(report["archive_exists"])

    def test_markdown_uses_short_workspace_label(self) -> None:
        result = self.run_script(
            "list",
            "--codex-home",
            str(self.home),
            "--limit",
            "5",
            "--scan-limit",
            "5",
            "--kind",
            "user",
            "--format",
            "markdown",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("workspace: example-project", result.stdout)
        self.assertNotIn("workspace: /tmp/example-project", result.stdout)
        self.assertNotIn("The parser is partly fixed", result.stdout)
        self.assertNotIn("archive path", result.stdout.lower())
        self.assertNotIn("thread ID", result.stdout)

    def test_kind_filter_can_narrow_results_when_needed(self) -> None:
        subagent_path = self.archive / (
            "rollout-2026-08-04T09-00-00-019test00-0000-0000-0000-000000000002.jsonl"
        )
        rows = [
            record(
                "session_meta",
                {
                    "id": "019test00-0000-0000-0000-000000000002",
                    "session_id": "019test00-0000-0000-0000-000000000002",
                    "timestamp": "2026-08-04T09:00:00Z",
                    "cwd": "/tmp/example-project",
                    "thread_source": "subagent",
                },
                "2026-08-04T09:00:00Z",
            ),
            record(
                "event_msg",
                {
                    "type": "user_message",
                    "message": "Draft a compact evidence summary.",
                },
                "2026-08-04T09:00:01Z",
            ),
        ]
        subagent_path.write_text(
            "".join(json.dumps(row) + "\n" for row in rows),
            encoding="utf-8",
        )

        user_only = self.run_script(
            "list",
            "--codex-home",
            str(self.home),
            "--limit",
            "5",
            "--scan-limit",
            "5",
            "--kind",
            "user",
            "--format",
            "json",
        )
        self.assertEqual(user_only.returncode, 0, user_only.stderr)
        self.assertEqual(
            [item["thread_id"] for item in json.loads(user_only.stdout)["candidates"]],
            ["019test00-0000-0000-0000-000000000001"],
        )

        all_sources = self.run_script(
            "list",
            "--codex-home",
            str(self.home),
            "--limit",
            "5",
            "--scan-limit",
            "5",
            "--kind",
            "all",
            "--format",
            "json",
        )
        self.assertEqual(all_sources.returncode, 0, all_sources.stderr)
        self.assertEqual(
            {item["thread_id"] for item in json.loads(all_sources.stdout)["candidates"]},
            {
                "019test00-0000-0000-0000-000000000001",
                "019test00-0000-0000-0000-000000000002",
            },
        )

        default_user = self.run_script(
            "list",
            "--codex-home",
            str(self.home),
            "--limit",
            "5",
            "--scan-limit",
            "5",
            "--format",
            "json",
        )
        self.assertEqual(default_user.returncode, 0, default_user.stderr)
        self.assertEqual(
            [item["thread_id"] for item in json.loads(default_user.stdout)["candidates"]],
            ["019test00-0000-0000-0000-000000000001"],
        )

        exact_subagent = self.run_script(
            "list",
            "--codex-home",
            str(self.home),
            "--thread-id",
            "019test00-0000-0000-0000-000000000002",
            "--limit",
            "5",
            "--scan-limit",
            "5",
            "--format",
            "json",
        )
        self.assertEqual(exact_subagent.returncode, 0, exact_subagent.stderr)
        self.assertEqual(
            [item["thread_id"] for item in json.loads(exact_subagent.stdout)["candidates"]],
            ["019test00-0000-0000-0000-000000000002"],
        )

    def test_airbnb_query_prefers_underlying_work_over_recovery_meta_thread(self) -> None:
        actual_path = self.archive / (
            "rollout-2026-08-12T17-30-00-019airbnb0-0000-0000-0000-000000000001.jsonl"
        )
        actual_rows = [
            record(
                "session_meta",
                {
                    "id": "019airbnb0-0000-0000-0000-000000000001",
                    "timestamp": "2026-08-12T17:30:00Z",
                    "cwd": "/tmp/can",
                    "thread_source": "user",
                },
                "2026-08-12T17:30:00Z",
            ),
            record(
                "event_msg",
                {
                    "type": "user_message",
                    "message": (
                        "# Files mentioned by the user:\n\n"
                        "## screenshot.png: /tmp/screenshot.png\n\n"
                        "## My request:\ncan you access my chrome tabs with units to compare?"
                    ),
                },
                "2026-08-12T17:30:01Z",
            ),
            record(
                "event_msg",
                {
                    "type": "agent_message",
                    "message": (
                        "Built the blind Airbnb comparison at "
                        "outputs/blind-unit-comparison/index.html."
                    ),
                },
                "2026-08-12T17:30:02Z",
            ),
            record(
                "event_msg",
                {"type": "user_message", "message": "where can i view the html/site"},
                "2026-08-12T17:30:03Z",
            ),
        ]
        actual_path.write_text(
            "".join(json.dumps(row) + "\n" for row in actual_rows),
            encoding="utf-8",
        )

        meta_path = self.archive / (
            "rollout-2026-08-17T16-47-00-019airbnb0-0000-0000-0000-000000000002.jsonl"
        )
        meta_rows = [
            record(
                "session_meta",
                {
                    "id": "019airbnb0-0000-0000-0000-000000000002",
                    "timestamp": "2026-08-17T16:47:00Z",
                    "cwd": "/tmp/help",
                    "thread_source": "user",
                },
                "2026-08-17T16:47:00Z",
            ),
            record(
                "event_msg",
                {
                    "type": "user_message",
                    "message": "help me find the archived Airbnb project",
                },
                "2026-08-17T16:47:01Z",
            ),
        ]
        meta_path.write_text(
            "".join(json.dumps(row) + "\n" for row in meta_rows),
            encoding="utf-8",
        )

        result = self.run_script(
            "list",
            "--codex-home",
            str(self.home),
            "--query",
            "airbnb",
            "--limit",
            "5",
            "--scan-limit",
            "5",
            "--format",
            "json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        candidates = json.loads(result.stdout)["candidates"]
        self.assertEqual(
            [item["thread_id"] for item in candidates[:2]],
            [
                "019airbnb0-0000-0000-0000-000000000001",
                "019airbnb0-0000-0000-0000-000000000002",
            ],
        )
        self.assertNotIn("Files mentioned", candidates[0]["display_title"])
        self.assertIn("chrome tabs", candidates[0]["display_title"].lower())

    def test_inspect_excludes_hidden_context_and_redacts_secret(self) -> None:
        result = self.run_script(
            "inspect",
            "--codex-home",
            str(self.home),
            "--path",
            str(self.archive_path),
            "--format",
            "json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["coverage"]["developer_and_system_records_excluded"])
        self.assertIn("Recover the handoff parser", json.dumps(report))
        self.assertNotIn("hidden-secret", result.stdout)
        self.assertNotIn("sk-test_abcdefghijklmnopqrstuvwxyz123456", result.stdout)
        self.assertIn("<REDACTED>", result.stdout)

    def test_inspect_pairs_turns_strips_boilerplate_and_reports_activity(self) -> None:
        activity_path = self.archive / (
            "rollout-2026-08-05T10-00-00-019activity-0000-0000-0000-000000000001.jsonl"
        )
        rows = [
            record(
                "session_meta",
                {
                    "id": "019activity-0000-0000-0000-000000000001",
                    "timestamp": "2026-08-05T10:00:00Z",
                    "cwd": "/tmp/airbnb",
                    "thread_source": "user",
                },
                "2026-08-05T10:00:00Z",
            ),
            record(
                "event_msg",
                {"type": "task_started", "turn_id": "turn-1"},
                "2026-08-05T10:00:01Z",
            ),
            record(
                "event_msg",
                {
                    "type": "user_message",
                    "message": (
                        "# Files mentioned by the user:\n\n"
                        "## screenshot.png: /tmp/private-screenshot.png\n\n"
                        "<in-app-browser-context source=\"ambient-ui-state\">\n"
                        "Current URL: https://example.invalid/private\n"
                        "</in-app-browser-context>\n\n"
                        "## My request:\nadd prices to each saved round"
                    ),
                },
                "2026-08-05T10:00:02Z",
            ),
            record(
                "response_item",
                {
                    "type": "function_call",
                    "name": "apply_patch",
                    "arguments": (
                        "*** Begin Patch\n"
                        "*** Update File: outputs/blind-unit-comparison/index.html\n"
                        "*** End Patch"
                    ),
                },
                "2026-08-05T10:00:03Z",
            ),
            record(
                "response_item",
                {
                    "type": "function_call_output",
                    "output": '{"exit_code": 0, "output": "private raw output"}',
                },
                "2026-08-05T10:00:04Z",
            ),
            record(
                "event_msg",
                {
                    "type": "agent_message",
                    "phase": "final",
                    "message": "Added dates and totals to saved-round cards.",
                },
                "2026-08-05T10:00:05Z",
            ),
        ]
        activity_path.write_text(
            "".join(json.dumps(row) + "\n" for row in rows),
            encoding="utf-8",
        )

        result = self.run_script(
            "inspect",
            "--codex-home",
            str(self.home),
            "--path",
            str(activity_path),
            "--format",
            "json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(
            [message["role"] for message in report["visible_messages"]],
            ["user", "assistant"],
        )
        self.assertEqual(report["visible_messages"][0]["text"], "add prices to each saved round")
        self.assertNotIn("private-screenshot", result.stdout)
        self.assertNotIn("example.invalid", result.stdout)
        self.assertNotIn("private raw output", result.stdout)
        self.assertEqual(
            report["activity"]["changed_paths"],
            ["outputs/blind-unit-comparison/index.html"],
        )
        self.assertEqual(report["activity"]["recorded_command_exit_codes"]["zero"], 1)
        self.assertEqual(report["coverage"]["ambient_context_blocks_removed"], 1)
        self.assertEqual(report["coverage"]["attachment_preambles_removed"], 1)

    def test_inspect_rejects_path_outside_archive(self) -> None:
        outside = self.home / "sessions" / "active.jsonl"
        outside.write_text("{}\n", encoding="utf-8")
        result = self.run_script(
            "inspect",
            "--codex-home",
            str(self.home),
            "--path",
            str(outside),
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("outside the archived_sessions directory", result.stderr)

    def test_handoff_contract_keeps_source_inside_prompt_and_omits_ids(self) -> None:
        instructions = SKILL.read_text(encoding="utf-8")
        handoff = instructions.split("## 5. Produce the handoff", 1)[1]

        self.assertIn("Main Codex task (confirmed)", instructions)
        self.assertIn("Source type unverified", instructions)
        self.assertIn("Do not produce a recovery handoff", instructions)
        self.assertIn("The fenced prompt must include", handoff)
        self.assertIn("`Type: Side chat`", handoff)


if __name__ == "__main__":
    unittest.main()
