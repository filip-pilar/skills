from __future__ import annotations

import gzip
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "extract_history.py"
SPEC = importlib.util.spec_from_file_location("extract_history", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def record(kind: str, payload: dict, timestamp: str) -> dict:
    return {"timestamp": timestamp, "type": kind, "payload": payload}


def skill_context(body: str, path: str = "/skills/sample-skill/SKILL.md") -> dict:
    return record(
        "response_item",
        {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": (
                        "<skill>\n<name>sample-skill</name>\n"
                        f"<path>{path}</path>\n{body}\n</skill>"
                    ),
                }
            ],
        },
        "2026-07-20T10:01:02Z",
    )


class AuditorExtractorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)
        self.sessions = self.home / "sessions" / "2026" / "07" / "20"
        self.sessions.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_session(
        self,
        session_id: str,
        turns: list[list[dict]],
        *,
        source: object = "vscode",
        thread_source: str = "user",
        developer_text: str | None = None,
    ) -> None:
        path = self.sessions / f"rollout-2026-07-20T10-00-00-{session_id}.jsonl"
        rows = [
            record(
                "session_meta",
                {
                    "id": session_id,
                    "timestamp": "2026-07-20T10:00:00Z",
                    "cwd": "/work/example",
                    "source": source,
                    "thread_source": thread_source,
                },
                "2026-07-20T10:00:00Z",
            )
        ]
        for index, turn_rows in enumerate(turns, 1):
            turn_id = f"{session_id}-turn-{index}"
            rows.append(
                record(
                    "event_msg",
                    {"type": "task_started", "turn_id": turn_id},
                    f"2026-07-20T10:0{index}:00Z",
                )
            )
            if developer_text:
                rows.append(
                    record(
                        "response_item",
                        {
                            "type": "message",
                            "role": "developer",
                            "content": [{"type": "input_text", "text": developer_text}],
                        },
                        f"2026-07-20T10:0{index}:01Z",
                    )
                )
            for row in turn_rows:
                payload = dict(row["payload"])
                if payload.get("type") in {"task_complete", "turn_aborted"}:
                    payload.setdefault("turn_id", turn_id)
                rows.append(
                    {
                        "timestamp": row["timestamp"],
                        "type": row["type"],
                        "payload": payload,
                    }
                )
        path.write_text(
            "".join(json.dumps(row) + "\n" for row in rows),
            encoding="utf-8",
        )

    def report(self, *extra: str) -> dict:
        args = MODULE.parse_args(
            [
                "--skill",
                "sample-skill",
                "--codex-home",
                str(self.home),
                "--since",
                "2026-07-01",
                "--format",
                "json",
                *extra,
            ]
        )
        return MODULE.build_report(args)

    def test_catalogue_presence_is_exposure_not_invocation(self) -> None:
        self.write_session(
            "catalogue-only",
            [
                [
                    record(
                        "event_msg",
                        {"type": "user_message", "message": "Explain this code."},
                        "2026-07-20T10:01:02Z",
                    ),
                    record(
                        "event_msg",
                        {"type": "task_complete", "last_agent_message": "Done."},
                        "2026-07-20T10:01:03Z",
                    ),
                ]
            ],
            developer_text=(
                "- sample-skill: Example. "
                "(file: /skills/sample-skill/SKILL.md)"
            ),
        )
        report = self.report()
        self.assertEqual(report["summary"]["explicit_invocations"], 0)
        self.assertEqual(
            report["coverage"]["sessions_with_skill_exposed_in_context"], 1
        )

    def test_historical_discussion_is_not_invocation(self) -> None:
        self.write_session(
            "discussion",
            [
                [
                    record(
                        "event_msg",
                        {
                            "type": "user_message",
                            "message": (
                                "Use historical $sample-skill invocations as a test case."
                            ),
                        },
                        "2026-07-20T10:01:02Z",
                    ),
                    record(
                        "event_msg",
                        {"type": "task_complete", "last_agent_message": "Reviewed."},
                        "2026-07-20T10:01:03Z",
                    ),
                ]
            ],
        )
        self.assertEqual(self.report()["summary"]["explicit_invocations"], 0)

    def test_picker_link_creates_exact_version_episode(self) -> None:
        self.write_session(
            "picker-link",
            [
                [
                    record(
                        "event_msg",
                        {
                            "type": "user_message",
                            "message": (
                                "[$sample-skill]"
                                "(/Users/me/.codex/skills/sample-skill/SKILL.md)"
                            ),
                        },
                        "2026-07-20T10:01:02Z",
                    ),
                    skill_context("---\nname: sample-skill\n---\nBody"),
                    record(
                        "event_msg",
                        {"type": "task_complete", "last_agent_message": "Done."},
                        "2026-07-20T10:01:03Z",
                    ),
                ]
            ],
        )
        report = self.report()
        episode = report["episodes"][0]
        self.assertEqual(episode["version"]["status"], "exact")
        digest = episode["version"]["content_sha256"]
        self.assertEqual(
            report["version_cohorts"]["exact"][digest]["explicit_episode_ids"],
            [episode["episode_id"]],
        )

    def test_current_skill_path_labels_observed_exact_cohort(self) -> None:
        current = self.home / "current" / "SKILL.md"
        current.parent.mkdir()
        current.write_text("current body\n", encoding="utf-8")
        self.write_session(
            "current-version",
            [
                [
                    record(
                        "event_msg",
                        {"type": "user_message", "message": "$sample-skill"},
                        "2026-07-20T10:01:02Z",
                    ),
                    skill_context("current body"),
                    record(
                        "event_msg",
                        {"type": "task_complete", "last_agent_message": "Done."},
                        "2026-07-20T10:01:03Z",
                    ),
                ]
            ],
        )
        report = self.report("--current-skill-path", str(current))
        self.assertEqual(report["current_version"]["status"], "observed_explicit")
        self.assertEqual(
            report["current_version"]["explicit_episode_ids"],
            ["current-version:current-version-turn-1"],
        )

    def test_current_skill_path_labels_unobserved_contract(self) -> None:
        current = self.home / "current" / "SKILL.md"
        current.parent.mkdir()
        current.write_text("new body\n", encoding="utf-8")
        self.write_session(
            "old-version",
            [
                [
                    record(
                        "event_msg",
                        {"type": "user_message", "message": "$sample-skill"},
                        "2026-07-20T10:01:02Z",
                    ),
                    skill_context("old body"),
                    record(
                        "event_msg",
                        {"type": "task_complete", "last_agent_message": "Done."},
                        "2026-07-20T10:01:03Z",
                    ),
                ]
            ],
        )
        report = self.report("--current-skill-path", str(current))
        self.assertEqual(report["current_version"]["status"], "unobserved")
        self.assertEqual(report["current_version"]["explicit_episode_ids"], [])

    def test_announcement_plus_exact_read_is_an_unconfirmed_candidate(self) -> None:
        self.write_session(
            "inferred",
            [
                [
                    record(
                        "event_msg",
                        {"type": "user_message", "message": "Please review this workflow."},
                        "2026-07-20T10:01:02Z",
                    ),
                    record(
                        "event_msg",
                        {
                            "type": "agent_message",
                            "phase": "commentary",
                            "message": "I’m using sample-skill for this review.",
                        },
                        "2026-07-20T10:01:03Z",
                    ),
                    record(
                        "response_item",
                        {
                            "type": "custom_tool_call",
                            "name": "exec_command",
                            "input": {
                                "cmd": "sed -n '1,200p' /skills/sample-skill/SKILL.md"
                            },
                        },
                        "2026-07-20T10:01:04Z",
                    ),
                    record(
                        "event_msg",
                        {"type": "task_complete", "last_agent_message": "Done."},
                        "2026-07-20T10:01:05Z",
                    ),
                ]
            ],
        )
        report = self.report()
        self.assertEqual(report["episodes"], [])
        episode = report["inferred_candidates"][0]
        self.assertEqual(episode["invocation"]["kind"], "inferred_candidate")
        self.assertEqual(
            episode["invocation"]["confidence"], "requires_adjudication"
        )
        self.assertTrue(episode["invocation"]["adjudication_required"])
        self.assertEqual(report["summary"]["inferred_candidates"], 1)

    def test_announcement_alone_is_not_an_inferred_candidate(self) -> None:
        self.write_session(
            "announcement-only",
            [
                [
                    record(
                        "event_msg",
                        {"type": "user_message", "message": "Review this workflow."},
                        "2026-07-20T10:01:02Z",
                    ),
                    record(
                        "event_msg",
                        {
                            "type": "agent_message",
                            "phase": "commentary",
                            "message": "I’m using sample-skill for this review.",
                        },
                        "2026-07-20T10:01:03Z",
                    ),
                    record(
                        "event_msg",
                        {"type": "task_complete", "last_agent_message": "Done."},
                        "2026-07-20T10:01:04Z",
                    ),
                ]
            ],
        )
        self.assertEqual(self.report()["summary"]["inferred_candidates"], 0)

    def test_backticked_delegation_request_is_explicit(self) -> None:
        self.write_session(
            "backticked",
            [
                [
                    record(
                        "event_msg",
                        {
                            "type": "user_message",
                            "message": (
                                "<codex_delegation><input>"
                                "Run `$sample-skill` on this task."
                                "</input></codex_delegation>"
                            ),
                        },
                        "2026-07-20T10:01:02Z",
                    ),
                    skill_context("current body"),
                    record(
                        "event_msg",
                        {"type": "task_complete", "last_agent_message": "Done."},
                        "2026-07-20T10:01:03Z",
                    ),
                ]
            ],
        )
        report = self.report()
        self.assertEqual(report["summary"]["explicit_invocations"], 1)
        self.assertEqual(report["summary"]["inferred_candidates"], 0)

    def test_skill_review_evidence_remains_a_candidate(self) -> None:
        self.write_session(
            "review-candidate",
            [
                [
                    record(
                        "event_msg",
                        {
                            "type": "user_message",
                            "message": "Audit how sample-skill behaves in history.",
                        },
                        "2026-07-20T10:01:02Z",
                    ),
                    skill_context("current body"),
                    record(
                        "event_msg",
                        {
                            "type": "agent_message",
                            "phase": "commentary",
                            "message": (
                                "I’ll use sample-skill only as the audited contract."
                            ),
                        },
                        "2026-07-20T10:01:03Z",
                    ),
                    record(
                        "response_item",
                        {
                            "type": "custom_tool_call",
                            "name": "exec_command",
                            "input": {"cmd": "sed -n 1,200p /skills/sample-skill/SKILL.md"},
                        },
                        "2026-07-20T10:01:04Z",
                    ),
                    record(
                        "event_msg",
                        {"type": "task_complete", "last_agent_message": "Audited."},
                        "2026-07-20T10:01:05Z",
                    ),
                ]
            ],
        )
        report = self.report()
        self.assertEqual(report["episodes"], [])
        self.assertEqual(len(report["inferred_candidates"]), 1)

    def test_embedded_guardian_transcript_is_not_invocation(self) -> None:
        self.write_session(
            "guardian-transcript",
            [
                [
                    record(
                        "event_msg",
                        {
                            "type": "user_message",
                            "message": (
                                "The following is the Codex agent history whose request "
                                "action you are assessing.\n>>> TRANSCRIPT START\n"
                                "[1] user: $sample-skill"
                            ),
                        },
                        "2026-07-20T10:01:02Z",
                    ),
                    record(
                        "event_msg",
                        {"type": "task_complete", "last_agent_message": "Assessed."},
                        "2026-07-20T10:01:03Z",
                    ),
                ]
            ],
        )
        self.assertEqual(self.report()["summary"]["explicit_invocations"], 0)

    def test_follow_up_evidence_is_neutral_and_redacted(self) -> None:
        self.write_session(
            "follow-up",
            [
                [
                    record(
                        "event_msg",
                        {"type": "user_message", "message": "$sample-skill"},
                        "2026-07-20T10:01:02Z",
                    ),
                    record(
                        "event_msg",
                        {
                            "type": "agent_message",
                            "phase": "commentary",
                            "message": "I’m using sample-skill for this review.",
                        },
                        "2026-07-20T10:01:03Z",
                    ),
                    record(
                        "response_item",
                        {
                            "type": "custom_tool_call",
                            "name": "exec_command",
                            "input": {
                                "cmd": "sed -n '1,200p' /skills/sample-skill/SKILL.md"
                            },
                        },
                        "2026-07-20T10:01:04Z",
                    ),
                    record(
                        "event_msg",
                        {"type": "task_complete", "last_agent_message": "Ready."},
                        "2026-07-20T10:01:05Z",
                    ),
                ],
                [
                    record(
                        "event_msg",
                        {
                            "type": "user_message",
                            "message": "Please keep the result narrower.",
                        },
                        "2026-07-20T10:02:02Z",
                    ),
                    record(
                        "response_item",
                        {
                            "type": "custom_tool_call",
                            "name": "exec_command",
                            "input": {"cmd": "sensitive-command --token secret"},
                        },
                        "2026-07-20T10:02:03Z",
                    ),
                    record(
                        "event_msg",
                        {"type": "task_complete", "last_agent_message": "Revised."},
                        "2026-07-20T10:02:04Z",
                    ),
                ],
            ],
        )
        episode = self.report()["episodes"][0]
        self.assertEqual(
            episode["invocation"]["evidence"],
            [
                "user_explicit_request",
                "assistant_announcement",
                "exact_skill_file_read",
            ],
        )
        self.assertEqual(
            episode["follow_up"]["user_messages"][0]["preview"],
            "Please keep the result narrower.",
        )
        self.assertEqual(
            episode["follow_up"]["tool_activity"]["by_name"],
            {"exec_command": 2},
        )
        rendered = json.dumps(episode)
        self.assertNotIn("sensitive-command", rendered)
        self.assertNotIn("correction_candidates", rendered)
        self.assertNotIn("gate_candidates", rendered)

    def test_long_activity_is_compacted_and_goal_status_is_labeled_requested(self) -> None:
        rows = [
            record(
                "event_msg",
                {
                    "type": "agent_message",
                    "phase": "commentary",
                    "message": f"Progress message {index}",
                },
                "2026-07-20T10:01:03Z",
            )
            for index in range(10)
        ]
        rows.extend(
            [
                record(
                    "response_item",
                    {
                        "type": "custom_tool_call",
                        "name": "exec_command",
                        "input": {"cmd": f"private-command-{index}"},
                    },
                    "2026-07-20T10:01:04Z",
                )
                for index in range(12)
            ]
        )
        rows.extend(
            [
                record(
                    "response_item",
                    {
                        "type": "custom_tool_call",
                        "name": "update_goal",
                        "input": {"status": "complete"},
                    },
                    "2026-07-20T10:01:05Z",
                ),
                record(
                    "event_msg",
                    {"type": "task_complete", "last_agent_message": "Finished."},
                    "2026-07-20T10:01:06Z",
                ),
            ]
        )
        self.write_session(
            "long-activity",
            [
                [
                    record(
                        "event_msg",
                        {"type": "user_message", "message": "$sample-skill"},
                        "2026-07-20T10:01:02Z",
                    ),
                    *rows,
                ]
            ],
        )
        episode = self.report()["episodes"][0]
        assistant = episode["follow_up"]["assistant_activity"]
        tools = episode["follow_up"]["tool_activity"]
        self.assertEqual(assistant["message_count"], 11)
        self.assertEqual(assistant["sample_count"], 4)
        self.assertEqual(assistant["omitted_count"], 7)
        self.assertEqual(tools["call_count"], 13)
        self.assertEqual(
            tools["by_name"], {"exec_command": 12, "update_goal": 1}
        )
        self.assertEqual(
            tools["goal_events"],
            [
                {
                    "turn_id": "long-activity-turn-1",
                    "action": "update_goal",
                    "requested_status": "complete",
                }
            ],
        )
        self.assertNotIn("private-command", json.dumps(episode))

    def test_each_invocation_gets_its_turn_version(self) -> None:
        self.write_session(
            "two-versions",
            [
                [
                    record(
                        "event_msg",
                        {"type": "user_message", "message": "$sample-skill"},
                        "2026-07-20T10:01:02Z",
                    ),
                    skill_context("version one"),
                    record(
                        "event_msg",
                        {"type": "task_complete", "last_agent_message": "One."},
                        "2026-07-20T10:01:03Z",
                    ),
                ],
                [
                    record(
                        "event_msg",
                        {"type": "user_message", "message": "Use $sample-skill again."},
                        "2026-07-20T10:02:02Z",
                    ),
                    skill_context("version two"),
                    record(
                        "event_msg",
                        {"type": "task_complete", "last_agent_message": "Two."},
                        "2026-07-20T10:02:03Z",
                    ),
                ],
            ],
        )
        report = self.report()
        self.assertEqual(report["summary"]["explicit_invocations"], 2)
        self.assertEqual(report["summary"]["distinct_exact_versions"], 2)
        first, second = report["episodes"]
        self.assertNotEqual(
            first["version"]["content_sha256"],
            second["version"]["content_sha256"],
        )
        self.assertEqual(
            first["follow_up"]["turn_states"],
            [{"turn_id": "two-versions-turn-1", "terminal": "turn_completed"}],
        )

    def test_multiple_attached_bodies_make_version_ambiguous(self) -> None:
        self.write_session(
            "ambiguous",
            [
                [
                    record(
                        "event_msg",
                        {"type": "user_message", "message": "$sample-skill"},
                        "2026-07-20T10:01:02Z",
                    ),
                    skill_context("version one"),
                    skill_context("version two", "/other/sample-skill/SKILL.md"),
                    record(
                        "event_msg",
                        {"type": "task_complete", "last_agent_message": "Done."},
                        "2026-07-20T10:01:03Z",
                    ),
                ]
            ],
        )
        report = self.report()
        episode = report["episodes"][0]
        self.assertEqual(episode["version"]["status"], "ambiguous")
        self.assertEqual(
            report["version_cohorts"]["ambiguous"]["explicit_episode_ids"],
            [episode["episode_id"]],
        )

    def test_missing_attached_body_is_unversioned(self) -> None:
        self.write_session(
            "unversioned",
            [
                [
                    record(
                        "event_msg",
                        {"type": "user_message", "message": "Please use $sample-skill."},
                        "2026-07-20T10:01:02Z",
                    ),
                    record(
                        "event_msg",
                        {"type": "task_complete", "last_agent_message": "Done."},
                        "2026-07-20T10:01:03Z",
                    ),
                ]
            ],
        )
        report = self.report()
        self.assertEqual(report["episodes"][0]["version"]["status"], "unversioned")
        self.assertEqual(report["summary"]["unversioned_explicit_episodes"], 1)

    def test_aborted_turn_is_observed_without_failure_claim(self) -> None:
        self.write_session(
            "aborted",
            [
                [
                    record(
                        "event_msg",
                        {"type": "user_message", "message": "$sample-skill"},
                        "2026-07-20T10:01:02Z",
                    ),
                    record(
                        "event_msg",
                        {"type": "turn_aborted", "reason": "user_cancelled"},
                        "2026-07-20T10:01:03Z",
                    ),
                ]
            ],
        )
        episode = self.report()["episodes"][0]
        self.assertEqual(
            episode["follow_up"]["turn_states"][0]["terminal"],
            "turn_aborted",
        )
        self.assertNotIn("failed", json.dumps(episode))

    def test_warm_cache_reuses_unchanged_session_without_changing_evidence(
        self,
    ) -> None:
        self.write_session(
            "cached",
            [
                [
                    record(
                        "event_msg",
                        {"type": "user_message", "message": "$sample-skill"},
                        "2026-07-20T10:01:02Z",
                    ),
                    skill_context("current body"),
                    record(
                        "event_msg",
                        {"type": "task_complete", "last_agent_message": "Done."},
                        "2026-07-20T10:01:03Z",
                    ),
                ]
            ],
        )
        cache = self.home / "custom-cache.json"
        cold = self.report("--cache-path", str(cache))
        warm = self.report("--cache-path", str(cache))

        self.assertEqual(cold["coverage"]["cache"]["status"], "created")
        self.assertEqual(cold["coverage"]["cache"]["hits"], 0)
        self.assertEqual(cold["coverage"]["cache"]["misses"], 1)
        self.assertEqual(warm["coverage"]["cache"]["status"], "warm")
        self.assertEqual(warm["coverage"]["cache"]["hits"], 1)
        self.assertEqual(warm["coverage"]["cache"]["misses"], 0)
        self.assertEqual(cold["episodes"], warm["episodes"])
        self.assertEqual(cold["summary"], warm["summary"])
        self.assertEqual(cold["version_cohorts"], warm["version_cohorts"])

    def test_cache_invalidates_only_the_changed_session(self) -> None:
        for session_id in ("stable", "changing"):
            self.write_session(
                session_id,
                [
                    [
                        record(
                            "event_msg",
                            {"type": "user_message", "message": "$sample-skill"},
                            "2026-07-20T10:01:02Z",
                        ),
                        record(
                            "event_msg",
                            {"type": "task_complete", "last_agent_message": "Done."},
                            "2026-07-20T10:01:03Z",
                        ),
                    ]
                ],
            )
        cache = self.home / "incremental-cache.json"
        self.report("--cache-path", str(cache))
        self.write_session(
            "changing",
            [
                [
                    record(
                        "event_msg",
                        {"type": "user_message", "message": "$sample-skill"},
                        "2026-07-20T10:01:02Z",
                    ),
                    record(
                        "event_msg",
                        {"type": "task_complete", "last_agent_message": "Done."},
                        "2026-07-20T10:01:03Z",
                    ),
                ],
                [
                    record(
                        "event_msg",
                        {
                            "type": "user_message",
                            "message": "Use $sample-skill again.",
                        },
                        "2026-07-20T10:02:02Z",
                    ),
                    record(
                        "event_msg",
                        {"type": "task_complete", "last_agent_message": "Again."},
                        "2026-07-20T10:02:03Z",
                    ),
                ],
            ],
        )
        report = self.report("--cache-path", str(cache))
        self.assertEqual(report["coverage"]["cache"]["status"], "updated")
        self.assertEqual(report["coverage"]["cache"]["hits"], 1)
        self.assertEqual(report["coverage"]["cache"]["misses"], 1)
        self.assertEqual(report["summary"]["explicit_invocations"], 3)

    def test_invalid_cache_is_rebuilt(self) -> None:
        self.write_session(
            "recover",
            [
                [
                    record(
                        "event_msg",
                        {"type": "user_message", "message": "$sample-skill"},
                        "2026-07-20T10:01:02Z",
                    ),
                    record(
                        "event_msg",
                        {"type": "task_complete", "last_agent_message": "Done."},
                        "2026-07-20T10:01:03Z",
                    ),
                ]
            ],
        )
        cache = self.home / "broken-cache.json"
        cache.write_text("{not-json", encoding="utf-8")
        report = self.report("--cache-path", str(cache))
        self.assertEqual(report["coverage"]["cache"]["status"], "rebuilt")
        self.assertEqual(report["coverage"]["cache"]["misses"], 1)
        self.assertEqual(report["summary"]["explicit_invocations"], 1)

    def test_malformed_matching_entry_is_reparsed(self) -> None:
        self.write_session(
            "malformed-entry",
            [
                [
                    record(
                        "event_msg",
                        {"type": "user_message", "message": "$sample-skill"},
                        "2026-07-20T10:01:02Z",
                    ),
                    record(
                        "event_msg",
                        {"type": "task_complete", "last_agent_message": "Done."},
                        "2026-07-20T10:01:03Z",
                    ),
                ]
            ],
        )
        session = next(self.sessions.glob("*.jsonl")).resolve()
        stat = session.stat()
        cache = self.home / "malformed-entry.json.gz"
        with gzip.open(cache, "wt", encoding="utf-8") as handle:
            json.dump(
                {
                    "cache_schema_version": MODULE.CACHE_SCHEMA_VERSION,
                    "skill": "sample-skill",
                    "entries": {
                        str(session): {
                            "size": stat.st_size,
                            "mtime_ns": stat.st_mtime_ns,
                            "session": {"meta": "invalid", "turns": []},
                        }
                    },
                },
                handle,
            )
        report = self.report("--cache-path", str(cache))
        self.assertEqual(report["coverage"]["cache"]["status"], "updated")
        self.assertEqual(report["coverage"]["cache"]["hits"], 0)
        self.assertEqual(report["coverage"]["cache"]["misses"], 1)
        self.assertEqual(report["summary"]["explicit_invocations"], 1)

    def test_cache_omits_raw_tool_inputs_and_full_messages(self) -> None:
        long_message = "Visible progress. " + ("x" * 300) + " FULL_MESSAGE_SECRET"
        self.write_session(
            "redacted-cache",
            [
                [
                    record(
                        "event_msg",
                        {"type": "user_message", "message": "$sample-skill"},
                        "2026-07-20T10:01:02Z",
                    ),
                    record(
                        "event_msg",
                        {
                            "type": "agent_message",
                            "phase": "commentary",
                            "message": long_message,
                        },
                        "2026-07-20T10:01:03Z",
                    ),
                    record(
                        "response_item",
                        {
                            "type": "custom_tool_call",
                            "name": "exec_command",
                            "input": {"cmd": "private-command --token RAW_TOOL_SECRET"},
                        },
                        "2026-07-20T10:01:04Z",
                    ),
                    record(
                        "event_msg",
                        {"type": "task_complete", "last_agent_message": "Done."},
                        "2026-07-20T10:01:05Z",
                    ),
                ]
            ],
        )
        cache = self.home / "redacted-cache.json"
        self.report("--cache-path", str(cache))
        with gzip.open(cache, "rt", encoding="utf-8") as handle:
            rendered = handle.read()
        self.assertNotIn("RAW_TOOL_SECRET", rendered)
        self.assertNotIn("private-command", rendered)
        self.assertNotIn("FULL_MESSAGE_SECRET", rendered)

    def test_no_cache_disables_reads_and_writes(self) -> None:
        self.write_session(
            "uncached",
            [
                [
                    record(
                        "event_msg",
                        {"type": "user_message", "message": "$sample-skill"},
                        "2026-07-20T10:01:02Z",
                    ),
                    record(
                        "event_msg",
                        {"type": "task_complete", "last_agent_message": "Done."},
                        "2026-07-20T10:01:03Z",
                    ),
                ]
            ],
        )
        report = self.report("--no-cache")
        expected = (
            self.home
            / "cache"
            / "skill-usage-auditor"
            / "sample-skill.json.gz"
        )
        self.assertEqual(report["coverage"]["cache"]["status"], "disabled")
        self.assertFalse(report["coverage"]["cache"]["enabled"])
        self.assertEqual(report["coverage"]["cache"]["misses"], 1)
        self.assertFalse(expected.exists())

    def test_subagents_are_excluded_by_default(self) -> None:
        self.write_session(
            "subagent",
            [
                [
                    record(
                        "event_msg",
                        {"type": "user_message", "message": "$sample-skill"},
                        "2026-07-20T10:01:02Z",
                    ),
                    record(
                        "event_msg",
                        {"type": "task_complete", "last_agent_message": "Done."},
                        "2026-07-20T10:01:03Z",
                    ),
                ]
            ],
            source={"subagent": {"other": "worker"}},
            thread_source="subagent",
        )
        self.assertEqual(self.report()["summary"]["explicit_invocations"], 0)
        self.assertEqual(
            self.report("--include-subagents")["summary"]["explicit_invocations"], 1
        )


if __name__ == "__main__":
    unittest.main()
