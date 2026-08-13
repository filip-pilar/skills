from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).parents[1]
SCRIPT = PACKAGE_ROOT / "scripts" / "expired_threads.py"


def record(kind: str, payload: dict, timestamp: str) -> dict:
    return {"timestamp": timestamp, "type": kind, "payload": payload}


class ExpiredThreadHandoverScriptTests(unittest.TestCase):
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
        self.assertNotIn("active thread", result.stdout)

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
        self.assertIn("latest assistant context: The parser is partly fixed", result.stdout)

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


if __name__ == "__main__":
    unittest.main()
