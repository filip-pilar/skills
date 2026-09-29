#!/usr/bin/env python3
"""Fetch sanitized, inventory-aware Codex skill and plugin usage analytics."""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import os
import re
import sys
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any


BASE_URL = "https://chatgpt.com/backend-api"
PROFILE_PATH = "/wham/profiles/me"
SKILL_PATH = "/wham/analytics/daily-skill-usage-metrics"
PLUGIN_PATH = "/wham/analytics/daily-plugin-usage-metrics"
ALLOWED_PATHS = frozenset((PROFILE_PATH, SKILL_PATH, PLUGIN_PATH))
MAX_WINDOW_DAYS = 365
ITEM_LIMIT = 1000
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
SCHEMA_VERSION = 6
VIEWS = (
    "current",
    "user",
    "all",
    "daily",
    "weekly",
    "monthly",
    "recent",
    "unobserved",
    "historical",
    "duplicates",
)
SORTS = (
    "most-used",
    "least-used",
    "most-recent",
    "least-recent",
    "first-observed",
    "name",
)


class UsageAnalyticsError(RuntimeError):
    """A safe, user-facing collector failure."""


class RefuseRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Prevent authenticated requests from leaving the fixed API origin."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        raise UsageAnalyticsError("private Codex analytics refused an HTTP redirect")


@dataclasses.dataclass(frozen=True)
class Auth:
    access_token: str
    account_id: str


def parse_date(value: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"invalid date {value!r}; expected YYYY-MM-DD"
        ) from exc


def date_windows(start: dt.date, end: dt.date) -> list[tuple[dt.date, dt.date]]:
    if start > end:
        raise UsageAnalyticsError("start date must not be after end date")
    windows: list[tuple[dt.date, dt.date]] = []
    cursor = start
    while cursor <= end:
        window_end = min(end, cursor + dt.timedelta(days=MAX_WINDOW_DAYS - 1))
        windows.append((cursor, window_end))
        cursor = window_end + dt.timedelta(days=1)
    return windows


def default_codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".codex"


def default_auth_path() -> Path:
    return default_codex_home() / "auth.json"


def load_auth(path: Path) -> Auth:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise UsageAnalyticsError(
            f"Codex authentication file not found at {path}; sign in through Codex"
        ) from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise UsageAnalyticsError(
            f"could not read valid Codex authentication metadata from {path}"
        ) from exc

    tokens = payload.get("tokens")
    if not isinstance(tokens, dict):
        raise UsageAnalyticsError(
            f"Codex authentication metadata at {path} has no token set"
        )
    access_token = tokens.get("access_token")
    account_id = tokens.get("account_id")
    if not isinstance(access_token, str) or not access_token:
        raise UsageAnalyticsError(
            f"Codex authentication metadata at {path} has no access token"
        )
    if not isinstance(account_id, str) or not account_id:
        raise UsageAnalyticsError(
            f"Codex authentication metadata at {path} has no account identifier"
        )
    return Auth(access_token=access_token, account_id=account_id)


class ApiClient:
    def __init__(
        self,
        auth: Auth,
        *,
        timeout: float = 30.0,
        opener: Callable[..., Any] | None = None,
    ) -> None:
        self._auth = auth
        self._timeout = timeout
        self._opener = opener or urllib.request.build_opener(
            RefuseRedirectHandler()
        ).open

    def get(self, path: str, params: dict[str, str | int | bool] | None = None) -> Any:
        if path not in ALLOWED_PATHS:
            raise UsageAnalyticsError("refusing to call an unapproved endpoint")
        query = urllib.parse.urlencode(params or {})
        url = f"{BASE_URL}{path}" + (f"?{query}" if query else "")
        request = urllib.request.Request(
            url,
            method="GET",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self._auth.access_token}",
                "ChatGPT-Account-Id": self._auth.account_id,
                "User-Agent": "codex-skill-analytics/2",
            },
        )
        try:
            response = self._opener(request, timeout=self._timeout)
            with response:
                content_type = response.headers.get_content_type()
                body = response.read(MAX_RESPONSE_BYTES + 1)
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                raise UsageAnalyticsError(
                    f"ChatGPT authentication was rejected with HTTP {exc.code}; "
                    "sign in through Codex and retry"
                ) from exc
            raise UsageAnalyticsError(
                f"private Codex analytics request failed with HTTP {exc.code}"
            ) from exc
        except urllib.error.URLError as exc:
            raise UsageAnalyticsError(
                "private Codex analytics request could not reach ChatGPT"
            ) from exc

        if len(body) > MAX_RESPONSE_BYTES:
            raise UsageAnalyticsError("private Codex analytics response was too large")
        if content_type != "application/json":
            raise UsageAnalyticsError(
                f"private Codex analytics returned unexpected content type {content_type!r}"
            )
        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            raise UsageAnalyticsError(
                "private Codex analytics returned invalid JSON"
            ) from exc


def require_dict(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise UsageAnalyticsError(f"unexpected private API schema at {context}")
    return value


def require_list(value: Any, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise UsageAnalyticsError(f"unexpected private API schema at {context}")
    return value


def project_profile(payload: Any) -> dict[str, Any]:
    root = require_dict(payload, "Profile response")
    stats = require_dict(root.get("stats"), "Profile stats")
    top = require_list(stats.get("top_invocations", []), "Profile top invocations")
    projected_top: list[dict[str, Any]] = []
    for raw in top:
        item = require_dict(raw, "Profile top invocation")
        kind = item.get("type")
        name = item.get("skill_name") if kind == "skill" else item.get("plugin_name")
        count = item.get("usage_count")
        if isinstance(kind, str) and isinstance(name, str) and isinstance(count, int):
            projected_top.append({"type": kind, "name": name, "count": count})

    activity_dates: list[str] = []
    for bucket_name in (
        "cumulative_daily_usage_buckets",
        "daily_usage_buckets",
        "weekly_usage_buckets",
    ):
        buckets = stats.get(bucket_name, [])
        if not isinstance(buckets, list):
            continue
        for raw in buckets:
            if isinstance(raw, dict) and isinstance(raw.get("start_date"), str):
                activity_dates.append(raw["start_date"])

    return {
        "activity_start": min(activity_dates) if activity_dates else None,
        "activity_end": max(activity_dates) if activity_dates else None,
        "unique_skills_used": stats.get("unique_skills_used"),
        "total_skills_used": stats.get("total_skills_used"),
        "top_invocations": projected_top,
    }


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UsageAnalyticsError(f"could not read inventory metadata from {path}") from exc
    return require_dict(payload, f"inventory metadata {path}")


def _read_config(path: Path, warnings: list[str]) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        warnings.append(
            f"Could not parse Codex configuration at {path}; inventory may include disabled skills."
        )
        return {}


def _frontmatter_name(path: Path) -> str | None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = re.match(r"^name:\s*(.+?)\s*$", line)
        if match:
            value = match.group(1).strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            return value or None
    return None


def _invocation_mode(path: Path) -> str:
    metadata_path = path.parent / "agents" / "openai.yaml"
    try:
        metadata = metadata_path.read_text(encoding="utf-8")
    except OSError:
        return "automatic_or_manual"
    match = re.search(
        r"(?m)^\s*allow_implicit_invocation:\s*(true|false)\s*(?:#.*)?$",
        metadata,
        re.IGNORECASE,
    )
    if match and match.group(1).casefold() == "false":
        return "manual_only"
    return "automatic_or_manual"


def _distribution(source: str, marketplace: str | None) -> str:
    if source == "system":
        return "system"
    if source == "user":
        return "standalone_user"
    if marketplace == "openai-bundled":
        return "bundled_plugin"
    if marketplace == "openai-primary-runtime":
        return "runtime_plugin"
    if marketplace == "openai-curated-remote":
        return "remote_plugin"
    return "configured_plugin"


def _skill_config_entries(config: dict[str, Any]) -> list[dict[str, Any]]:
    skills = config.get("skills", {})
    if not isinstance(skills, dict):
        return []
    entries = skills.get("config", [])
    if not isinstance(entries, list):
        return []
    return [entry for entry in entries if isinstance(entry, dict)]


def _skill_enabled(
    canonical_name: str,
    path: Path,
    entries: list[dict[str, Any]],
) -> bool:
    enabled = True
    resolved = path.expanduser().resolve()
    for entry in entries:
        matches_name = entry.get("name") == canonical_name
        configured_path = entry.get("path")
        matches_path = False
        if isinstance(configured_path, str):
            try:
                matches_path = Path(configured_path).expanduser().resolve() == resolved
            except OSError:
                matches_path = False
        if (matches_name or matches_path) and isinstance(entry.get("enabled"), bool):
            enabled = entry["enabled"]
    return enabled


def _version_key(value: str) -> tuple[tuple[int, str], ...]:
    parts = re.split(r"([0-9]+)", value.casefold())
    return tuple(
        (1, f"{int(part):020d}") if part.isdigit() else (0, part)
        for part in parts
    )


def _select_plugin_manifest(root: Path) -> Path | None:
    candidates = list(root.glob("*/.codex-plugin/plugin.json"))
    direct = root / ".codex-plugin" / "plugin.json"
    if direct.is_file():
        candidates.append(direct)
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda path: (_version_key(path.parent.parent.name), str(path)),
    )


def _plugin_roots(
    codex_home: Path,
    config: dict[str, Any],
) -> list[tuple[Path, str, str | None]]:
    cache = codex_home / "plugins" / "cache"
    configured: dict[str, bool] = {}
    plugins = config.get("plugins", {})
    if isinstance(plugins, dict):
        for key, value in plugins.items():
            if isinstance(value, dict) and isinstance(value.get("enabled"), bool):
                configured[key] = value["enabled"]

    roots: dict[Path, tuple[str, str | None]] = {}
    for key, enabled in configured.items():
        if not enabled or "@" not in key:
            continue
        plugin_name, marketplace = key.rsplit("@", 1)
        root = cache / marketplace / plugin_name
        roots[root] = (marketplace, key)

    if cache.is_dir():
        for marker in cache.glob("*/*/.codex-remote-plugin-install.json"):
            root = marker.parent
            marketplace = root.parent.name
            plugin_name = root.name
            key = f"{plugin_name}@{marketplace}"
            if configured.get(key) is False:
                continue
            remote_id = None
            try:
                marker_payload = _read_json(marker)
                value = marker_payload.get("remote_plugin_id")
                if isinstance(value, str):
                    remote_id = value
            except UsageAnalyticsError:
                pass
            roots.setdefault(root, (marketplace, remote_id or key))

    return [
        (root, metadata[0], metadata[1])
        for root, metadata in sorted(roots.items(), key=lambda item: str(item[0]))
    ]


def _installation(
    *,
    name: str,
    base_name: str,
    namespace: str | None,
    source: str,
    path: Path,
    marketplace: str | None = None,
    plugin_identifier: str | None = None,
    plugin_display_name: str | None = None,
    plugin_author: str | None = None,
    plugin_repository: str | None = None,
    plugin_website: str | None = None,
    version: str | None = None,
) -> dict[str, Any]:
    invocation_mode = _invocation_mode(path)
    return {
        "name": name,
        "base_name": base_name,
        "namespace": namespace,
        "source": source,
        "path": str(path),
        "marketplace": marketplace,
        "plugin_identifier": plugin_identifier,
        "plugin_display_name": plugin_display_name,
        "plugin_author": plugin_author,
        "plugin_repository": plugin_repository,
        "plugin_website": plugin_website,
        "version": version,
        "distribution": _distribution(source, marketplace),
        "invocation_mode": invocation_mode,
        "implicit_invocation": invocation_mode != "manual_only",
    }


def discover_inventory(
    *,
    codex_home: Path | None = None,
    agents_skills_dir: Path | None = None,
    config_path: Path | None = None,
) -> dict[str, Any]:
    """Discover current skills without treating arbitrary cache entries as active."""

    resolved_home = (codex_home or default_codex_home()).expanduser()
    resolved_agents = (
        agents_skills_dir.expanduser()
        if agents_skills_dir is not None
        else Path.home() / ".agents" / "skills"
    )
    resolved_config = (
        config_path.expanduser()
        if config_path is not None
        else resolved_home / "config.toml"
    )
    warnings: list[str] = []
    config = _read_config(resolved_config, warnings)
    skill_entries = _skill_config_entries(config)
    installations: list[dict[str, Any]] = []

    roots = ((resolved_agents, "user"), (resolved_home / "skills", "user"))
    seen_paths: set[Path] = set()
    for root, default_source in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("SKILL.md")):
            try:
                resolved_path = path.resolve()
            except OSError:
                resolved_path = path
            if resolved_path in seen_paths:
                continue
            seen_paths.add(resolved_path)
            base_name = _frontmatter_name(path)
            if not base_name or not _skill_enabled(base_name, path, skill_entries):
                continue
            source = "system" if ".system" in path.parts else default_source
            installations.append(
                _installation(
                    name=base_name,
                    base_name=base_name,
                    namespace=None,
                    source=source,
                    path=path,
                )
            )

    for root, marketplace, plugin_identifier in _plugin_roots(resolved_home, config):
        manifest_path = _select_plugin_manifest(root)
        if manifest_path is None:
            warnings.append(
                f"Enabled or installed plugin at {root} has no readable package manifest."
            )
            continue
        try:
            manifest = _read_json(manifest_path)
        except UsageAnalyticsError as exc:
            warnings.append(str(exc))
            continue
        plugin_name = manifest.get("name")
        if not isinstance(plugin_name, str) or not plugin_name:
            warnings.append(f"Plugin manifest at {manifest_path} has no name.")
            continue
        version = (
            manifest.get("version")
            if isinstance(manifest.get("version"), str)
            else None
        )
        interface = (
            manifest.get("interface")
            if isinstance(manifest.get("interface"), dict)
            else {}
        )
        author = (
            manifest.get("author")
            if isinstance(manifest.get("author"), dict)
            else {}
        )
        plugin_display_name = (
            interface.get("displayName")
            if isinstance(interface.get("displayName"), str)
            else None
        )
        plugin_author = (
            author.get("name") if isinstance(author.get("name"), str) else None
        )
        plugin_repository = (
            manifest.get("repository")
            if isinstance(manifest.get("repository"), str)
            else None
        )
        plugin_website = next(
            (
                value
                for value in (manifest.get("homepage"), interface.get("websiteURL"))
                if isinstance(value, str) and value
            ),
            None,
        )
        skills_value = manifest.get("skills")
        skill_roots: list[Path] = []
        if isinstance(skills_value, str):
            skill_roots.append(manifest_path.parent.parent / skills_value)
        elif isinstance(skills_value, list):
            skill_roots.extend(
                manifest_path.parent.parent / value
                for value in skills_value
                if isinstance(value, str)
            )
        for skill_root in skill_roots:
            if not skill_root.is_dir():
                continue
            for path in sorted(skill_root.rglob("SKILL.md")):
                base_name = _frontmatter_name(path)
                if not base_name:
                    continue
                canonical_name = f"{plugin_name}:{base_name}"
                if not _skill_enabled(canonical_name, path, skill_entries):
                    continue
                installations.append(
                    _installation(
                        name=canonical_name,
                        base_name=base_name,
                        namespace=plugin_name,
                        source="plugin",
                        path=path,
                        marketplace=marketplace,
                        plugin_identifier=plugin_identifier,
                        plugin_display_name=plugin_display_name,
                        plugin_author=plugin_author,
                        plugin_repository=plugin_repository,
                        plugin_website=plugin_website,
                        version=version,
                    )
                )

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in installations:
        grouped[item["name"]].append(item)
    current_skills: list[dict[str, Any]] = []
    for name, grouped_installations in grouped.items():
        sources = sorted({item["source"] for item in grouped_installations})
        distributions = sorted(
            {item["distribution"] for item in grouped_installations}
        )
        invocation_modes = sorted(
            {item["invocation_mode"] for item in grouped_installations}
        )
        namespaces = sorted(
            {item["namespace"] for item in grouped_installations if item["namespace"]}
        )
        current_skills.append(
            {
                "name": name,
                "base_name": grouped_installations[0]["base_name"],
                "namespace": namespaces[0] if len(namespaces) == 1 else None,
                "source": sources[0] if len(sources) == 1 else "multiple",
                "sources": sources,
                "distribution": (
                    distributions[0] if len(distributions) == 1 else "multiple"
                ),
                "distributions": distributions,
                "invocation_mode": (
                    invocation_modes[0] if len(invocation_modes) == 1 else "mixed"
                ),
                "source_paths": sorted(
                    {item["path"] for item in grouped_installations}
                ),
                "installation_count": len(grouped_installations),
                "duplicate_installation": len(grouped_installations) > 1,
                "installations": sorted(
                    grouped_installations,
                    key=lambda item: (item["source"], item["path"]),
                ),
            }
        )
    current_skills.sort(key=lambda item: item["name"].casefold())
    duplicates = [item for item in current_skills if item["duplicate_installation"]]
    return {
        "enabled": True,
        "codex_home": str(resolved_home),
        "config_path": str(resolved_config),
        "current_skill_count": len(current_skills),
        "installation_count": len(installations),
        "current_skills": current_skills,
        "duplicate_installations": duplicates,
        "warnings": warnings,
    }


def metric_config(kind: str) -> tuple[str, str, str]:
    if kind == "skills":
        return SKILL_PATH, "top_skill_limit", "skill_usage_overviews"
    if kind == "plugins":
        return PLUGIN_PATH, "top_plugin_limit", "plugin_usage_overviews"
    raise UsageAnalyticsError(f"unsupported metric kind {kind!r}")


def _recent_count(daily: list[dict[str, Any]], end: dt.date, days: int) -> int:
    threshold = end - dt.timedelta(days=days - 1)
    return sum(
        row["count"]
        for row in daily
        if threshold <= dt.date.fromisoformat(row["date"]) <= end
    )


def _finalize_record(record: dict[str, Any], end: dt.date) -> dict[str, Any] | None:
    daily: list[dict[str, Any]] = []
    for date_value, raw in sorted(record["daily"].items()):
        if raw["count"] <= 0:
            continue
        daily.append(
            {
                "date": date_value,
                "count": raw["count"],
                "identifiers": sorted(raw["identifiers"]),
            }
        )
    if not daily:
        return None
    total = sum(row["count"] for row in daily)
    first_observed = daily[0]["date"]
    last_observed = daily[-1]["date"]
    first_date = dt.date.fromisoformat(first_observed)
    last_date = dt.date.fromisoformat(last_observed)
    elapsed_weeks = ((end - first_date).days + 1) / 7
    active_days = len(daily)
    identifiers = sorted(record["identifiers"])
    item = {
        "id": record["id"],
        "name": record["name"],
        "count": total,
        "first_observed": first_observed,
        "last_used": last_observed,
        "identifiers": identifiers,
        "display_names": sorted(record["display_names"]),
        "marketplaces": sorted(record["marketplaces"]),
        "active_days": active_days,
        "days_since_last_use": (end - last_date).days,
        "uses_per_active_day": round(total / active_days, 4),
        "uses_per_week_since_first_observed": round(total / elapsed_weeks, 4),
        "uses_last_7_days": _recent_count(daily, end, 7),
        "uses_last_30_days": _recent_count(daily, end, 30),
        "uses_last_90_days": _recent_count(daily, end, 90),
        "daily": daily,
        "identity_flags": [],
    }
    if len(identifiers) > 1:
        item["identity_flags"].append("multiple_identifiers_for_name")
    return item


def collect_metric(
    client: ApiClient,
    kind: str,
    start: dt.date,
    end: dt.date,
) -> dict[str, Any]:
    path, limit_field, overview_field = metric_config(kind)
    records: dict[tuple[str, str], dict[str, Any]] = {}
    freshness_values: list[str] = []
    active_dates: set[str] = set()
    returned_dates: set[str] = set()

    for window_start, window_end in date_windows(start, end):
        payload = require_dict(
            client.get(
                path,
                {
                    "start_date": window_start.isoformat(),
                    "end_date": window_end.isoformat(),
                    "group_by": "day",
                    limit_field: ITEM_LIMIT,
                    "workspace_user": "true",
                },
            ),
            f"{kind} response",
        )
        data = require_list(payload.get("data"), f"{kind} data")
        freshness = payload.get("data_freshness_ts")
        if isinstance(freshness, str):
            freshness_values.append(freshness)
        for raw_day in data:
            day = require_dict(raw_day, f"{kind} day")
            date_value = day.get("date")
            if not isinstance(date_value, str):
                raise UsageAnalyticsError(f"unexpected private API schema at {kind} date")
            try:
                parsed_date = dt.date.fromisoformat(date_value)
            except ValueError as exc:
                raise UsageAnalyticsError(
                    f"unexpected private API schema at {kind} date"
                ) from exc
            if not start <= parsed_date <= end:
                raise UsageAnalyticsError(
                    f"private API returned {kind} date outside the requested range"
                )
            returned_dates.add(date_value)
            overviews = require_list(day.get(overview_field), f"{kind} overviews")
            for raw_overview in overviews:
                overview = require_dict(raw_overview, f"{kind} overview")
                count = overview.get("invocation_counts")
                if not isinstance(count, int) or count < 0:
                    raise UsageAnalyticsError(
                        f"unexpected private API schema at {kind} invocation count"
                    )
                if kind == "skills":
                    name = overview.get("skill_name")
                    stable_id = name
                    identifiers = overview.get("skill_ids", [])
                    marketplace = None
                else:
                    name = overview.get("display_name")
                    stable_id = (
                        overview.get("plugin_id")
                        or overview.get("plugin_name")
                        or name
                    )
                    identifiers = [overview.get("plugin_id")]
                    marketplace = overview.get("marketplace")
                if not isinstance(name, str) or not name:
                    raise UsageAnalyticsError(
                        f"unexpected private API schema at {kind} name"
                    )
                if not isinstance(stable_id, str) or not stable_id:
                    stable_id = name
                identifier_values = (
                    {
                        value
                        for value in identifiers
                        if isinstance(value, str) and value
                    }
                    if isinstance(identifiers, list)
                    else set()
                )
                key = (stable_id, name)
                record = records.setdefault(
                    key,
                    {
                        "id": stable_id,
                        "name": name,
                        "identifiers": set(),
                        "display_names": set(),
                        "marketplaces": set(),
                        "daily": {},
                    },
                )
                record["identifiers"].update(identifier_values)
                display_name = overview.get("display_name")
                if isinstance(display_name, str) and display_name:
                    record["display_names"].add(display_name)
                if isinstance(marketplace, str) and marketplace:
                    record["marketplaces"].add(marketplace)
                daily = record["daily"].setdefault(
                    date_value, {"count": 0, "identifiers": set()}
                )
                daily["count"] += count
                daily["identifiers"].update(identifier_values)
                if count > 0:
                    active_dates.add(date_value)

    items = [
        finalized
        for record in records.values()
        if (finalized := _finalize_record(record, end)) is not None
    ]
    items.sort(key=lambda item: (-item["count"], item["name"].casefold()))
    other_items = [item for item in items if item["name"].casefold() == "other"]
    other_count = sum(item["count"] for item in other_items)
    named_items = [item for item in items if item["name"].casefold() != "other"]
    observed_dates = [row["date"] for item in items for row in item["daily"]]
    return {
        "total_invocations": sum(item["count"] for item in items),
        "active_days": len(active_dates),
        "distinct_items": len(named_items),
        "first_recorded_date": min(observed_dates) if observed_dates else None,
        "last_recorded_date": max(observed_dates) if observed_dates else None,
        "returned_start_date": min(returned_dates) if returned_dates else None,
        "returned_end_date": max(returned_dates) if returned_dates else None,
        "returned_day_count": len(returned_dates),
        "data_freshness": max(freshness_values) if freshness_values else None,
        "complete_for_returned_days": other_count == 0,
        "other_invocations": other_count,
        "other_daily": [row for item in other_items for row in item["daily"]],
        "items": named_items,
    }


def merge_skill_inventory(
    metric: dict[str, Any],
    inventory: dict[str, Any],
) -> None:
    current_items = inventory["current_skills"]
    current_by_name = {item["name"]: item for item in current_items}
    observed_by_name = {item["name"]: item for item in metric["items"]}

    for item in metric["items"]:
        if item["name"] in current_by_name:
            continue
        is_plugin = ":" in item["name"]
        item.update({
            "current_available": False,
            "inventory_status": "historical",
            "observation_status": "historical_skill_not_currently_available",
            "source": "plugin" if is_plugin else "unknown",
            "sources": ["plugin"] if is_plugin else ["unknown"],
            "distribution": "historical",
            "distributions": [],
            "invocation_mode": None,
            "source_paths": [],
            "namespace": item["name"].split(":", 1)[0] if is_plugin else None,
            "base_name": item["name"].rsplit(":", 1)[-1],
            "installation_count": 0,
            "duplicate_installation": False,
            "installations": [],
        })

    for inventory_item in current_items:
        item = observed_by_name.get(inventory_item["name"])
        observed = item is not None
        if item is None:
            item = {
                "id": inventory_item["name"],
                "count": 0,
                "first_observed": None,
                "last_used": None,
                "identifiers": [],
                "display_names": [],
                "marketplaces": sorted({
                    entry["marketplace"] for entry in inventory_item["installations"]
                    if entry["marketplace"]
                }),
                "active_days": 0,
                "days_since_last_use": None,
                "uses_per_active_day": None,
                "uses_per_week_since_first_observed": None,
                "uses_last_7_days": 0,
                "uses_last_30_days": 0,
                "uses_last_90_days": 0,
                "daily": [],
                "identity_flags": [],
            }
            metric["items"].append(item)
        item.update(inventory_item)
        item.update({
            "current_available": True,
            "inventory_status": "current_observed" if observed else "current_unobserved",
            "observation_status": (
                "observed_during_coverage" if observed
                else "no_invocation_returned_during_coverage"
            ),
        })
        if inventory_item["duplicate_installation"]:
            item["identity_flags"].append("duplicate_current_installation")

    metric["items"].sort(key=lambda item: (-item["count"], item["name"].casefold()))
    metric["inventory_summary"] = {
        "current_skill_count": len(current_items),
        "current_observed_count": sum(
            item["inventory_status"] == "current_observed" for item in metric["items"]
        ),
        "current_unobserved_count": sum(
            item["inventory_status"] == "current_unobserved" for item in metric["items"]
        ),
        "historical_skill_count": sum(
            item["inventory_status"] == "historical" for item in metric["items"]
        ),
        "duplicate_name_count": len(inventory["duplicate_installations"]),
    }


def _inventory_disabled() -> dict[str, Any]:
    return {
        "enabled": False,
        "current_skill_count": 0,
        "installation_count": 0,
        "current_skills": [],
        "duplicate_installations": [],
        "warnings": [],
    }


def build_warnings(
    metrics: dict[str, dict[str, Any]],
    inventory: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []
    for kind, metric in metrics.items():
        returned_start = metric.get("returned_start_date")
        if returned_start is None:
            warnings.append(f"The {kind} endpoint returned no dated rows.")
    if any(not metric["complete_for_returned_days"] for metric in metrics.values()):
        warnings.append(
            "Named-item counts are truncated because at least one response retained an Other bucket."
        )
    warnings.extend(inventory["warnings"])
    return warnings


def build_report(
    client: ApiClient,
    *,
    kind: str,
    start: dt.date | None,
    end: dt.date,
    days: int | None,
    all_available: bool,
    inventory: dict[str, Any] | None = None,
    inventory_enabled: bool = True,
    report_options: dict[str, Any] | None = None,
    include_profile: bool = False,
) -> dict[str, Any]:
    profile = (
        project_profile(client.get(PROFILE_PATH))
        if all_available or include_profile else None
    )
    if all_available:
        activity_start = profile["activity_start"]
        if not isinstance(activity_start, str):
            raise UsageAnalyticsError(
                "Profile did not expose an earliest activity date; provide --start"
            )
        try:
            resolved_start = dt.date.fromisoformat(activity_start)
        except ValueError as exc:
            raise UsageAnalyticsError(
                "Profile exposed an invalid earliest activity date"
            ) from exc
    elif start is not None:
        resolved_start = start
    else:
        requested_days = days if days is not None else MAX_WINDOW_DAYS
        if requested_days < 1:
            raise UsageAnalyticsError("--days must be at least 1")
        resolved_start = end - dt.timedelta(days=requested_days - 1)
    if resolved_start > end:
        raise UsageAnalyticsError("start date must not be after end date")

    resolved_inventory = inventory
    if resolved_inventory is None:
        resolved_inventory = (
            discover_inventory() if inventory_enabled and kind != "plugins"
            else _inventory_disabled()
        )
    kinds: Iterable[str] = ("skills", "plugins") if kind == "both" else (kind,)
    metrics = {
        metric_kind: collect_metric(client, metric_kind, resolved_start, end)
        for metric_kind in kinds
    }
    if "skills" in metrics and resolved_inventory.get("enabled"):
        merge_skill_inventory(metrics["skills"], resolved_inventory)
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": {
            "origin": "https://chatgpt.com",
            "classification": "private_undocumented",
            "read_only": True,
        },
        "requested_range": {
            "start": resolved_start.isoformat(),
            "end": end.isoformat(),
            "windows": len(date_windows(resolved_start, end)),
        },
        "report_options": report_options
        or {"view": "current", "sort": "most-used", "recent_days": 30},
        "inventory": resolved_inventory,
        "metrics": metrics,
        "warnings": build_warnings(metrics, resolved_inventory),
    }
    if profile is not None:
        report["profile_cross_check"] = profile
    return report


def _sort_items(items: list[dict[str, Any]], sort: str) -> list[dict[str, Any]]:
    if sort == "name":
        key = lambda item: (item["name"].casefold(),)
    elif sort == "least-used":
        key = lambda item: (item["count"], item["name"].casefold())
    elif sort == "most-recent":
        key = lambda item: (
            item["last_used"] is None,
            -dt.date.fromisoformat(item["last_used"]).toordinal()
            if item["last_used"]
            else 0,
            item["name"].casefold(),
        )
    elif sort == "least-recent":
        key = lambda item: (
            item["last_used"] is not None,
            item["last_used"] or "",
            item["name"].casefold(),
        )
    elif sort == "first-observed":
        key = lambda item: (
            item["first_observed"] is None,
            item["first_observed"] or "",
            item["name"].casefold(),
        )
    else:
        key = lambda item: (-item["count"], item["name"].casefold())
    return sorted(items, key=key)


def _view_items(
    items: list[dict[str, Any]],
    view: str,
    recent_days: int,
    end: dt.date,
) -> list[dict[str, Any]]:
    if view == "current":
        if any("current_available" in item for item in items):
            return [item for item in items if item.get("current_available")]
        return items
    if view == "user":
        return [
            item
            for item in items
            if item.get("current_available") and item.get("source") == "user"
        ]
    if view == "unobserved":
        return [
            item for item in items if item.get("current_available") and item["count"] == 0
        ]
    if view == "historical":
        return [item for item in items if item.get("inventory_status") == "historical"]
    if view == "duplicates":
        return [item for item in items if item.get("duplicate_installation")]
    if view == "recent":
        return [
            item for item in items if _recent_count(item["daily"], end, recent_days) > 0
        ]
    return items


def _period_label(date_value: str, view: str) -> str:
    parsed = dt.date.fromisoformat(date_value)
    if view == "monthly":
        return parsed.strftime("%Y-%m")
    if view == "weekly":
        iso = parsed.isocalendar()
        return f"{iso.year}-W{iso.week:02d}"
    return date_value


def _timeline_rows(
    items: list[dict[str, Any]], view: str
) -> list[dict[str, Any]]:
    totals: dict[tuple[str, str, str], int] = defaultdict(int)
    for item in items:
        for row in item["daily"]:
            totals[(_period_label(row["date"], view), item["id"], item["name"])] += row["count"]
    return [
        {"period": period, "id": identifier, "name": name, "count": count}
        for (period, identifier, name), count in sorted(
            totals.items(), key=lambda entry: (entry[0][0], entry[0][1].casefold())
        )
    ]


def render_report(report: dict[str, Any], *, details: bool = False) -> dict[str, Any]:
    """Select and sort once for either compact output or a full diagnostic report."""
    options = report["report_options"]
    view = options["view"]
    end = dt.date.fromisoformat(report["requested_range"]["end"])
    if details:
        result = {**report, "selected_view": {**options, "metrics": {}}}
    else:
        result = {
            key: report[key]
            for key in (
                "schema_version", "generated_at", "source", "requested_range",
                "report_options", "warnings",
            )
        }
        result.update({
            "detail": "compact",
            "inventory_enabled": report["inventory"]["enabled"],
            "metrics": {},
        })

    for kind, metric in report["metrics"].items():
        items = _sort_items(
            _view_items(metric["items"], view, options["recent_days"], end),
            options["sort"],
        )
        timeline = view in ("daily", "weekly", "monthly")
        rows = _timeline_rows(items, view) if timeline else []
        if details:
            result["selected_view"]["metrics"][kind] = (
                {"row_count": len(rows), "rows": rows} if timeline else
                {"item_count": len(items), "items": [{"id": item["id"], "name": item["name"]} for item in items]}
            )
            continue
        selected = {
            "coverage": {
                key: metric[key]
                for key in (
                    "returned_start_date", "returned_end_date", "returned_day_count",
                    "data_freshness", "complete_for_returned_days", "other_invocations",
                )
            },
            "item_count": len(items),
            "observed_items": sum(item["count"] > 0 for item in items),
            "total_invocations": sum(item["count"] for item in items),
        }
        if timeline:
            selected["rows"] = rows
        else:
            selected["items"] = [compact_item(item) for item in items]
        result["metrics"][kind] = selected
    return result


def compact_item(item: dict[str, Any]) -> dict[str, Any]:
    result = {
        key: item[key]
        for key in (
            "id", "name", "count", "active_days", "first_observed", "last_used",
            "uses_last_30_days", "current_available", "observation_status",
            "distribution", "invocation_mode",
        )
        if key in item
    }
    for key in ("identifiers", "identity_flags", "marketplaces"):
        if item.get(key):
            result[key] = item[key]
    if item.get("duplicate_installation"):
        result["installation_count"] = item["installation_count"]
    installations = item.get("installations", [])
    if item.get("duplicate_installation") or any(
        entry.get("plugin_identifier") for entry in installations
    ):
        result["installations"] = [
            {
                key: entry[key]
                for key in (
                    "distribution", "marketplace", "plugin_identifier",
                    "plugin_display_name", "plugin_author", "plugin_repository",
                    "plugin_website", "invocation_mode",
                )
                if entry.get(key) is not None
            }
            for entry in installations
        ]
    return result


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch sanitized, inventory-aware skill and plugin usage from "
            "Codex's private ChatGPT analytics endpoints."
        )
    )
    range_group = parser.add_mutually_exclusive_group()
    range_group.add_argument("--start", type=parse_date)
    range_group.add_argument("--days", type=int)
    range_group.add_argument("--all-available", action="store_true")
    parser.add_argument(
        "--end",
        type=parse_date,
        default=dt.datetime.now(dt.timezone.utc).date(),
    )
    parser.add_argument(
        "--kind", choices=("skills", "plugins", "both"), default="skills"
    )
    parser.add_argument(
        "--details", action="store_true",
        help="include full inventory, daily histories, and diagnostic metadata",
    )
    parser.add_argument("--view", choices=VIEWS, default="current")
    parser.add_argument("--sort", choices=SORTS, default="most-used")
    parser.add_argument("--recent-days", type=int, default=30)
    parser.add_argument("--no-inventory", action="store_true")
    parser.add_argument("--auth-file", type=Path, default=default_auth_path())
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args(argv)
    if args.view in {"user", "unobserved", "historical", "duplicates"} and (
        args.kind != "skills" or args.no_inventory
    ):
        parser.error(f"--view {args.view} requires --kind skills with inventory enabled")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    if args.recent_days < 1:
        print("ERROR: --recent-days must be at least 1", file=sys.stderr)
        return 1
    options = {
        "view": args.view,
        "sort": args.sort,
        "recent_days": args.recent_days,
    }
    try:
        auth = load_auth(args.auth_file.expanduser())
        client = ApiClient(auth, timeout=args.timeout)
        report = build_report(
            client,
            kind=args.kind,
            start=args.start,
            end=args.end,
            days=args.days,
            all_available=args.all_available,
            inventory_enabled=not args.no_inventory,
            report_options=options,
            include_profile=args.details,
        )
    except UsageAnalyticsError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    output = render_report(report, details=args.details)
    json.dump(output, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
