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
SCHEMA_VERSION = 3
KNOWN_SKILL_RENAMES = {
    "codex-skill-usage-analytics": ("codex-usage-analytics",),
}
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
    "possible-renames",
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
                "User-Agent": "codex-skill-usage-analytics/2",
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
        "source_path": str(path),
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
                    {item["source_path"] for item in grouped_installations}
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


def _round_rate(value: float) -> float:
    return round(value, 4)


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
        "name": record["name"],
        "count": total,
        "first_observed": first_observed,
        "last_observed": last_observed,
        "last_used": last_observed,
        "identifiers": identifiers,
        "display_names": sorted(record["display_names"]),
        "marketplaces": sorted(record["marketplaces"]),
        "active_days": active_days,
        "days_since_last_use": (end - last_date).days,
        "uses_per_active_day": _round_rate(total / active_days),
        "uses_per_week_since_first_observed": _round_rate(total / elapsed_weeks),
        "uses_last_7_days": _recent_count(daily, end, 7),
        "uses_last_30_days": _recent_count(daily, end, 30),
        "uses_last_90_days": _recent_count(daily, end, 90),
        "daily": daily,
        "identity_flags": [],
        "possible_renames": [],
    }
    if len(identifiers) > 1:
        item["identity_flags"].append("multiple_identifiers_for_name")
    return item


def _analyze_identifier_names(items: list[dict[str, Any]]) -> None:
    names_by_identifier: dict[str, set[str]] = defaultdict(set)
    for item in items:
        for identifier in item.get("identifiers", []):
            names_by_identifier[identifier].add(item["name"])
    for identifier, names in names_by_identifier.items():
        if len(names) < 2:
            continue
        for item in items:
            if identifier not in item.get("identifiers", []):
                continue
            if "identifier_observed_with_multiple_names" not in item["identity_flags"]:
                item["identity_flags"].append(
                    "identifier_observed_with_multiple_names"
                )
            for other_name in sorted(names - {item["name"]}):
                candidate = {
                    "name": other_name,
                    "evidence": "shared_telemetry_identifier",
                    "identifier": identifier,
                }
                if candidate not in item["possible_renames"]:
                    item["possible_renames"].append(candidate)


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
    _analyze_identifier_names(items)
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


def _normalized_base_name(name: str) -> str:
    base = name.rsplit(":", 1)[-1]
    return re.sub(r"[^a-z0-9]+", "", base.casefold())


def _empty_inventory_item(
    inventory_item: dict[str, Any],
    possible_predecessors: list[dict[str, Any]],
) -> dict[str, Any]:
    status = (
        "not_observed_under_current_name"
        if possible_predecessors
        else "no_invocation_returned_during_coverage"
    )
    flags = ["possible_renamed_predecessor"] if possible_predecessors else []
    if inventory_item["duplicate_installation"]:
        flags.append("duplicate_current_installation")
    marketplaces = sorted(
        {
            installation["marketplace"]
            for installation in inventory_item["installations"]
            if installation.get("marketplace")
        }
    )
    return {
        "name": inventory_item["name"],
        "count": 0,
        "first_observed": None,
        "last_observed": None,
        "last_used": None,
        "identifiers": [],
        "display_names": [],
        "marketplaces": marketplaces,
        "active_days": 0,
        "days_since_last_use": None,
        "uses_per_active_day": None,
        "uses_per_week_since_first_observed": None,
        "uses_last_7_days": 0,
        "uses_last_30_days": 0,
        "uses_last_90_days": 0,
        "daily": [],
        "identity_flags": flags,
        "possible_renames": possible_predecessors,
        "current_available": True,
        "inventory_status": "current_unobserved",
        "observation_status": status,
        "source": inventory_item["source"],
        "sources": inventory_item["sources"],
        "distribution": inventory_item.get("distribution", "standalone_user"),
        "distributions": inventory_item.get(
            "distributions", [inventory_item.get("distribution", "standalone_user")]
        ),
        "invocation_mode": inventory_item.get(
            "invocation_mode", "automatic_or_manual"
        ),
        "source_paths": inventory_item.get(
            "source_paths",
            [item["path"] for item in inventory_item["installations"]],
        ),
        "namespace": inventory_item["namespace"],
        "base_name": inventory_item["base_name"],
        "installation_count": inventory_item["installation_count"],
        "duplicate_installation": inventory_item["duplicate_installation"],
        "installations": inventory_item["installations"],
    }


def merge_skill_inventory(
    metric: dict[str, Any],
    inventory: dict[str, Any],
) -> None:
    current_items = inventory.get("current_skills", []) if inventory.get("enabled") else []
    current_by_name = {item["name"]: item for item in current_items}
    observed_by_name = {item["name"]: item for item in metric["items"]}
    historical_by_normalized: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in metric["items"]:
        if item["name"] not in current_by_name:
            historical_by_normalized[_normalized_base_name(item["name"])].append(item)

    for item in metric["items"]:
        inventory_item = current_by_name.get(item["name"])
        if inventory_item is None:
            is_plugin = ":" in item["name"]
            item.update(
                {
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
                }
            )
            continue
        item.update(
            {
                "current_available": True,
                "inventory_status": "current_observed",
                "observation_status": "observed_during_coverage",
                "source": inventory_item["source"],
                "sources": inventory_item["sources"],
                "distribution": inventory_item.get(
                    "distribution", "standalone_user"
                ),
                "distributions": inventory_item.get(
                    "distributions",
                    [inventory_item.get("distribution", "standalone_user")],
                ),
                "invocation_mode": inventory_item.get(
                    "invocation_mode", "automatic_or_manual"
                ),
                "source_paths": inventory_item.get(
                    "source_paths",
                    [entry["path"] for entry in inventory_item["installations"]],
                ),
                "namespace": inventory_item["namespace"],
                "base_name": inventory_item["base_name"],
                "installation_count": inventory_item["installation_count"],
                "duplicate_installation": inventory_item["duplicate_installation"],
                "installations": inventory_item["installations"],
            }
        )
        if inventory_item["duplicate_installation"]:
            item["identity_flags"].append("duplicate_current_installation")

    for inventory_item in current_items:
        if inventory_item["name"] in observed_by_name:
            continue
        candidates_by_name = {
            historical["name"]: {
                "name": historical["name"],
                "evidence": "same_normalized_base_name",
            }
            for historical in historical_by_normalized.get(
                _normalized_base_name(inventory_item["base_name"]), []
            )
        }
        for old_name in KNOWN_SKILL_RENAMES.get(inventory_item["name"], ()):
            historical = observed_by_name.get(old_name)
            if historical is None or old_name in current_by_name:
                continue
            candidates_by_name[old_name] = {
                "name": old_name,
                "evidence": "declared_package_rename",
            }
            successor = {
                "name": inventory_item["name"],
                "evidence": "declared_package_rename",
            }
            if successor not in historical["possible_renames"]:
                historical["possible_renames"].append(successor)
            if "declared_renamed_successor" not in historical["identity_flags"]:
                historical["identity_flags"].append("declared_renamed_successor")
        candidates = sorted(candidates_by_name.values(), key=lambda item: item["name"])
        metric["items"].append(_empty_inventory_item(inventory_item, candidates))

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
        "duplicate_name_count": len(inventory.get("duplicate_installations", [])),
        "possible_rename_count": sum(
            bool(item.get("possible_renames")) for item in metric["items"]
        ),
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
    profile: dict[str, Any],
    start: dt.date,
    metrics: dict[str, dict[str, Any]],
    end: dt.date | None = None,
    inventory: dict[str, Any] | None = None,
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
    if inventory:
        warnings.extend(inventory.get("warnings", []))
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
) -> dict[str, Any]:
    profile = project_profile(client.get(PROFILE_PATH))
    if all_available:
        activity_start = profile.get("activity_start")
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
            discover_inventory() if inventory_enabled else _inventory_disabled()
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
        "profile_cross_check": profile,
        "inventory": resolved_inventory,
        "metrics": metrics,
        "warnings": build_warnings(
            profile, resolved_start, metrics, end, resolved_inventory
        ),
    }
    report["selected_view"] = _selected_view_payload(report)
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
    if view == "possible-renames":
        return [item for item in items if item.get("possible_renames")]
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
) -> list[tuple[str, str, int]]:
    totals: dict[tuple[str, str], int] = defaultdict(int)
    for item in items:
        for row in item["daily"]:
            totals[(_period_label(row["date"], view), item["name"])] += row["count"]
    return [
        (period, name, count)
        for (period, name), count in sorted(
            totals.items(), key=lambda entry: (entry[0][0], entry[0][1].casefold())
        )
    ]


def _selected_view_payload(report: dict[str, Any]) -> dict[str, Any]:
    options = report["report_options"]
    view = options["view"]
    sort = options["sort"]
    recent_days = options["recent_days"]
    end = dt.date.fromisoformat(report["requested_range"]["end"])
    selected: dict[str, Any] = {
        "view": view,
        "sort": sort,
        "recent_days": recent_days,
        "metrics": {},
    }
    for kind, metric in report["metrics"].items():
        items = _sort_items(
            _view_items(metric["items"], view, recent_days, end), sort
        )
        if view in ("daily", "weekly", "monthly"):
            rows = [
                {"period": period, "name": name, "count": count}
                for period, name, count in _timeline_rows(items, view)
            ]
            selected["metrics"][kind] = {"row_count": len(rows), "rows": rows}
        else:
            names = [item["name"] for item in items]
            selected["metrics"][kind] = {
                "item_count": len(names),
                "item_names": names,
            }
    return selected


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
        "--format", choices=("json",), default="json", help="Output JSON (the default)"
    )
    parser.add_argument("--view", choices=VIEWS, default="current")
    parser.add_argument("--sort", choices=SORTS, default="most-used")
    parser.add_argument("--recent-days", type=int, default=30)
    parser.add_argument("--no-inventory", action="store_true")
    parser.add_argument("--auth-file", type=Path, default=default_auth_path())
    parser.add_argument("--timeout", type=float, default=30.0)
    return parser.parse_args(argv)


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
        )
    except UsageAnalyticsError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
