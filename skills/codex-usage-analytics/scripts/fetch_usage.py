#!/usr/bin/env python3
"""Fetch sanitized Codex skill and plugin analytics from ChatGPT's private API."""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
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
SCHEMA_VERSION = 1


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


def default_auth_path() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    root = Path(codex_home).expanduser() if codex_home else Path.home() / ".codex"
    return root / "auth.json"


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
                "User-Agent": "codex-usage-analytics/1",
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


def metric_config(kind: str) -> tuple[str, str, str]:
    if kind == "skills":
        return SKILL_PATH, "top_skill_limit", "skill_usage_overviews"
    if kind == "plugins":
        return PLUGIN_PATH, "top_plugin_limit", "plugin_usage_overviews"
    raise UsageAnalyticsError(f"unsupported metric kind {kind!r}")


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
            overviews = require_list(day.get(overview_field), f"{kind} overviews")
            if overviews:
                active_dates.add(date_value)
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
                else:
                    name = overview.get("display_name")
                    stable_id = (
                        overview.get("plugin_id")
                        or overview.get("plugin_name")
                        or name
                    )
                    identifiers = [overview.get("plugin_id")]
                if not isinstance(name, str) or not name:
                    raise UsageAnalyticsError(
                        f"unexpected private API schema at {kind} name"
                    )
                if not isinstance(stable_id, str) or not stable_id:
                    stable_id = name
                key = (stable_id, name)
                aggregate = records.setdefault(
                    key,
                    {
                        "name": name,
                        "count": 0,
                        "first_observed": date_value,
                        "last_observed": date_value,
                        "identifiers": set(),
                    },
                )
                aggregate["count"] += count
                aggregate["first_observed"] = min(
                    aggregate["first_observed"], date_value
                )
                aggregate["last_observed"] = max(
                    aggregate["last_observed"], date_value
                )
                if isinstance(identifiers, list):
                    aggregate["identifiers"].update(
                        value for value in identifiers if isinstance(value, str) and value
                    )

    items = [
        {
            **{key: value for key, value in record.items() if key != "identifiers"},
            "identifiers": sorted(record["identifiers"]),
        }
        for record in records.values()
    ]
    items.sort(key=lambda item: (-item["count"], item["name"].casefold()))
    other_count = sum(
        item["count"] for item in items if item["name"].casefold() == "other"
    )
    named_items = [item for item in items if item["name"].casefold() != "other"]
    observed_dates = [
        value
        for item in items
        for value in (item["first_observed"], item["last_observed"])
    ]
    return {
        "total_invocations": sum(item["count"] for item in items),
        "active_days": len(active_dates),
        "distinct_items": len(named_items),
        "first_recorded_date": min(observed_dates) if observed_dates else None,
        "last_recorded_date": max(observed_dates) if observed_dates else None,
        "data_freshness": max(freshness_values) if freshness_values else None,
        "complete_for_returned_days": other_count == 0,
        "other_invocations": other_count,
        "items": named_items,
    }


def build_warnings(
    profile: dict[str, Any],
    start: dt.date,
    metrics: dict[str, dict[str, Any]],
) -> list[str]:
    warnings = [
        "The endpoints are undocumented private ChatGPT infrastructure and may change.",
        "Invocation counts measure recorded use, not task success or skill value.",
        "Skill and plugin totals may overlap and must not be added together.",
    ]
    activity_start = profile.get("activity_start")
    if isinstance(activity_start, str) and activity_start < start.isoformat():
        warnings.append(
            "The requested range starts after the earliest activity visible in Profile."
        )
    first_dates = [
        metric["first_recorded_date"]
        for metric in metrics.values()
        if metric.get("first_recorded_date") is not None
    ]
    if isinstance(activity_start, str) and first_dates and activity_start < min(first_dates):
        warnings.append(
            "Profile activity predates the first returned analytics record; "
            "the report is not proven lifetime-complete."
        )
    if any(not metric["complete_for_returned_days"] for metric in metrics.values()):
        warnings.append(
            "At least one response retained an Other bucket, so named-item counts are truncated."
        )
    profile_skill_total = profile.get("total_skills_used")
    skill_metric = metrics.get("skills")
    if (
        isinstance(profile_skill_total, int)
        and skill_metric is not None
        and profile_skill_total != skill_metric["total_invocations"]
    ):
        warnings.append(
            "Profile total skill usage differs from the detailed daily analytics total; "
            "treat them as separate aggregates rather than reconciling either away."
        )
    return warnings


def build_report(
    client: ApiClient,
    *,
    kind: str,
    start: dt.date | None,
    end: dt.date,
    days: int | None,
    all_available: bool,
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

    kinds: Iterable[str] = ("skills", "plugins") if kind == "both" else (kind,)
    metrics = {
        metric_kind: collect_metric(client, metric_kind, resolved_start, end)
        for metric_kind in kinds
    }
    return {
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
        "profile_cross_check": profile,
        "metrics": metrics,
        "warnings": build_warnings(profile, resolved_start, metrics),
    }


def markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# Codex usage analytics",
        "",
        f"Requested range: {report['requested_range']['start']} through "
        f"{report['requested_range']['end']} "
        f"({report['requested_range']['windows']} request window(s)).",
        "",
    ]
    for kind, metric in report["metrics"].items():
        lines.extend(
            [
                f"## {kind.title()}",
                "",
                f"Recorded coverage: {metric['first_recorded_date'] or 'none'} through "
                f"{metric['last_recorded_date'] or 'none'}; "
                f"{metric['total_invocations']} invocations across "
                f"{metric['distinct_items']} named items on "
                f"{metric['active_days']} active days.",
                "",
                "| Name | Invocations | First observed | Last observed |",
                "| --- | ---: | --- | --- |",
            ]
        )
        for item in metric["items"]:
            safe_name = item["name"].replace("|", "\\|")
            lines.append(
                f"| {safe_name} | {item['count']} | "
                f"{item['first_observed']} | {item['last_observed']} |"
            )
        lines.append("")
        if not metric["complete_for_returned_days"]:
            lines.extend(
                [
                    f"Named rows are incomplete: {metric['other_invocations']} "
                    "invocations remained in Other.",
                    "",
                ]
            )

    lines.extend(["## Warnings", ""])
    lines.extend(f"- {warning}" for warning in report["warnings"])
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch sanitized skill and plugin usage from Codex's private "
            "ChatGPT analytics endpoints."
        )
    )
    range_group = parser.add_mutually_exclusive_group()
    range_group.add_argument("--start", type=parse_date)
    range_group.add_argument("--days", type=int)
    range_group.add_argument("--all-available", action="store_true")
    parser.add_argument("--end", type=parse_date, default=dt.datetime.now(dt.timezone.utc).date())
    parser.add_argument(
        "--kind", choices=("skills", "plugins", "both"), default="both"
    )
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--auth-file", type=Path, default=default_auth_path())
    parser.add_argument("--timeout", type=float, default=30.0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
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
        )
    except UsageAnalyticsError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        json.dump(report, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(markdown_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
