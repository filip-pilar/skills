#!/usr/bin/env python3
"""Extract neutral, read-only evidence for one skill from local Codex history."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import sqlite3
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = 4
CACHE_SCHEMA_VERSION = 2
CACHE_DIR_NAME = "skill-usage-auditor"


def parse_timestamp(raw: Any) -> datetime | None:
    if not isinstance(raw, str) or not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def normalized_preview(text: str, limit: int = 240) -> str:
    return re.sub(r"\s+", " ", text).strip()[:limit]


def text_digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def message_text(payload: dict[str, Any]) -> str:
    content = payload.get("content")
    if not isinstance(content, list):
        return ""
    return "\n".join(
        item["text"]
        for item in content
        if isinstance(item, dict) and isinstance(item.get("text"), str)
    )


def serialized_tool_input(payload: dict[str, Any]) -> str:
    rendered: list[str] = []
    for value in (payload.get("arguments"), payload.get("input")):
        if isinstance(value, str):
            rendered.append(value)
        elif value is not None:
            try:
                rendered.append(json.dumps(value, sort_keys=True))
            except TypeError:
                rendered.append(str(value))
    return "\n".join(rendered)


def tool_name(payload: dict[str, Any]) -> str:
    value = payload.get("name")
    return value if isinstance(value, str) and value else "unknown"


def tool_arguments(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("input")
    if value is None:
        value = payload.get("arguments")
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def goal_event(payload: dict[str, Any]) -> dict[str, Any] | None:
    name = tool_name(payload).rsplit(".", 1)[-1]
    if name not in {"create_goal", "get_goal", "update_goal"}:
        return None
    arguments = tool_arguments(payload)
    event: dict[str, Any] = {"action": name}
    status = arguments.get("status")
    if name == "update_goal" and isinstance(status, str):
        event["requested_status"] = status
    objective = arguments.get("objective")
    if name == "create_goal" and isinstance(objective, str):
        event["objective_sha256"] = text_digest(objective)
        event["objective_preview"] = normalized_preview(objective)
    return event


def is_subagent(meta: dict[str, Any]) -> bool:
    if meta.get("thread_source") == "subagent":
        return True
    source = meta.get("source")
    if isinstance(source, dict):
        return "subagent" in source
    return isinstance(source, str) and "subagent" in source.lower()


def skill_patterns(skill: str) -> tuple[re.Pattern[str], re.Pattern[str], re.Pattern[str]]:
    escaped = re.escape(skill)
    reference = rf"`?\${escaped}\b`?"
    token = re.compile(rf"(?<![A-Za-z0-9_-])\${escaped}\b", re.IGNORECASE)
    direct = re.compile(
        rf"(?:"
        rf"^\s*{reference}|"
        rf"\[\${escaped}\]\([^)\n]*(?:^|[/\\]){escaped}[/\\]SKILL\.md\)|"
        rf"\b(?:use|run|invoke|call|start)\s+(?:the\s+)?{reference}|"
        rf"\b(?:with|using)\s+{reference}|"
        rf"\blet(?:'|’)s\s+(?:(?:use|run)\s+)?{reference}|"
        rf"\b(?:use|run|invoke|call)\s+(?:the\s+)?{escaped}\s+skill\b"
        rf")",
        re.IGNORECASE,
    )
    announcement = re.compile(
        rf"\b(?:using|following|invoking|"
        rf"i(?:(?:'|’)m| am|(?:'|’)ll| will)\s+(?:using|following|invoking)|"
        rf"i(?:(?:'|’)ll| will)\s+use)\b"
        rf"[^\n]{{0,96}}(?:\$|`)?{escaped}\b",
        re.IGNORECASE,
    )
    return token, direct, announcement


def is_embedded_transcript(text: str) -> bool:
    lowered = text.lower()
    return (
        "the following is the codex agent history whose request action you are assessing"
        in lowered
        or ">>> transcript start" in lowered
    )


def availability_pattern(skill: str) -> re.Pattern[str]:
    escaped = re.escape(skill)
    return re.compile(
        rf"(?:<name>\s*{escaped}\s*</name>|^\s*-\s+{escaped}\s*:|"
        rf"(?:^|[/\\]){escaped}[/\\]SKILL\.md)",
        re.IGNORECASE | re.MULTILINE,
    )


def skill_read_pattern(skill: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?:^|[/\\]){re.escape(skill)}[/\\]SKILL\.md\b", re.IGNORECASE
    )


@dataclass
class ToolCall:
    name: str
    exact_skill_read: bool = False
    goal_event: dict[str, Any] | None = None


@dataclass
class TextEvidence:
    text_sha256: str
    preview: str
    explicit_request: bool = False


@dataclass
class AssistantEvidence:
    phase: str
    text_sha256: str
    preview: str
    announcement: bool = False


@dataclass
class Turn:
    turn_id: str
    started_at: str | None = None
    user_texts: list[TextEvidence] = field(default_factory=list)
    assistant_messages: list[AssistantEvidence] = field(default_factory=list)
    tool_calls: list[ToolCall] = field(default_factory=list)
    skill_contexts: list[dict[str, Any]] = field(default_factory=list)
    terminal: str = "unfinished_turn"
    completed_at: str | None = None


@dataclass
class Session:
    path: Path
    meta: dict[str, Any]
    turns: list[Turn]
    available: bool
    unsupported_user_records: int = 0

    @property
    def session_id(self) -> str:
        value = self.meta.get("id") or self.meta.get("session_id")
        return str(value or self.path.stem)


def read_session(path: Path, skill: str) -> Session | None:
    meta: dict[str, Any] = {}
    turns: list[Turn] = []
    by_id: dict[str, Turn] = {}
    current: Turn | None = None
    available = False
    unsupported_user_records = 0
    token_re, direct_re, announcement_re = skill_patterns(skill)
    read_re = skill_read_pattern(skill)
    availability_re = availability_pattern(skill)
    skill_block_re = re.compile(
        rf"<skill>\s*<name>\s*{re.escape(skill)}\s*</name>\s*"
        rf"<path>(.*?)</path>(.*?)</skill>",
        re.IGNORECASE | re.DOTALL,
    )

    try:
        handle = path.open("r", encoding="utf-8")
    except OSError:
        return None

    with handle:
        for line in handle:
            try:
                record = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            if not isinstance(record, dict):
                continue
            kind = record.get("type")
            payload = record.get("payload")
            if kind == "session_meta" and isinstance(payload, dict):
                if not meta:
                    meta = payload
                continue
            if not isinstance(payload, dict):
                continue

            payload_type = payload.get("type")
            if kind == "event_msg" and payload_type == "task_started":
                turn_id = str(payload.get("turn_id") or f"turn-{len(turns) + 1}")
                current = Turn(turn_id=turn_id, started_at=record.get("timestamp"))
                turns.append(current)
                by_id[turn_id] = current
                continue
            if kind == "event_msg" and payload_type == "user_message":
                if current is None:
                    unsupported_user_records += 1
                    continue
                text = payload.get("message")
                if isinstance(text, str):
                    current.user_texts.append(
                        TextEvidence(
                            text_sha256=text_digest(text),
                            preview=normalized_preview(text),
                            explicit_request=bool(
                                token_re.search(text)
                                and direct_re.search(text)
                                and not is_embedded_transcript(text)
                            ),
                        )
                    )
                continue
            if kind == "event_msg" and payload_type in {
                "agent_message",
                "task_complete",
                "turn_aborted",
            }:
                target = by_id.get(str(payload.get("turn_id") or "")) or current
                if target is None:
                    continue
                if payload_type == "agent_message":
                    text = payload.get("message")
                    if isinstance(text, str):
                        target.assistant_messages.append(
                            AssistantEvidence(
                                phase=str(payload.get("phase") or ""),
                                text_sha256=text_digest(text),
                                preview=normalized_preview(text),
                                announcement=bool(announcement_re.search(text)),
                            )
                        )
                elif payload_type == "task_complete":
                    target.terminal = "turn_completed"
                    target.completed_at = str(
                        payload.get("completed_at") or record.get("timestamp") or ""
                    )
                    final = payload.get("last_agent_message")
                    if isinstance(final, str) and final:
                        target.assistant_messages.append(
                            AssistantEvidence(
                                phase="final",
                                text_sha256=text_digest(final),
                                preview=normalized_preview(final),
                                announcement=bool(announcement_re.search(final)),
                            )
                        )
                else:
                    target.terminal = "turn_aborted"
                    target.completed_at = str(
                        payload.get("completed_at") or record.get("timestamp") or ""
                    )
                continue
            if kind == "response_item" and payload_type == "message":
                role = payload.get("role")
                if role in {"developer", "user"}:
                    context_text = message_text(payload)
                    available = available or bool(availability_re.search(context_text))
                    if role == "user" and current is not None:
                        for match in skill_block_re.finditer(context_text):
                            body = match.group(2).strip()
                            current.skill_contexts.append(
                                {
                                    "path": match.group(1).strip(),
                                    "content_sha256": hashlib.sha256(
                                        body.encode("utf-8")
                                    ).hexdigest(),
                                    "bytes": len(body.encode("utf-8")),
                                }
                            )
                continue
            if kind == "response_item" and payload_type in {
                "function_call",
                "custom_tool_call",
            }:
                if current is not None:
                    serialized_input = serialized_tool_input(payload)
                    current.tool_calls.append(
                        ToolCall(
                            name=tool_name(payload),
                            exact_skill_read=bool(read_re.search(serialized_input)),
                            goal_event=goal_event(payload),
                        )
                    )

    if not meta and not turns:
        return None
    return Session(
        path=path,
        meta=meta,
        turns=turns,
        available=available,
        unsupported_user_records=unsupported_user_records,
    )


def history_paths(codex_home: Path) -> Iterable[Path]:
    for root in (codex_home / "sessions", codex_home / "archived_sessions"):
        if root.is_dir():
            yield from root.rglob("*.jsonl")


def session_cache_record(
    session: Session,
    *,
    include_turns: bool,
) -> dict[str, Any]:
    meta = {
        key: session.meta[key]
        for key in (
            "id",
            "session_id",
            "timestamp",
            "cwd",
            "source",
            "thread_source",
        )
        if key in session.meta
    }
    return {
        "meta": meta,
        "available": session.available,
        "unsupported_user_records": session.unsupported_user_records,
        "turns": [
            {
                "turn_id": turn.turn_id,
                "started_at": turn.started_at,
                "user_texts": [
                    {
                        "text_sha256": text.text_sha256,
                        "preview": text.preview,
                        "explicit_request": text.explicit_request,
                    }
                    for text in turn.user_texts
                ],
                "assistant_messages": [
                    {
                        "phase": message.phase,
                        "text_sha256": message.text_sha256,
                        "preview": message.preview,
                        "announcement": message.announcement,
                    }
                    for message in turn.assistant_messages
                ],
                "tool_calls": [
                    {
                        "name": call.name,
                        "exact_skill_read": call.exact_skill_read,
                        "goal_event": call.goal_event,
                    }
                    for call in turn.tool_calls
                ],
                "skill_contexts": turn.skill_contexts,
                "terminal": turn.terminal,
                "completed_at": turn.completed_at,
            }
            for turn in session.turns
        ],
    } if include_turns else {
        "meta": meta,
        "available": session.available,
        "unsupported_user_records": session.unsupported_user_records,
        "turns": [],
    }


def session_from_cache(path: Path, data: dict[str, Any]) -> Session | None:
    try:
        turns = [
            Turn(
                turn_id=str(turn["turn_id"]),
                started_at=turn.get("started_at"),
                user_texts=[
                    TextEvidence(
                        text_sha256=str(text["text_sha256"]),
                        preview=str(text["preview"]),
                        explicit_request=bool(text.get("explicit_request")),
                    )
                    for text in turn.get("user_texts", [])
                ],
                assistant_messages=[
                    AssistantEvidence(
                        phase=str(message.get("phase") or ""),
                        text_sha256=str(message["text_sha256"]),
                        preview=str(message["preview"]),
                        announcement=bool(message.get("announcement")),
                    )
                    for message in turn.get("assistant_messages", [])
                ],
                tool_calls=[
                    ToolCall(
                        name=str(call.get("name") or "unknown"),
                        exact_skill_read=bool(call.get("exact_skill_read")),
                        goal_event=(
                            call.get("goal_event")
                            if isinstance(call.get("goal_event"), dict)
                            else None
                        ),
                    )
                    for call in turn.get("tool_calls", [])
                ],
                skill_contexts=[
                    context
                    for context in turn.get("skill_contexts", [])
                    if isinstance(context, dict)
                ],
                terminal=str(turn.get("terminal") or "unfinished_turn"),
                completed_at=turn.get("completed_at"),
            )
            for turn in data.get("turns", [])
            if isinstance(turn, dict)
        ]
        meta = data.get("meta")
        if not isinstance(meta, dict):
            return None
        return Session(
            path=path,
            meta=meta,
            turns=turns,
            available=bool(data.get("available")),
            unsupported_user_records=int(data.get("unsupported_user_records") or 0),
        )
    except (KeyError, TypeError, ValueError):
        return None


def cache_path_for(args: argparse.Namespace, codex_home: Path) -> Path:
    if args.cache_path is not None:
        return args.cache_path.expanduser().resolve()
    return codex_home / "cache" / CACHE_DIR_NAME / f"{args.skill}.json.gz"


def load_cache(path: Path, skill: str) -> tuple[dict[str, Any], str]:
    if not path.is_file():
        return {}, "cold"
    try:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}, "invalid"
    if (
        not isinstance(payload, dict)
        or payload.get("cache_schema_version") != CACHE_SCHEMA_VERSION
        or payload.get("skill") != skill
        or not isinstance(payload.get("entries"), dict)
    ):
        return {}, "invalid"
    return payload["entries"], "warm"


def write_cache(
    path: Path,
    skill: str,
    entries: dict[str, Any],
) -> bool:
    temporary_path: Path | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with tempfile.NamedTemporaryFile(
            "wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
        with gzip.open(
            temporary_path,
            "wt",
            encoding="utf-8",
            compresslevel=6,
        ) as handle:
            json.dump(
                {
                    "cache_schema_version": CACHE_SCHEMA_VERSION,
                    "skill": skill,
                    "entries": entries,
                },
                handle,
                separators=(",", ":"),
                sort_keys=True,
            )
            handle.write("\n")
        temporary_path.chmod(0o600)
        temporary_path.replace(path)
        return True
    except OSError:
        return False
    finally:
        if temporary_path is not None and temporary_path.exists():
            try:
                temporary_path.unlink()
            except OSError:
                pass


def load_titles(codex_home: Path) -> dict[str, str]:
    titles: dict[str, str] = {}
    for path in (
        codex_home / "sqlite" / "state_5.sqlite",
        codex_home / "state_5.sqlite",
    ):
        if not path.is_file():
            continue
        try:
            connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
            rows = connection.execute("SELECT id, title FROM threads").fetchall()
            connection.close()
        except sqlite3.Error:
            continue
        for thread_id, title in rows:
            if isinstance(thread_id, str) and isinstance(title, str):
                titles.setdefault(thread_id, title)
    return titles


def unique_contexts(turn: Turn) -> list[dict[str, Any]]:
    return list(
        {
            (item["path"], item["content_sha256"]): item
            for item in turn.skill_contexts
        }.values()
    )


def version_for(turn: Turn) -> dict[str, Any]:
    contexts = unique_contexts(turn)
    hashes = sorted({item["content_sha256"] for item in contexts})
    if len(hashes) == 1:
        return {
            "status": "exact",
            "content_sha256": hashes[0],
            "contexts": contexts,
        }
    return {
        "status": "ambiguous" if hashes else "unversioned",
        "contexts": contexts,
    }


def preview_record(
    evidence: TextEvidence | AssistantEvidence,
    omit_previews: bool,
    **fields: Any,
) -> dict[str, Any]:
    item = {**fields, "text_sha256": evidence.text_sha256}
    if not omit_previews:
        item["preview"] = evidence.preview
    return item


def compact_title(title: str | None, omit_previews: bool) -> dict[str, Any] | None:
    if not title:
        return None
    return preview_record(
        TextEvidence(
            text_sha256=text_digest(title),
            preview=normalized_preview(title),
        ),
        omit_previews,
    )


def compact_assistant_activity(
    window: list[Turn],
    omit_previews: bool,
) -> dict[str, Any]:
    samples: list[dict[str, Any]] = []
    total = 0
    phases: Counter[str] = Counter()
    for turn in window:
        unique: list[AssistantEvidence] = []
        seen: set[str] = set()
        for message in turn.assistant_messages:
            if message.text_sha256 in seen:
                continue
            seen.add(message.text_sha256)
            unique.append(message)
        total += len(unique)
        phases.update(message.phase or "unspecified" for message in unique)
        selected = unique if len(unique) <= 4 else unique[:2] + unique[-2:]
        for message in selected:
            samples.append(
                preview_record(
                    message,
                    omit_previews,
                    turn_id=turn.turn_id,
                    phase=message.phase,
                )
            )
    return {
        "message_count": total,
        "sample_count": len(samples),
        "omitted_count": total - len(samples),
        "by_phase": dict(sorted(phases.items())),
        "samples": samples,
    }


def compact_tool_activity(
    window: list[Turn],
    omit_previews: bool,
) -> dict[str, Any]:
    by_name: Counter[str] = Counter()
    by_turn: list[dict[str, Any]] = []
    goal_events: list[dict[str, Any]] = []
    total = 0
    for turn in window:
        turn_counts = Counter(call.name for call in turn.tool_calls)
        by_name.update(turn_counts)
        total += len(turn.tool_calls)
        if turn_counts:
            by_turn.append(
                {
                    "turn_id": turn.turn_id,
                    "count": sum(turn_counts.values()),
                    "by_name": dict(sorted(turn_counts.items())),
                }
            )
        for call in turn.tool_calls:
            if call.goal_event is None:
                continue
            event = {
                "turn_id": turn.turn_id,
                "action": call.goal_event["action"],
            }
            if "requested_status" in call.goal_event:
                event["requested_status"] = call.goal_event["requested_status"]
            objective_digest = call.goal_event.get("objective_sha256")
            if isinstance(objective_digest, str):
                event["objective_sha256"] = objective_digest
                if not omit_previews:
                    event["objective_preview"] = call.goal_event.get(
                        "objective_preview", ""
                    )
            goal_events.append(event)
    return {
        "call_count": total,
        "by_name": dict(sorted(by_name.items())),
        "by_turn": by_turn,
        "goal_events": goal_events,
    }


def episode_for(
    session: Session,
    invocation_index: int,
    invocation_kind: str,
    skill: str,
    title: str | None,
    omit_previews: bool,
    follow_up_turns: int,
    next_invocation_index: int | None,
) -> dict[str, Any]:
    turn = session.turns[invocation_index]
    end = min(
        next_invocation_index if next_invocation_index is not None else len(session.turns),
        invocation_index + follow_up_turns + 1,
    )
    window = session.turns[invocation_index:end]

    turn_user_messages = [
        preview_record(text, omit_previews) for text in turn.user_texts
    ]

    announcements = [
        message
        for message in turn.assistant_messages
        if message.announcement
    ]
    exact_read = any(call.exact_skill_read for call in turn.tool_calls)
    version = version_for(turn)
    evidence = ["user_explicit_request"] if invocation_kind == "explicit" else []
    if version["status"] in {"exact", "ambiguous"}:
        evidence.append("skill_context_attached")
    if announcements:
        evidence.append("assistant_announcement")
    if exact_read:
        evidence.append("exact_skill_file_read")

    follow_up_messages: list[dict[str, Any]] = []
    for later_turn in window[1:]:
        for text in later_turn.user_texts:
            follow_up_messages.append(
                preview_record(
                    text,
                    omit_previews,
                    turn_id=later_turn.turn_id,
                    timestamp=later_turn.started_at,
                )
            )

    return {
        "episode_id": f"{session.session_id}:{turn.turn_id}",
        "thread_id": session.session_id,
        "invocation_turn_id": turn.turn_id,
        "title": compact_title(title, omit_previews),
        "rollout_path": str(session.path),
        "date": str(turn.started_at or session.meta.get("timestamp") or ""),
        "cwd": session.meta.get("cwd"),
        "source": session.meta.get("source"),
        "thread_source": session.meta.get("thread_source"),
        "skill_exposed_in_context": session.available,
        "invocation": {
            "kind": invocation_kind,
            "turn_user_messages": turn_user_messages,
            "evidence": evidence,
            "confidence": (
                "requires_adjudication"
                if invocation_kind == "inferred_candidate"
                else "supported"
                if len(evidence) > 1
                else "observed"
            ),
            "adjudication_required": invocation_kind == "inferred_candidate",
        },
        "version": version,
        "follow_up": {
            "user_messages": follow_up_messages,
            "assistant_activity": compact_assistant_activity(
                window, omit_previews
            ),
            "tool_activity": compact_tool_activity(window, omit_previews),
            "turn_states": [
                {
                    "turn_id": window_turn.turn_id,
                    "terminal": window_turn.terminal,
                }
                for window_turn in window
            ],
        },
    }


def invocation_candidates(session: Session, skill: str) -> list[tuple[int, str]]:
    candidates: dict[int, str] = {}
    for index, turn in enumerate(session.turns):
        for text in turn.user_texts:
            if text.explicit_request:
                candidates[index] = "explicit"
        if index not in candidates:
            announced = any(message.announcement for message in turn.assistant_messages)
            exact_read = any(call.exact_skill_read for call in turn.tool_calls)
            if announced and (exact_read or bool(unique_contexts(turn))):
                candidates[index] = "inferred_candidate"
    return sorted(candidates.items())


def prefer_session(candidate: Session, existing: Session) -> bool:
    candidate_current = "archived_sessions" not in candidate.path.parts
    existing_current = "archived_sessions" not in existing.path.parts
    if candidate_current != existing_current:
        return candidate_current
    return candidate.path.stat().st_size > existing.path.stat().st_size


def build_version_cohorts(
    explicit_episodes: list[dict[str, Any]],
    inferred_candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    exact: dict[str, dict[str, Any]] = {}
    ambiguous = {"explicit_episode_ids": [], "candidate_episode_ids": []}
    unversioned = {"explicit_episode_ids": [], "candidate_episode_ids": []}
    for episode in explicit_episodes + inferred_candidates:
        candidate = episode["invocation"]["adjudication_required"]
        id_field = (
            "candidate_episode_ids" if candidate else "explicit_episode_ids"
        )
        version = episode["version"]
        if version["status"] == "exact":
            digest = version["content_sha256"]
            cohort = exact.setdefault(
                digest,
                {
                    "paths": [],
                    "explicit_episode_ids": [],
                    "candidate_episode_ids": [],
                },
            )
            cohort[id_field].append(episode["episode_id"])
            cohort["paths"] = sorted(
                set(cohort["paths"])
                | {context["path"] for context in version["contexts"]}
            )
        elif version["status"] == "ambiguous":
            ambiguous[id_field].append(episode["episode_id"])
        else:
            unversioned[id_field].append(episode["episode_id"])
    return {
        "exact": exact,
        "ambiguous": ambiguous,
        "unversioned": unversioned,
    }


def current_version_report(
    path: Path | None,
    cohorts: dict[str, Any],
) -> dict[str, Any]:
    if path is None:
        return {"status": "not_provided"}
    resolved = path.expanduser().resolve()
    try:
        body = resolved.read_text(encoding="utf-8").strip()
    except OSError as error:
        return {
            "status": "unavailable",
            "path": str(resolved),
            "error": error.__class__.__name__,
        }
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    cohort = cohorts["exact"].get(digest)
    if cohort is None:
        return {
            "status": "unobserved",
            "path": str(resolved),
            "content_sha256": digest,
            "bytes": len(body.encode("utf-8")),
            "explicit_episode_ids": [],
            "candidate_episode_ids": [],
        }
    explicit_ids = cohort["explicit_episode_ids"]
    candidate_ids = cohort["candidate_episode_ids"]
    status = "observed_explicit" if explicit_ids else "candidate_only"
    return {
        "status": status,
        "path": str(resolved),
        "content_sha256": digest,
        "bytes": len(body.encode("utf-8")),
        "explicit_episode_ids": explicit_ids,
        "candidate_episode_ids": candidate_ids,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    codex_home = args.codex_home.expanduser().resolve()
    now = datetime.now(timezone.utc)
    since = (
        datetime.strptime(args.since, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        if args.since
        else now - timedelta(days=args.days)
    )

    selected: dict[str, Session] = {}
    files_scanned = 0
    parseable_sessions = 0
    cache_path = cache_path_for(args, codex_home)
    cache_entries: dict[str, Any] = {}
    cache_load_status = "disabled"
    cache_hits = 0
    cache_misses = 0
    next_cache_entries: dict[str, Any] = {}
    if not args.no_cache:
        cache_entries, cache_load_status = load_cache(cache_path, args.skill)
    for path in history_paths(codex_home):
        files_scanned += 1
        try:
            stat = path.stat()
        except OSError:
            continue
        cache_key = str(path.resolve())
        fingerprint = {
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
        }
        cached = cache_entries.get(cache_key) if not args.no_cache else None
        session: Session | None
        if (
            isinstance(cached, dict)
            and cached.get("size") == fingerprint["size"]
            and cached.get("mtime_ns") == fingerprint["mtime_ns"]
        ):
            cached_session = cached.get("session")
            if isinstance(cached_session, dict):
                session = session_from_cache(path, cached_session)
                if session is None:
                    session = read_session(path, args.skill)
                    cache_misses += 1
                else:
                    cache_hits += 1
            elif cached_session is None:
                session = None
                cache_hits += 1
            else:
                session = read_session(path, args.skill)
                cache_misses += 1
        else:
            session = read_session(path, args.skill)
            cache_misses += 1
        if not args.no_cache:
            next_cache_entries[cache_key] = {
                **fingerprint,
                "session": (
                    session_cache_record(
                        session,
                        include_turns=bool(
                            invocation_candidates(session, args.skill)
                        ),
                    )
                    if session
                    else None
                ),
            }
        if session is None:
            continue
        parseable_sessions += 1
        timestamp = parse_timestamp(session.meta.get("timestamp"))
        if timestamp is not None and timestamp < since:
            continue
        if args.cwd_prefix:
            cwd = session.meta.get("cwd")
            if not isinstance(cwd, str) or not cwd.startswith(args.cwd_prefix):
                continue
        if not args.include_subagents and is_subagent(session.meta):
            continue
        existing = selected.get(session.session_id)
        if existing is None or prefer_session(session, existing):
            selected[session.session_id] = session

    cache_status = cache_load_status
    if not args.no_cache:
        cache_changed = (
            cache_misses > 0
            or set(next_cache_entries) != set(cache_entries)
            or cache_load_status != "warm"
        )
        if cache_changed:
            if write_cache(cache_path, args.skill, next_cache_entries):
                cache_status = {
                    "cold": "created",
                    "invalid": "rebuilt",
                    "warm": "updated",
                }.get(cache_load_status, "updated")
            else:
                cache_status = "write_failed"

    titles = load_titles(codex_home)
    episodes: list[dict[str, Any]] = []
    exposure_count = 0
    unsupported_user_records = 0
    for session in selected.values():
        exposure_count += int(session.available)
        unsupported_user_records += session.unsupported_user_records
        candidates = invocation_candidates(session, args.skill)
        for position, (index, kind) in enumerate(candidates):
            next_index = (
                candidates[position + 1][0]
                if position + 1 < len(candidates)
                else None
            )
            episodes.append(
                episode_for(
                    session,
                    index,
                    kind,
                    args.skill,
                    titles.get(session.session_id),
                    args.omit_previews,
                    args.follow_up_turns,
                    next_index,
                )
            )
    episodes.sort(key=lambda item: (item.get("date") or "", item["episode_id"]))
    explicit_episodes = [
        episode
        for episode in episodes
        if not episode["invocation"]["adjudication_required"]
    ]
    inferred_candidates = [
        episode
        for episode in episodes
        if episode["invocation"]["adjudication_required"]
    ]
    cohorts = build_version_cohorts(explicit_episodes, inferred_candidates)
    current_version = current_version_report(args.current_skill_path, cohorts)

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": now.isoformat(),
        "query": {
            "skill": args.skill,
            "since": since.isoformat(),
            "cwd_prefix": args.cwd_prefix,
            "include_subagents": args.include_subagents,
            "follow_up_turns": args.follow_up_turns,
            "current_skill_path": (
                str(args.current_skill_path) if args.current_skill_path else None
            ),
        },
        "coverage": {
            "codex_home": str(codex_home),
            "files_scanned": files_scanned,
            "parseable_sessions": parseable_sessions,
            "qualifying_sessions": len(selected),
            "sessions_with_skill_exposed_in_context": exposure_count,
            "unsupported_user_records": unsupported_user_records,
            "cache": {
                "enabled": not args.no_cache,
                "status": cache_status,
                "path": str(cache_path) if not args.no_cache else None,
                "hits": cache_hits,
                "misses": cache_misses,
            },
        },
        "summary": {
            "explicit_invocations": len(explicit_episodes),
            "inferred_candidates": len(inferred_candidates),
            "exact_version_explicit_episodes": sum(
                episode["version"]["status"] == "exact"
                for episode in explicit_episodes
            ),
            "exact_version_candidate_episodes": sum(
                episode["version"]["status"] == "exact"
                for episode in inferred_candidates
            ),
            "ambiguous_version_explicit_episodes": len(
                cohorts["ambiguous"]["explicit_episode_ids"]
            ),
            "ambiguous_version_candidate_episodes": len(
                cohorts["ambiguous"]["candidate_episode_ids"]
            ),
            "unversioned_explicit_episodes": len(
                cohorts["unversioned"]["explicit_episode_ids"]
            ),
            "unversioned_candidate_episodes": len(
                cohorts["unversioned"]["candidate_episode_ids"]
            ),
            "distinct_exact_versions": len(cohorts["exact"]),
        },
        "current_version": current_version,
        "version_cohorts": cohorts,
        "episodes": explicit_episodes,
        "inferred_candidates": inferred_candidates,
        "limitations": [
            "Injected skill catalogues establish availability only.",
            "Explicit-request matching is intentionally high precision and may miss paraphrases.",
            "Inferred candidates require manual adjudication and are never counted as observed invocations.",
            "Follow-up evidence is neutral and requires review against a stated audit rubric.",
            "Follow-up review is bounded to the configured number of later turns.",
            "turn_completed means a final response was returned, not objective success.",
            "Goal lifecycle records are requested tool actions, not proof that the action succeeded.",
            "Only an exact attached skill-body hash establishes a version cohort.",
        ],
    }


def print_summary(report: dict[str, Any]) -> None:
    query = report["query"]
    coverage = report["coverage"]
    summary = report["summary"]
    print(f"skill={query['skill']} since={query['since']}")
    print(
        "coverage "
        f"files={coverage['files_scanned']} "
        f"sessions={coverage['qualifying_sessions']} "
        f"exposures={coverage['sessions_with_skill_exposed_in_context']}"
    )
    cache = coverage["cache"]
    print(
        "cache "
        f"status={cache['status']} "
        f"hits={cache['hits']} "
        f"misses={cache['misses']}"
    )
    print(
        "observed "
        f"explicit={summary['explicit_invocations']} "
        f"inferred_candidates={summary['inferred_candidates']} "
        f"exact_explicit={summary['exact_version_explicit_episodes']} "
        f"unversioned_explicit={summary['unversioned_explicit_episodes']} "
        f"versions={summary['distinct_exact_versions']}"
    )
    current = report["current_version"]
    print(
        "current_version "
        f"status={current['status']} "
        f"hash={current.get('content_sha256') or '-'}"
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", required=True, help="skill name without the leading $")
    parser.add_argument(
        "--codex-home",
        type=Path,
        default=Path.home() / ".codex",
        help="Codex data directory (default: ~/.codex)",
    )
    window = parser.add_mutually_exclusive_group()
    window.add_argument("--days", type=int, default=90)
    window.add_argument("--since", help="inclusive UTC date in YYYY-MM-DD form")
    parser.add_argument("--cwd-prefix")
    parser.add_argument(
        "--current-skill-path",
        type=Path,
        help="current target SKILL.md used to identify its historical cohort",
    )
    parser.add_argument("--include-subagents", action="store_true")
    parser.add_argument(
        "--cache-path",
        type=Path,
        help=(
            "persistent evidence-cache file "
            "(default: <codex-home>/cache/skill-usage-auditor/<skill>.json.gz)"
        ),
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="disable persistent evidence caching for this run",
    )
    parser.add_argument(
        "--follow-up-turns",
        type=int,
        default=3,
        help="later turns to include after each invocation (default: 3)",
    )
    parser.add_argument("--omit-previews", action="store_true")
    parser.add_argument("--format", choices=("json", "summary"), default="summary")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", args.skill):
        parser.error("--skill must use lowercase hyphen-case")
    if args.days is not None and args.days <= 0:
        parser.error("--days must be positive")
    if args.follow_up_turns < 0:
        parser.error("--follow-up-turns must be non-negative")
    if args.no_cache and args.cache_path is not None:
        parser.error("--cache-path cannot be combined with --no-cache")
    if args.since:
        try:
            datetime.strptime(args.since, "%Y-%m-%d")
        except ValueError:
            parser.error("--since must use YYYY-MM-DD")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_report(args)
    if args.format == "json":
        json.dump(report, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print_summary(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
