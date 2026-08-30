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
        self.side_id = "01aside00-0000-0000-0000-000000000001"
        self.closed_side_id = "01aside00-0000-0000-0000-000000000002"
        self.likely_side_id = "01aside00-0000-0000-0000-000000000003"
        self.synthetic_thread_id = "01aside00-0000-0000-0000-000000000004"
        self.possible_side_id = "01aside00-0000-0000-0000-000000000005"
        self.internal_thread_id = "01aside00-0000-0000-0000-000000000006"
        self.recovery_meta_id = "01aside00-0000-0000-0000-000000000007"
        self.parent_id = "01parent0-0000-0000-0000-000000000001"
        global_state = {
            "electron-persisted-atom-state": {
                f"thread-tab-routes-v1:{self.parent_id}": {
                    "topology": {
                        "left": {"tabIds": []},
                        "right": {"tabIds": [f"sidechat:{self.side_id}"]},
                        "bottom": {"tabIds": []},
                    }
                }
            }
        }
        (self.home / ".codex-global-state.json").write_text(
            json.dumps(global_state), encoding="utf-8"
        )
        state = sqlite3.connect(self.home / "state_5.sqlite")
        state.execute(
            """
            CREATE TABLE threads (
                id TEXT PRIMARY KEY, title TEXT, archived INTEGER,
                archived_at INTEGER, updated_at_ms INTEGER, cwd TEXT,
                thread_source TEXT, git_branch TEXT, rollout_path TEXT
            )
            """
        )
        state.commit()
        state.close()
        logs = sqlite3.connect(self.home / "logs_2.sqlite")
        logs.execute(
            """
            CREATE TABLE logs (
                id INTEGER PRIMARY KEY, ts INTEGER, ts_nanos INTEGER, level TEXT,
                target TEXT, feedback_log_body TEXT, module_path TEXT, file TEXT,
                line INTEGER, thread_id TEXT, process_uuid TEXT, estimated_bytes INTEGER
            )
            """
        )
        user_body = (
            'Submission sub=Submission { op: TurnInput { request: TurnInputRequest { '
            'input: UserInput { content: [Text { text: "Review the stale roadmap and propose Batch 013A.", '
            'text_elements: [] }], client_id: "test" }, cwd: "/tmp/side-project" } } }'
        )
        logs.execute(
            "INSERT INTO logs (ts, ts_nanos, target, feedback_log_body, thread_id) VALUES (?, 0, ?, ?, ?)",
            (1785837600, "codex_core::session::handlers", user_body, self.side_id),
        )
        logs.execute(
            "INSERT INTO logs (ts, ts_nanos, target, feedback_log_body, thread_id) VALUES (?, 0, ?, ?, ?)",
            (
                1785837601,
                "codex_core::stream_events_utils",
                "ToolCall: send_message_to_thread parent prompt token=parent-payload-must-stay-excluded",
                self.side_id,
            ),
        )
        logs.execute(
            "INSERT INTO logs (ts, ts_nanos, target, feedback_log_body, thread_id) VALUES (?, 0, ?, ?, ?)",
            (
                1785837500,
                "codex_core::session::rollout_reconstruction",
                'app_server.request{otel.name="thread/fork"}: ignored patch',
                self.closed_side_id,
            ),
        )
        closed_body = (
            'Submission sub=Submission { op: TurnInput { request: TurnInputRequest { '
            'input: UserInput { content: [Text { text: "Draft a reply for the parent task.", '
            'text_elements: [] }], client_id: "test" } } } }'
        )
        logs.execute(
            "INSERT INTO logs (ts, ts_nanos, target, feedback_log_body, thread_id) VALUES (?, 0, ?, ?, ?)",
            (1785837501, "codex_core::session::handlers", closed_body, self.closed_side_id),
        )
        likely_messages = (
            '[$sidekick](/tmp/sidekick/SKILL.md)',
            "good work, whats next",
            "Im AI. We need to decide whether live webhook testing belongs in this adapter repository.",
            "The Linq Chat SDK project should preserve the signed-webhook replay decisions.",
        )
        for index, message in enumerate(likely_messages):
            body = (
                'Submission sub=Submission { op: TurnInput { request: TurnInputRequest { '
                f'input: UserInput {{ content: [Text {{ text: {json.dumps(message)}, '
                'text_elements: [] }], client_id: "test" } } } }'
            )
            logs.execute(
                "INSERT INTO logs (ts, ts_nanos, target, feedback_log_body, thread_id) VALUES (?, 0, ?, ?, ?)",
                (1785837700 + index, "codex_core::session::handlers", body, self.likely_side_id),
            )
        logs.execute(
            "INSERT INTO logs (ts, ts_nanos, target, feedback_log_body, thread_id) VALUES (?, 0, ?, ?, ?)",
            (
                1785837704,
                "feedback_tags",
                "session_task.run model=gpt-test cwd=/tmp/linq-chat-sdk}: sampling",
                self.likely_side_id,
            ),
        )
        synthetic_body = (
            'Submission sub=Submission { op: TurnInput { request: TurnInputRequest { '
            'input: UserInput { content: [Text { text: "<codex_delegation>Inspect the adapter.</codex_delegation>", '
            'text_elements: [] }], client_id: "test" } } } }'
        )
        logs.execute(
            "INSERT INTO logs (ts, ts_nanos, target, feedback_log_body, thread_id) VALUES (?, 0, ?, ?, ?)",
            (1785837800, "codex_core::session::handlers", synthetic_body, self.synthetic_thread_id),
        )
        possible_body = (
            'Submission sub=Submission { op: TurnInput { request: TurnInputRequest { '
            'input: UserInput { content: [Text { text: "Check the rare adapter edge case.", '
            'text_elements: [] }], client_id: "test" } } } }'
        )
        logs.execute(
            "INSERT INTO logs (ts, ts_nanos, target, feedback_log_body, thread_id) VALUES (?, 0, ?, ?, ?)",
            (1785837602, "codex_core::session::handlers", possible_body, self.possible_side_id),
        )
        internal_body = (
            'Submission sub=Submission { op: TurnInput { request: TurnInputRequest { '
            'input: UserInput { content: [Text { text: "You write the one-line activity update displayed beneath an existing Codex task title.", '
            'text_elements: [] }], client_id: "test" } } } }'
        )
        logs.execute(
            "INSERT INTO logs (ts, ts_nanos, target, feedback_log_body, thread_id) VALUES (?, 0, ?, ?, ?)",
            (1785837900, "codex_core::session::handlers", internal_body, self.internal_thread_id),
        )
        recovery_messages = (
            '[$recover-side-thread](/tmp/recover-side-thread/SKILL.md)',
            "Which one is the latest one from the Linq Chat SDK project?",
        )
        for index, message in enumerate(recovery_messages):
            body = (
                'Submission sub=Submission { op: TurnInput { request: TurnInputRequest { '
                f'input: UserInput {{ content: [Text {{ text: {json.dumps(message)}, '
                'text_elements: [] }], client_id: "test" } } } }'
            )
            logs.execute(
                "INSERT INTO logs (ts, ts_nanos, target, feedback_log_body, thread_id) VALUES (?, 0, ?, ?, ?)",
                (1785838000 + index, "codex_core::session::handlers", body, self.recovery_meta_id),
            )
        logs.commit()
        logs.close()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def side_list(self, *args: str) -> dict:
        result = self.run_script(
            "side-list", "--codex-home", str(self.home), *args, "--format", "json"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def side_inspect(self, thread_id: str, *args: str, expected: int = 0) -> dict:
        result = self.run_script(
            "side-inspect", "--codex-home", str(self.home), "--thread-id", thread_id, *args
        )
        self.assertEqual(result.returncode, expected, result.stderr)
        return json.loads(result.stdout)

    def add_user_turn(
        self, thread_id: str, timestamp: int, message: str, cwd: str = "/tmp/reliability-lab",
        *, nanos: int = 0,
    ) -> str:
        body = (
            'Submission sub=Submission { op: TurnInput { request: TurnInputRequest { '
            f'input: UserInput {{ content: [Text {{ text: {json.dumps(message)}, '
            f'text_elements: [] }}], client_id: "test" }}, cwd: {json.dumps(cwd)} }} }} }}'
        )
        connection = sqlite3.connect(self.home / "logs_2.sqlite")
        connection.execute(
            "INSERT INTO logs (ts, ts_nanos, target, feedback_log_body, thread_id) VALUES (?, ?, ?, ?, ?)",
            (timestamp, nanos, "codex_core::session::handlers", body, thread_id),
        )
        connection.commit()
        connection.close()
        return body

    def add_state_task(self, thread_id: str, source: str = "user", title: str = "Parent task") -> None:
        connection = sqlite3.connect(self.home / "state_5.sqlite")
        connection.execute(
            """
            INSERT INTO threads (
                id, title, archived, archived_at, updated_at_ms, cwd,
                thread_source, git_branch, rollout_path
            ) VALUES (?, ?, 0, NULL, 1785837600000, '/tmp/reliability-lab', ?, '', '')
            """,
            (thread_id, title, source),
        )
        connection.commit()
        connection.close()

    def add_parent_tool_call(
        self, side_id: str, parent_id: str, timestamp: int, prompt: str
    ) -> None:
        body = (
            'ToolCall: send_message_to_thread arguments='
            + json.dumps({"threadId": parent_id, "prompt": prompt})
        )
        connection = sqlite3.connect(self.home / "logs_2.sqlite")
        connection.execute(
            "INSERT INTO logs (ts, ts_nanos, target, feedback_log_body, thread_id) VALUES (?, 0, ?, ?, ?)",
            (timestamp, "codex_core::tools::parallel", body, side_id),
        )
        connection.commit()
        connection.close()

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

    def test_side_list_uses_persisted_tab_state_and_logs(self) -> None:
        report = self.side_list("--limit", "10")
        by_id = {item["thread_id"]: item for item in report["candidates"]}
        registered = by_id[self.side_id]
        self.assertEqual(registered["source_type"], "side_chat_confirmed")
        self.assertEqual(registered["parent_thread_id"], self.parent_id)
        self.assertEqual(registered["workspace"], "side-project")
        self.assertIn("stale roadmap", registered["title"].lower())
        self.assertEqual(report["sources_scanned"]["registered_side_chats"], 1)

    def test_side_list_finds_closed_historical_fork_candidate(self) -> None:
        by_id = {item["thread_id"]: item for item in self.side_list("--limit", "10")["candidates"]}
        closed = by_id[self.closed_side_id]
        self.assertEqual(closed["source_type"], "side_chat_log_candidate")
        self.assertFalse(closed["registered_in_tab_state"])
        self.assertIn("reply", closed["title"].lower())

    def test_side_list_finds_likely_chat_without_fork_marker(self) -> None:
        report = self.side_list("--limit", "10", "--scan-limit", "20")
        by_id = {item["thread_id"]: item for item in report["candidates"]}
        self.assertEqual(report["candidates"][0]["thread_id"], self.likely_side_id)
        self.assertEqual(report["groups"][-1]["project"], "Unknown project")
        likely = by_id[self.likely_side_id]
        self.assertEqual(likely["source_type"], "side_chat_likely")
        self.assertEqual(likely["confidence"], "likely")
        self.assertFalse(likely["fork_marker_observed"])
        self.assertEqual(likely["workspace"], "linq-chat-sdk")
        self.assertEqual(likely["project_label"], "Linq Chat SDK")
        self.assertIn("signed-webhook replay", likely["title"].lower())
        self.assertNotIn("recover-side-thread", likely["title"])
        self.assertEqual(likely["latest_message_at"], "2026-08-04 10:01 UTC")
        self.assertRegex(likely["latest_message_age"], r"^(?:just now|\d+(?:m|h|d|w|mo|y) ago)$")
        self.assertEqual(likely["sort_epoch"], 1785837703.0)
        self.assertEqual(report["sources_scanned"]["interactive_log_threads_scanned"], 7)

    def test_side_list_excludes_synthetic_and_unmatched_single_turn_threads(self) -> None:
        broad_ids = {
            item["thread_id"]
            for item in self.side_list("--limit", "20", "--scan-limit", "20")["candidates"]
        }
        self.assertNotIn(self.synthetic_thread_id, broad_ids)
        self.assertNotIn(self.internal_thread_id, broad_ids)
        self.assertNotIn(self.recovery_meta_id, broad_ids)
        self.assertNotIn(self.possible_side_id, broad_ids)

        candidates = self.side_list(
            "--query", "rare adapter edge case", "--limit", "20", "--scan-limit", "20"
        )["candidates"]
        self.assertEqual([item["thread_id"] for item in candidates], [self.possible_side_id])
        self.assertEqual(candidates[0]["confidence"], "possible")

    def test_side_list_query_searches_all_turns_and_groups_by_project(self) -> None:
        report = self.side_list(
            "--query", "signed-webhook replay", "--limit", "20", "--scan-limit", "20"
        )
        self.assertEqual(
            [item["thread_id"] for item in report["candidates"]],
            [self.likely_side_id],
        )
        self.assertEqual(report["groups"][0]["project"], "Linq Chat SDK")

    def test_side_list_markdown_is_grouped_and_compact(self) -> None:
        result = self.run_script(
            "side-list",
            "--codex-home",
            str(self.home),
            "--limit",
            "20",
            "--scan-limit",
            "20",
            "--format",
            "markdown",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("I found 3 matching Side-chat candidates in the searched stages; showing 1–3.", result.stdout)
        self.assertIn("Linq Chat SDK\n", result.stdout)
        self.assertIn("Confirmed Side chat", result.stdout)
        self.assertIn("Likely Side chat", result.stdout)
        self.assertIn("Latest message ", result.stdout)
        self.assertNotIn("2026-08-04 10:01 UTC", result.stdout)
        self.assertIn("Reply with the number you want to recover.", result.stdout)
        self.assertNotIn("/tmp/", result.stdout)
        self.assertNotIn(self.likely_side_id, result.stdout)

    def test_side_list_reports_totals_and_supports_show_more_pagination(self) -> None:
        first_report = self.side_list("--limit", "1", "--scan-limit", "20")
        self.assertEqual(first_report["pagination"]["total_matches"], 3)
        self.assertEqual(first_report["pagination"]["returned"], 1)
        self.assertTrue(first_report["pagination"]["has_more"])
        self.assertEqual(first_report["pagination"]["next_offset"], 1)
        self.assertEqual(
            first_report["pagination"]["confidence_counts"],
            {"confirmed": 1, "likely": 2, "possible": 0},
        )

        more = self.run_script(
            "side-list",
            "--codex-home",
            str(self.home),
            "--limit",
            "1",
            "--offset",
            "1",
            "--scan-limit",
            "20",
            "--format",
            "markdown",
        )
        self.assertEqual(more.returncode, 0, more.stderr)
        self.assertIn("showing 2–2", more.stdout)
        self.assertIn("2. ", more.stdout)
        self.assertIn("More matches are available; ask to show more.", more.stdout)

    def test_side_list_supports_project_phrase_title_and_id_filters(self) -> None:
        filter_cases = (
            ("--project", "linq chat sdk", self.likely_side_id),
            ("--phrase", "signed-webhook replay", self.likely_side_id),
            ("--title", "signed-webhook replay", self.likely_side_id),
            ("--thread-id", self.possible_side_id, self.possible_side_id),
        )
        for flag, value, expected_id in filter_cases:
            with self.subTest(flag=flag):
                candidates = self.side_list(
                    flag, value, "--limit", "20", "--scan-limit", "20"
                )["candidates"]
                self.assertEqual([item["thread_id"] for item in candidates], [expected_id])

        possible = self.run_script(
            "side-list",
            "--codex-home",
            str(self.home),
            "--thread-id",
            self.possible_side_id,
            "--format",
            "markdown",
        )
        self.assertEqual(possible.returncode, 0, possible.stderr)
        self.assertIn("Possible Side chat", possible.stdout)
        self.assertIn("Confirmation required before recovery", possible.stdout)

    def test_html_lab_regression_matches_terms_split_across_turns_beyond_compact_horizon(self) -> None:
        html_side = "01ahtml00-0000-0000-0000-000000000001"
        self.add_user_turn(html_side, 1785800000, "Locky should only review the implementation approach.")
        self.add_user_turn(html_side, 1785800001, "The landing page needs a cleaner visual hierarchy.")
        self.add_user_turn(html_side, 1785800002, "Please create a new HTML experiment.")
        self.add_user_turn(html_side, 1785800003, "Use the lab workspace for the final comparison.")

        report = self.side_list(
            "--query", "landing page html lab", "--scan-limit", "2", "--limit", "12"
        )
        self.assertEqual([item["thread_id"] for item in report["candidates"]], [html_side])
        candidate = report["candidates"][0]
        self.assertEqual(candidate["recovery_stage"], "full_readable_log_horizon")
        self.assertEqual(candidate["matched_evidence"], "submitted_user_turns")
        self.assertIn("lab workspace", candidate["title"].lower())
        self.assertTrue(report["coverage"]["candidate_horizon"]["full_horizon_searched"])
        self.assertGreater(report["coverage"]["candidate_horizon"]["interactive_threads_in_readable_horizon"], 2)

    def test_recovery_audit_and_delegation_records_cannot_match_or_outrank_real_topic(self) -> None:
        real_side = "01areal00-0000-0000-0000-000000000001"
        audit_side = "01aaudit0-0000-0000-0000-000000000001"
        parent_id = "01aaudit0-0000-0000-0000-000000000002"
        audit_prompt = (
            "Please deeply investigate and brainstorm how to make recover-side-thread substantially "
            "more reliable before implementing the landing page HTML lab regression."
        )
        self.add_user_turn(real_side, 1785798000, "Compare the landing page composition.")
        self.add_user_turn(real_side, 1785798001, "Build the HTML alternative next.")
        self.add_user_turn(real_side, 1785798002, "Keep the result in the lab workspace.")
        self.add_user_turn(real_side, 1785799000, audit_prompt)

        self.add_state_task(parent_id, title="Reliability parent")
        self.add_user_turn(audit_side, 1785799500, "Review the evidence carefully before responding.")
        self.add_user_turn(
            audit_side,
            1785799600,
            f"<codex_delegation>{audit_prompt}</codex_delegation>",
        )
        self.add_user_turn(audit_side, 1785799700, audit_prompt)
        self.add_parent_tool_call(audit_side, parent_id, 1785799800, audit_prompt)

        report = self.side_list(
            "--query", "landing page html lab", "--scan-limit", "1", "--limit", "20"
        )
        self.assertEqual([item["thread_id"] for item in report["candidates"]], [real_side])
        real = report["candidates"][0]
        self.assertEqual(real["user_messages_observed"], 3)
        self.assertEqual(real["recovery_meta_messages_excluded"], 1)
        self.assertEqual(real["sort_epoch"], 1785798002.0)
        self.assertNotIn("deeply investigate", real["title"].lower())
        self.assertNotIn("deeply investigate", real["matched_message_snippet"].lower())

        audit = self.side_list("--thread-id", audit_side, "--limit", "20")["candidates"][0]
        self.assertEqual(audit["user_messages_observed"], 1)
        self.assertEqual(audit["synthetic_messages_excluded"], 1)
        self.assertEqual(audit["recovery_meta_messages_excluded"], 1)
        self.assertEqual(audit["sort_epoch"], 1785799500.0)
        self.assertEqual(audit["parent_relationship_source"], "unresolved")
        self.assertNotIn("landing page", audit["title"].lower())

    def test_repeated_and_redaction_colliding_submissions_keep_count_and_latest_message(self) -> None:
        side_id = "01arepeat-0000-0000-0000-000000000001"
        first_body = self.add_user_turn(
            side_id, 1785900000, "Compare token=sk-abcdefghijklmnop for the release checklist."
        )
        self.add_user_turn(
            side_id, 1785900600, "Compare token=sk-qrstuvwxyzabcdef for the release checklist."
        )
        legacy_dir = self.home / "sqlite"
        legacy_dir.mkdir(exist_ok=True)
        legacy = sqlite3.connect(legacy_dir / "logs_2.sqlite")
        legacy.execute(
            """
            CREATE TABLE logs (
                id INTEGER PRIMARY KEY, ts INTEGER, ts_nanos INTEGER, level TEXT,
                target TEXT, feedback_log_body TEXT, module_path TEXT, file TEXT,
                line INTEGER, thread_id TEXT, process_uuid TEXT, estimated_bytes INTEGER
            )
            """
        )
        legacy.execute(
            "INSERT INTO logs (ts, ts_nanos, target, feedback_log_body, thread_id) VALUES (?, 0, ?, ?, ?)",
            (1785900000, "codex_core::session::handlers", first_body, side_id),
        )
        legacy.commit()
        legacy.close()

        report = self.side_list(
            "--query", "release checklist", "--scan-limit", "2", "--limit", "20"
        )
        candidate = next(item for item in report["candidates"] if item["thread_id"] == side_id)
        self.assertEqual(candidate["user_messages_observed"], 2)
        self.assertEqual(candidate["latest_message_at"], "2026-08-05 03:30 UTC")
        serialized = json.dumps(report)
        self.assertNotIn("sk-abcdefghijklmnop", serialized)
        self.assertNotIn("sk-qrstuvwxyzabcdef", serialized)

    def test_parent_directed_topic_recovers_lost_mapping_and_exact_parent_history(self) -> None:
        side_id = "01aparent-0000-0000-0000-000000000001"
        parent_id = "01aparent-0000-0000-0000-000000000002"
        self.add_state_task(parent_id, title="Unrelated parent title")
        self.add_user_turn(side_id, 1785920000, "Please review the latest option before we continue.")
        self.add_parent_tool_call(
            side_id, parent_id, 1785920001,
            "Assess the landing page HTML lab and report the strongest layout.",
        )
        history = sqlite3.connect(self.home / "thread_history_1.sqlite")
        history.execute(
            """
            CREATE TABLE thread_items (
                thread_id TEXT, turn_id TEXT, item_id TEXT, rollout_ordinal INTEGER,
                created_at_ms INTEGER, item_json TEXT, item_type TEXT,
                updated_at_ordinal INTEGER DEFAULT 0
            )
            """
        )
        history.execute(
            "INSERT INTO thread_items VALUES (?, 'turn-1', 'item-1', 1, ?, ?, 'agentMessage', 0)",
            (
                parent_id,
                1785920002000,
                json.dumps({"type": "agentMessage", "text": "The downstream comparison selected layout B."}),
            ),
        )
        history.commit()
        history.close()

        candidate = self.side_list(
            "--query", "landing page html lab", "--scan-limit", "2", "--limit", "20"
        )["candidates"][0]
        self.assertEqual(candidate["thread_id"], side_id)
        self.assertEqual(candidate["confidence"], "possible")
        self.assertEqual(candidate["recovery_stage"], "parent_directed_evidence")
        self.assertEqual(candidate["parent_thread_id"], parent_id)
        self.assertEqual(candidate["parent_relationship_source"], "allowlisted_parent_directed_tool_call")

        inspected = self.side_inspect(side_id, "--confirm-possible")
        self.assertEqual(inspected["parent_thread_id"], parent_id)
        self.assertEqual(
            inspected["downstream_parent_evidence"][0]["evidence_type"],
            "downstream_parent_evidence",
        )
        self.assertIn("layout B", inspected["downstream_parent_evidence"][0]["text"])
        self.assertTrue(inspected["coverage"]["downstream_parent_evidence"]["bounded_to_exact_parent"])

    def test_parent_conflicts_remain_unresolved_and_do_not_inspect_history(self) -> None:
        side_id = "01aconfl0-0000-0000-0000-000000000001"
        first_parent = "01aconfl0-0000-0000-0000-000000000002"
        second_parent = "01aconfl0-0000-0000-0000-000000000003"
        self.add_state_task(first_parent, title="First parent")
        self.add_state_task(second_parent, title="Second parent")
        self.add_user_turn(side_id, 1785930000, "Investigate the conflicting parent relationship evidence.")
        self.add_parent_tool_call(side_id, first_parent, 1785930001, "First parent prompt")
        self.add_parent_tool_call(side_id, second_parent, 1785930002, "Second parent prompt")

        candidate = self.side_list(
            "--query", "conflicting parent relationship", "--limit", "20"
        )["candidates"][0]
        self.assertEqual(candidate["parent_thread_id"], "")
        self.assertEqual(candidate["parent_relationship_conflicts"], [first_parent, second_parent])

        report = self.side_inspect(side_id, "--confirm-possible")
        self.assertEqual(report["downstream_parent_evidence"], [])
        self.assertEqual(
            report["coverage"]["downstream_parent_evidence"]["status"],
            "not_inspected_parent_unresolved_or_conflicted",
        )

    def test_schema_failure_degrades_classification_and_suppresses_log_only_records(self) -> None:
        connection = sqlite3.connect(self.home / "state_5.sqlite")
        connection.execute("DROP TABLE threads")
        connection.execute("CREATE TABLE threads (id TEXT PRIMARY KEY, title TEXT)")
        connection.commit()
        connection.close()

        report = self.side_list("--query", "signed webhook replay", "--limit", "20")
        self.assertEqual(report["candidates"], [])
        self.assertEqual(report["coverage"]["classification"]["status"], "degraded")
        self.assertTrue(report["coverage"]["classification"]["fail_safe_log_only_exclusion"])

        inspection = self.side_inspect(self.likely_side_id, expected=1)
        self.assertIn("classification coverage is degraded", inspection["error"])

    def test_partial_log_schema_failure_is_reported_without_hiding_readable_sources(self) -> None:
        legacy_dir = self.home / "sqlite"
        legacy_dir.mkdir(exist_ok=True)
        legacy = sqlite3.connect(legacy_dir / "logs_2.sqlite")
        legacy.execute("CREATE TABLE logs (thread_id TEXT, ts INTEGER)")
        legacy.commit()
        legacy.close()

        report = self.side_list("--query", "signed webhook replay", "--limit", "20")
        self.assertEqual(report["candidates"][0]["thread_id"], self.likely_side_id)
        legacy_coverage = next(
            item for item in report["coverage"]["log_sources"]
            if item["source"] == "legacy logs_2.sqlite"
        )
        self.assertEqual(legacy_coverage["status"], "schema_mismatch")
        self.assertIn("legacy logs_2.sqlite", report["coverage"]["sources"]["unavailable"])

    def test_database_registered_non_side_sources_never_enter_candidate_pool(self) -> None:
        excluded = {
            "01aexclude-0000-0000-0000-000000000001": "subagent",
            "01aexclude-0000-0000-0000-000000000002": "guardian",
            "01aexclude-0000-0000-0000-000000000003": "automation",
            "01aexclude-0000-0000-0000-000000000004": "user",
        }
        for index, (thread_id, source) in enumerate(excluded.items()):
            self.add_state_task(thread_id, source=source, title=f"{source} task")
            self.add_user_turn(thread_id, 1785940000 + index, "Unique forbidden topic candidate text.")
        report = self.side_list("--query", "forbidden topic candidate", "--limit", "20")
        self.assertEqual(report["candidates"], [])

    def test_narrowed_pagination_is_stable_and_reports_hidden_weak_matches(self) -> None:
        for index in range(3):
            self.add_user_turn(
                f"01aweak00-0000-0000-0000-00000000000{index}",
                1785950000 + index,
                f"Inspect stable pagination marker {index}.",
            )
        args = (
            "--query", "stable pagination marker", "--scan-limit", "1", "--limit", "1",
        )
        first = self.side_list(*args)
        repeated = self.side_list(*args)
        self.assertEqual(first["candidates"][0]["thread_id"], repeated["candidates"][0]["thread_id"])
        self.assertEqual(first["pagination"], repeated["pagination"])
        self.assertEqual(first["pagination"]["confidence_counts"]["possible"], 3)
        self.assertEqual(first["coverage"]["weak_candidates"]["not_displayed_on_page"], 2)

    def test_side_inspect_reports_source_specific_coverage(self) -> None:
        report = self.side_inspect(self.side_id)
        self.assertEqual(report["source_type"], "side_chat_confirmed")
        self.assertIn("Batch 013A", report["visible_messages"][0]["text"])
        coverage = report["coverage"]
        self.assertTrue(coverage["side_user_turns"]["searched"])
        self.assertTrue(coverage["side_user_turns"]["found"])
        self.assertEqual(coverage["ordinary_side_assistant_prose"]["status"], "unavailable_body_markers_only")
        self.assertEqual(coverage["tool_activity"]["status"], "allowlisted_only")
        self.assertEqual(coverage["downstream_parent_evidence"]["status"], "not_present")
        self.assertIsNone(coverage["ordinary_side_assistant_prose"]["found"])
        self.assertTrue(coverage["raw_tool_inputs_and_outputs_excluded"])
        self.assertNotIn("assistant_message_bodies_available", coverage)
        self.assertNotIn("parent-payload-must-stay-excluded", json.dumps(report))
        self.assertIn("does not establish", coverage["note"])

    def test_side_inspect_requires_confirmation_for_possible_candidate(self) -> None:
        blocked_report = self.side_inspect(self.possible_side_id, expected=1)
        self.assertTrue(blocked_report["confirmation_required"])
        self.assertEqual(blocked_report["candidate"]["confidence"], "possible")
        self.assertNotIn("visible_messages", blocked_report)

        confirmed_report = self.side_inspect(self.possible_side_id, "--confirm-possible")
        self.assertEqual(confirmed_report["confidence"], "possible")
        self.assertIn("rare adapter edge case", confirmed_report["visible_messages"][0]["text"])

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
        self.assertIn("Side chat (confirmed)", instructions)
        self.assertIn("Likely Side chat", instructions)
        self.assertIn("Possible Side chat", instructions)
        self.assertIn("Group numbered choices by Codex project", instructions)
        self.assertIn("relative age of its latest actual user message", instructions)
        self.assertIn("Discover local Side chats first", instructions)
        self.assertIn("side-list", instructions)
        self.assertIn("side-inspect", instructions)
        self.assertIn("legacy archive commands are exact-record fallbacks only", instructions)
        self.assertIn("Candidate selection and `side-inspect` are intermediate steps, not completion", instructions)
        self.assertIn("Bounded downstream parent evidence", instructions)
        self.assertIn("Missing title or workspace is a coverage gap", handoff)
        self.assertIn("Type: Side chat", handoff)
        self.assertIn("Side user turns, ordinary Side assistant prose, tool activity, downstream parent evidence", handoff)

    def test_local_discovery_precedes_visible_supplements(self) -> None:
        instructions = SKILL.read_text(encoding="utf-8")
        local = instructions.index("## 1. Discover local Side chats first")
        visible = instructions.index("## 2. Supplement with visible evidence")
        absent = instructions.index("## 3. Handle absence and classification honestly")

        self.assertLess(local, visible)
        self.assertLess(visible, absent)
        self.assertIn("These are supplements, not a prerequisite for local discovery", instructions)
        self.assertIn("Do not falsely say the skill cannot search automatically", instructions)
        self.assertIn("Use partial evidence", instructions)


if __name__ == "__main__":
    unittest.main()
