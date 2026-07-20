#!/usr/bin/env python3
"""Generate a disposable Web Traffic Inspector proof-prototype."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, unquote, urlparse


ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
PLACEHOLDER_PATTERN = re.compile(r"\{\{([A-Za-z][A-Za-z0-9_-]*)\}\}")
SENSITIVE_NAME = re.compile(
    r"(?:^|[-_])(?:authorization|cookie|password|passwd|secret|credential|session|private[-_]?key|access[-_]?token|refresh[-_]?token|api[-_]?key|signature)(?:$|[-_])",
    re.IGNORECASE,
)
ALLOWED_TOP = {
    "title", "description", "demonstrates", "constraints", "mode", "sideEffect",
    "actionLabel", "localPort", "verification", "inputs", "request", "renderer",
    "workflow", "companion", "mechanismKind",
}
ALLOWED_INPUT = {
    "name", "label", "type", "required", "placeholder", "value", "options",
    "min", "max", "step", "minLength", "maxLength", "pattern",
}
ALLOWED_VERIFICATION = {"status", "relationship", "summary"}
ALLOWED_REQUEST = {"url", "method", "headers", "query", "body", "credentials"}
ALLOWED_RENDERER = {"type", "itemsPath", "titlePath", "subtitlePath", "imagePath", "hrefPath"}
ALLOWED_WORKFLOW = {
    "type", "itemsPath", "valuePath", "titlePath", "subtitlePath", "imagePath",
    "hrefPath", "selectionActionLabel", "detailRequest", "detailRenderer",
}
ALLOWED_COMPANION = {"transport", "targetUrl", "targetStatePolicy", "allowedPageOrigins", "allowedEndpointOrigins", "runtime"}
ALLOWED_RUNTIME = {"authMode", "session", "profile", "cdp"}
INPUT_TYPES = {"text", "textarea", "number", "url", "select", "checkbox"}
METHODS = {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"}
RENDERERS = {"auto", "cards", "images", "table", "text"}
MODES = {"direct", "relay", "browser"}
WORKFLOWS = {"single", "search-select-detail"}
VERIFICATION_STATUSES = {"verified", "partial", "blocked", "provisional"}
MECHANISM_RELATIONSHIPS = {"same-mechanism", "equivalent-substitute", "captured-evidence-only"}
MECHANISM_KINDS = {"http-replay", "page-runtime-extraction"}
TARGET_STATE_POLICIES = {"exact", "allow-consumed", "allow-query-to-fragment"}
AUTH_MODES = {"none", "existing-session", "interactive-profile", "cdp", "runtime-headers"}
SESSION_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
PAGE_RUNTIME_FORBIDDEN_INPUT_NAMES = {
    "code", "javascript", "script", "selector", "targeturl", "target-url", "url",
}


class SpecError(ValueError):
    pass


def fail(message: str) -> None:
    raise SpecError(message)


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{label} must be an object.")
    return value


def reject_unknown(value: dict[str, Any], allowed: set[str], label: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        fail(f"{label} contains unknown field(s): {', '.join(unknown)}.")


def require_text(value: dict[str, Any], key: str, label: str | None = None) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result.strip():
        fail(f"{label or key} must be a non-empty string.")
    return result.strip()


def parse_http_url(value: str, label: str) -> tuple[str, str]:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        fail(f"{label} must be an absolute http:// or https:// URL.")
    if parsed.username is not None or parsed.password is not None:
        fail(f"{label} must not contain embedded credentials.")
    return f"{parsed.scheme}://{parsed.netloc}", parsed.query


def find_placeholders(value: Any) -> set[str]:
    if isinstance(value, str):
        return set(PLACEHOLDER_PATTERN.findall(value))
    if isinstance(value, list):
        return set().union(*(find_placeholders(item) for item in value)) if value else set()
    if isinstance(value, dict):
        found: set[str] = set()
        for key, item in value.items():
            found.update(find_placeholders(key))
            found.update(find_placeholders(item))
        return found
    return set()


def find_sensitive_keys(value: Any, prefix: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(key, str) and SENSITIVE_NAME.search(key):
                found.append(path)
            found.extend(find_sensitive_keys(item, path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(find_sensitive_keys(item, f"{prefix}[{index}]"))
    return found


def json_for_inline_script(value: Any) -> str:
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def validate_inputs(spec: dict[str, Any]) -> list[str]:
    inputs = spec.get("inputs")
    if not isinstance(inputs, list):
        fail("inputs must be an array.")
    names: list[str] = []
    for index, raw_input in enumerate(inputs):
        item = require_object(raw_input, f"inputs[{index}]")
        reject_unknown(item, ALLOWED_INPUT, f"inputs[{index}]")
        name = require_text(item, "name", f"inputs[{index}].name")
        if not NAME_PATTERN.fullmatch(name):
            fail(f"inputs[{index}].name must start with a letter and contain only letters, numbers, underscores, or hyphens.")
        if name in names:
            fail(f"Duplicate input name: {name}.")
        if SENSITIVE_NAME.search(name):
            fail(f"Input {name} appears to collect authentication material, which generated HTML must not do.")
        names.append(name)
        require_text(item, "label", f"inputs[{index}].label")
        input_type = require_text(item, "type", f"inputs[{index}].type")
        if input_type not in INPUT_TYPES:
            fail(f"inputs[{index}].type must be one of: {', '.join(sorted(INPUT_TYPES))}.")
        if "required" in item and not isinstance(item["required"], bool):
            fail(f"inputs[{index}].required must be a boolean.")
        if input_type == "select":
            options = item.get("options")
            if not isinstance(options, list) or not options:
                fail(f"inputs[{index}].options must be a non-empty array for a select input.")
            for option_index, option in enumerate(options):
                option = require_object(option, f"inputs[{index}].options[{option_index}]")
                if set(option) != {"label", "value"} or not all(isinstance(option[key], str) for key in option):
                    fail(f"inputs[{index}].options[{option_index}] must contain string label and value fields only.")
        elif "options" in item:
            fail(f"inputs[{index}].options is only valid for select inputs.")
        numeric_keys = {"min", "max", "step"} & set(item)
        if numeric_keys and input_type != "number":
            fail(f"inputs[{index}] numeric bounds are only valid for number inputs.")
        for key in numeric_keys:
            value = item[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                fail(f"inputs[{index}].{key} must be a number.")
        if "step" in item and item["step"] <= 0:
            fail(f"inputs[{index}].step must be greater than zero.")
        if "min" in item and "max" in item and item["min"] > item["max"]:
            fail(f"inputs[{index}].min must not exceed max.")
        text_keys = {"minLength", "maxLength", "pattern"} & set(item)
        if text_keys and input_type not in {"text", "textarea", "url"}:
            fail(f"inputs[{index}] text constraints are only valid for text, textarea, or url inputs.")
        for key in {"minLength", "maxLength"} & set(item):
            value = item[key]
            if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > 100_000:
                fail(f"inputs[{index}].{key} must be an integer from 0 through 100000.")
        if "minLength" in item and "maxLength" in item and item["minLength"] > item["maxLength"]:
            fail(f"inputs[{index}].minLength must not exceed maxLength.")
        if "pattern" in item:
            if not isinstance(item["pattern"], str) or not item["pattern"]:
                fail(f"inputs[{index}].pattern must be a non-empty regular expression string.")
            try:
                re.compile(item["pattern"])
            except re.error as error:
                fail(f"inputs[{index}].pattern is invalid: {error}.")
    return names


def validate_verification(spec: dict[str, Any]) -> None:
    verification = require_object(spec.get("verification", {
        "status": "provisional",
        "relationship": "same-mechanism",
        "summary": "Verification provenance has not yet been recorded.",
    }), "verification")
    reject_unknown(verification, ALLOWED_VERIFICATION, "verification")
    status = require_text(verification, "status", "verification.status")
    if status not in VERIFICATION_STATUSES:
        fail(f"verification.status must be one of: {', '.join(sorted(VERIFICATION_STATUSES))}.")
    relationship = require_text(verification, "relationship", "verification.relationship")
    if relationship not in MECHANISM_RELATIONSHIPS:
        fail(f"verification.relationship must be one of: {', '.join(sorted(MECHANISM_RELATIONSHIPS))}.")
    if status == "verified" and relationship == "captured-evidence-only":
        fail("verification.status verified cannot use captured-evidence-only relationship.")
    verification["summary"] = require_text(verification, "summary", "verification.summary")
    spec["verification"] = verification


def validate_request(spec: dict[str, Any], input_names: list[str]) -> tuple[dict[str, Any], str]:
    request = require_object(spec.get("request"), "request")
    reject_unknown(request, ALLOWED_REQUEST, "request")
    url = require_text(request, "url", "request.url")
    endpoint_origin, url_query = parse_http_url(url, "request.url")
    for name, _ in parse_qsl(url_query, keep_blank_values=True):
        if SENSITIVE_NAME.search(name):
            fail(f"request.url contains sensitive-looking query parameter {name}; supply it only at runtime.")
    method = require_text(request, "method", "request.method").upper()
    if method not in METHODS:
        fail(f"request.method must be one of: {', '.join(sorted(METHODS))}.")
    request["method"] = method
    headers = request.get("headers", {})
    if not isinstance(headers, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in headers.items()):
        fail("request.headers must be an object of string values.")
    for name in headers:
        if SENSITIVE_NAME.search(name):
            fail(f"request.headers contains sensitive-looking header {name}; supply it only at runtime.")
    query = request.get("query", {})
    if not isinstance(query, dict):
        fail("request.query must be an object.")
    for name in query:
        if SENSITIVE_NAME.search(name):
            fail(f"request.query contains sensitive-looking field {name}; supply it only at runtime.")
    if method in {"GET", "HEAD"} and "body" in request:
        fail(f"request.body is not supported for {method} requests.")
    sensitive_body_keys = find_sensitive_keys(request.get("body"))
    if sensitive_body_keys:
        fail(f"request.body contains sensitive-looking field(s): {', '.join(sensitive_body_keys)}; supply authentication only at runtime.")
    credentials = request.get("credentials", "omit")
    if credentials not in {"omit", "same-origin", "include"}:
        fail("request.credentials must be omit, same-origin, or include.")
    placeholders = find_placeholders({"headers": headers, "query": query, "body": request.get("body")})
    unknown_placeholders = sorted(placeholders - set(input_names))
    if unknown_placeholders:
        fail(f"Request uses unknown input placeholder(s): {', '.join(unknown_placeholders)}.")
    return request, endpoint_origin


def validate_renderer(spec: dict[str, Any]) -> None:
    renderer = spec.get("renderer", {"type": "auto"})
    renderer = require_object(renderer, "renderer")
    reject_unknown(renderer, ALLOWED_RENDERER, "renderer")
    renderer_type = renderer.get("type", "auto")
    if renderer_type not in RENDERERS:
        fail(f"renderer.type must be one of: {', '.join(sorted(RENDERERS))}.")
    for key, value in renderer.items():
        if key != "type" and (not isinstance(value, str) or not value.strip()):
            fail(f"renderer.{key} must be a non-empty dot-separated path.")
        if key != "type" and not all(NAME_PATTERN.fullmatch(part) for part in value.split(".")):
            fail(f"renderer.{key} contains an invalid path component.")
    spec["renderer"] = renderer


def validate_renderer_object(raw: Any, label: str) -> dict[str, Any]:
    wrapper = {"renderer": raw}
    try:
        validate_renderer(wrapper)
    except SpecError as error:
        message = str(error).replace("renderer", label, 1)
        fail(message)
    return wrapper["renderer"]


def validate_path(value: dict[str, Any], key: str, label: str, required: bool = False) -> None:
    if key not in value:
        if required:
            fail(f"{label}.{key} must be a non-empty dot-separated path.")
        return
    path = value[key]
    if not isinstance(path, str) or not path.strip():
        fail(f"{label}.{key} must be a non-empty dot-separated path.")
    if not all(NAME_PATTERN.fullmatch(part) for part in path.split(".")):
        fail(f"{label}.{key} contains an invalid path component.")


def validate_workflow(spec: dict[str, Any], input_names: list[str]) -> tuple[dict[str, Any], list[tuple[str, dict[str, Any], str]]]:
    raw = spec.get("workflow", {"type": "single"})
    workflow = require_object(raw, "workflow")
    reject_unknown(workflow, ALLOWED_WORKFLOW, "workflow")
    workflow_type = require_text(workflow, "type", "workflow.type")
    if workflow_type not in WORKFLOWS:
        fail(f"workflow.type must be one of: {', '.join(sorted(WORKFLOWS))}.")
    workflow["type"] = workflow_type
    if workflow_type == "single":
        if set(workflow) != {"type"}:
            fail("workflow type single does not accept additional fields.")
        spec["workflow"] = workflow
        return workflow, []

    for key in ("itemsPath", "valuePath", "titlePath"):
        validate_path(workflow, key, "workflow", required=True)
    for key in ("subtitlePath", "imagePath", "hrefPath"):
        validate_path(workflow, key, "workflow")
    workflow["selectionActionLabel"] = require_text(workflow, "selectionActionLabel", "workflow.selectionActionLabel")
    detail_request_wrapper = {"request": workflow.get("detailRequest")}
    detail_request, detail_origin = validate_request(detail_request_wrapper, [*input_names, "selectedValue"])
    workflow["detailRequest"] = detail_request
    workflow["detailRenderer"] = validate_renderer_object(workflow.get("detailRenderer", {"type": "auto"}), "workflow.detailRenderer")
    spec["workflow"] = workflow
    return workflow, [("detail", detail_request, detail_origin)]


def validate_cdp(value: str) -> str:
    if value.isdigit():
        port = int(value)
        if 1 <= port <= 65535:
            return value
        fail("companion.runtime.cdp port must be from 1 through 65535.")
    parsed = urlparse(value)
    try:
        port = parsed.port
    except ValueError:
        fail("companion.runtime.cdp contains an invalid port.")
    if (
        parsed.scheme not in {"http", "https"}
        or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
        or port is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        fail("companion.runtime.cdp must be a loopback port or loopback http(s) URL without credentials, query, or fragment.")
    return value


def validate_runtime(raw: Any, transport: str) -> dict[str, Any]:
    runtime = require_object({} if raw is None else raw, "companion.runtime")
    reject_unknown(runtime, ALLOWED_RUNTIME, "companion.runtime")
    auth_mode = runtime.get("authMode", "none")
    if auth_mode not in AUTH_MODES:
        fail(f"companion.runtime.authMode must be one of: {', '.join(sorted(AUTH_MODES))}.")
    session = runtime.get("session", "wti-demo" if transport == "browser" else "")
    if not isinstance(session, str) or (session and not SESSION_PATTERN.fullmatch(session)):
        fail("companion.runtime.session must contain only letters, numbers, underscores, and hyphens and be at most 64 characters.")
    profile = runtime.get("profile", "")
    cdp = runtime.get("cdp", "")
    for key, value in (("profile", profile), ("cdp", cdp)):
        if not isinstance(value, str) or any(character in value for character in "\0\r\n"):
            fail(f"companion.runtime.{key} must be a single-line string.")

    if transport == "browser":
        if auth_mode == "runtime-headers":
            fail("companion.runtime.authMode runtime-headers is only valid for node transport.")
        if not session:
            fail("companion.runtime.session is required for browser transport.")
        if auth_mode == "interactive-profile":
            if not profile:
                fail("companion.runtime.profile is required for interactive-profile authentication.")
            if cdp:
                fail("companion.runtime.cdp is not valid with interactive-profile authentication.")
        elif auth_mode == "cdp":
            if not cdp:
                fail("companion.runtime.cdp is required for cdp authentication.")
            validate_cdp(cdp)
            if profile:
                fail("companion.runtime.profile is not valid with cdp authentication.")
        elif profile or cdp:
            fail("companion.runtime.profile and cdp require their matching authentication mode.")
    else:
        if auth_mode not in {"none", "runtime-headers"}:
            fail("Node transport supports only none or runtime-headers authentication.")
        if session or profile or cdp:
            fail("companion.runtime session, profile, and cdp are only valid for browser transport.")

    return {
        "authMode": auth_mode,
        "session": session,
        "profile": profile,
        "cdp": cdp,
        "prepare": transport == "browser" and auth_mode != "existing-session",
        "runtimeHeadersStdin": transport == "node" and auth_mode == "runtime-headers",
    }


def validate_companion(spec: dict[str, Any], endpoint_origin: str | None) -> dict[str, Any] | None:
    mode = spec["mode"]
    raw = spec.get("companion")
    if mode == "direct":
        if raw is not None:
            fail("companion is not valid when mode is direct.")
        return None
    companion = require_object(raw, "companion")
    reject_unknown(companion, ALLOWED_COMPANION, "companion")
    transport = require_text(companion, "transport", "companion.transport")
    expected = "browser" if mode == "browser" else "node"
    if transport != expected:
        fail(f"mode {mode} requires companion.transport {expected}.")
    companion["runtime"] = validate_runtime(companion.get("runtime"), transport)
    endpoint_origins = companion.get("allowedEndpointOrigins", [endpoint_origin] if endpoint_origin else [])
    if not isinstance(endpoint_origins, list):
        fail("companion.allowedEndpointOrigins must be an array.")
    if endpoint_origin and not endpoint_origins:
        fail("companion.allowedEndpointOrigins must be a non-empty array for HTTP replay.")
    normalized_endpoints = [parse_http_url(origin, "companion.allowedEndpointOrigins entry")[0] for origin in endpoint_origins]
    if endpoint_origin and endpoint_origin not in normalized_endpoints:
        fail("companion.allowedEndpointOrigins must include request.url's origin.")
    companion["allowedEndpointOrigins"] = sorted(set(normalized_endpoints))
    if transport == "browser":
        target_url = require_text(companion, "targetUrl", "companion.targetUrl")
        target_origin, _ = parse_http_url(target_url, "companion.targetUrl")
        parsed_target = urlparse(target_url)
        for name, _ in parse_qsl(parsed_target.query, keep_blank_values=True):
            if SENSITIVE_NAME.search(name):
                fail(f"companion.targetUrl contains sensitive-looking query parameter {name}; authentication must remain runtime-only.")
        if parsed_target.fragment and SENSITIVE_NAME.search(unquote(parsed_target.fragment)):
            fail("companion.targetUrl contains a sensitive-looking fragment; authentication must remain runtime-only.")
        target_state_policy = companion.get("targetStatePolicy", "exact")
        if target_state_policy not in TARGET_STATE_POLICIES:
            fail(f"companion.targetStatePolicy must be one of: {', '.join(sorted(TARGET_STATE_POLICIES))}.")
        companion["targetStatePolicy"] = target_state_policy
        page_origins = companion.get("allowedPageOrigins", [target_origin])
        if not isinstance(page_origins, list) or not page_origins:
            fail("companion.allowedPageOrigins must be a non-empty array.")
        normalized_pages = [parse_http_url(origin, "companion.allowedPageOrigins entry")[0] for origin in page_origins]
        if target_origin not in normalized_pages:
            fail("companion.allowedPageOrigins must include companion.targetUrl's origin.")
        companion["allowedPageOrigins"] = sorted(set(normalized_pages))
    else:
        if "targetUrl" in companion or "targetStatePolicy" in companion or "allowedPageOrigins" in companion:
            fail("targetUrl, targetStatePolicy, and allowedPageOrigins are only valid for browser transport.")
        companion["targetUrl"] = ""
        companion["targetStatePolicy"] = "exact"
        companion["allowedPageOrigins"] = []
    return companion


def validate_spec(raw: Any) -> tuple[dict[str, Any], dict[str, Any] | None]:
    spec = require_object(raw, "spec")
    spec = json.loads(json.dumps(spec))
    reject_unknown(spec, ALLOWED_TOP, "spec")
    for key in ("title", "description", "demonstrates", "constraints", "actionLabel"):
        spec[key] = require_text(spec, key)
    mode = require_text(spec, "mode")
    if mode not in MODES:
        fail(f"mode must be one of: {', '.join(sorted(MODES))}.")
    spec["mode"] = mode
    if not isinstance(spec.get("sideEffect"), bool):
        fail("sideEffect must be a boolean.")
    mechanism_kind = spec.get("mechanismKind", "http-replay")
    if mechanism_kind not in MECHANISM_KINDS:
        fail(f"mechanismKind must be one of: {', '.join(sorted(MECHANISM_KINDS))}.")
    spec["mechanismKind"] = mechanism_kind
    local_port = spec.get("localPort", 8000 if mode == "direct" else 8765)
    if isinstance(local_port, bool) or not isinstance(local_port, int) or not 1024 <= local_port <= 65535:
        fail("localPort must be an integer from 1024 through 65535.")
    spec["localPort"] = local_port
    validate_verification(spec)
    input_names = validate_inputs(spec)
    if mechanism_kind == "page-runtime-extraction":
        if mode != "browser":
            fail("mechanismKind page-runtime-extraction requires mode browser.")
        if "request" in spec:
            fail("mechanismKind page-runtime-extraction does not accept request; the generated fixed page recipe is the only execution path.")
        for definition in spec["inputs"]:
            normalized_name = definition["name"].lower()
            if definition["type"] == "url" or normalized_name in PAGE_RUNTIME_FORBIDDEN_INPUT_NAMES:
                fail("Page-runtime inputs must be action data, not JavaScript, selectors, or target URLs.")
        request = None
        endpoint_origin = None
    else:
        request, endpoint_origin = validate_request(spec, input_names)
        spec["request"] = request
    validate_renderer(spec)
    workflow, workflow_requests = validate_workflow(spec, input_names)
    if mechanism_kind == "page-runtime-extraction" and workflow["type"] != "single":
        fail("Page-runtime extraction supports only the bounded single workflow.")
    companion = validate_companion(spec, endpoint_origin)
    if companion and companion["targetStatePolicy"] == "allow-consumed":
        target = urlparse(companion["targetUrl"])
        if mechanism_kind != "page-runtime-extraction":
            fail("companion.targetStatePolicy allow-consumed is only valid for page-runtime extraction.")
        if not target.query and not target.fragment:
            fail("companion.targetStatePolicy allow-consumed requires fixed query or fragment state to consume.")
    if companion and companion["targetStatePolicy"] == "allow-query-to-fragment":
        target = urlparse(companion["targetUrl"])
        if mechanism_kind != "page-runtime-extraction":
            fail("companion.targetStatePolicy allow-query-to-fragment is only valid for page-runtime extraction.")
        if not target.query or target.fragment:
            fail("companion.targetStatePolicy allow-query-to-fragment requires fixed query state and no configured fragment.")
    companion_config = None
    if companion:
        requests = {} if request is None else {"main": request, "search": request}
        endpoint_origins = set() if endpoint_origin is None else {endpoint_origin}
        for request_key, workflow_request, workflow_origin in workflow_requests:
            requests[request_key] = workflow_request
            endpoint_origins.add(workflow_origin)
        missing_origins = endpoint_origins - set(companion["allowedEndpointOrigins"])
        if missing_origins:
            fail(f"companion.allowedEndpointOrigins must include workflow request origin(s): {', '.join(sorted(missing_origins))}.")
        target = urlparse(companion["targetUrl"])
        companion_config = {
            "transport": companion["transport"],
            "targetUrl": companion["targetUrl"],
            "targetPath": target.path or "/",
            "targetSearchParams": parse_qsl(target.query, keep_blank_values=True),
            "targetFragment": unquote(target.fragment),
            "targetStatePolicy": companion["targetStatePolicy"],
            "allowedPageOrigins": companion["allowedPageOrigins"],
            "allowedEndpointOrigins": companion["allowedEndpointOrigins"],
            "inputNames": input_names,
            "runtimeInputNames": ["selectedValue"] if workflow["type"] == "search-select-detail" else [],
            "inputDefinitions": spec["inputs"],
            "localPort": spec["localPort"],
            "sideEffect": spec["sideEffect"],
            "mechanismKind": mechanism_kind,
            "runtime": companion["runtime"],
            "request": request,
            "requests": requests,
        }
    return spec, companion_config


def render_template(path: Path, replacements: dict[str, str]) -> str:
    rendered = path.read_text(encoding="utf-8")
    for marker, replacement in replacements.items():
        count = rendered.count(marker)
        if count != 1:
            fail(f"Template {path.name} must contain {marker} exactly once; found {count}.")
        rendered = rendered.replace(marker, replacement)
    leftovers = sorted(set(re.findall(r"__WTI_[A-Z0-9_]+__", rendered)))
    if leftovers:
        fail(f"Template {path.name} contains unresolved marker(s): {', '.join(leftovers)}.")
    return rendered


def atomic_write(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        fail(f"Refusing to overwrite existing file: {path}. Use --force to replace generated files.")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def build(spec_path: Path, output: Path, force: bool) -> list[Path]:
    try:
        raw = json.loads(spec_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        fail(f"Spec file does not exist: {spec_path}.")
    except json.JSONDecodeError as error:
        fail(f"Spec is not valid JSON: line {error.lineno}, column {error.colno}.")
    spec, companion = validate_spec(raw)
    document_title = spec["title"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    demo_spec = json.loads(json.dumps(spec))
    if companion:
        demo_spec["companion"]["runtime"] = {"authMode": companion["runtime"]["authMode"]}
    demo = render_template(
        ASSETS / "demo-template.html",
        {
            "__WTI_DOCUMENT_TITLE__": document_title,
            "__WTI_DEMO_CONFIG__": json_for_inline_script(demo_spec),
        },
    )
    if spec["mode"] == "direct":
        run_command = f"python3 -m http.server {spec['localPort']} --bind 127.0.0.1 --directory {shlex.quote(str(output))}"
        demo_url = f"http://127.0.0.1:{spec['localPort']}/demo.html"
    else:
        command = ["node", str(output / "browser-companion.mjs"), "--port", str(spec["localPort"])]
        runtime = companion["runtime"]
        if companion["transport"] == "browser":
            command.extend(["--session", runtime["session"]])
            if runtime["authMode"] == "interactive-profile":
                command.extend(["--profile", runtime["profile"]])
            elif runtime["authMode"] == "cdp":
                command.extend(["--cdp", runtime["cdp"]])
            elif runtime["authMode"] == "existing-session":
                command.append("--no-prepare")
        elif runtime["runtimeHeadersStdin"]:
            command.append("--runtime-headers-stdin")
        run_command = shlex.join(command)
        demo_url = f"http://127.0.0.1:{spec['localPort']}/"
    findings = render_template(
        ASSETS / "findings-template.md",
        {
            "__WTI_FINDINGS_TITLE__": spec["title"],
            "__WTI_FINDINGS_MODE__": spec["mode"],
            "__WTI_FINDINGS_MECHANISM_KIND__": spec["mechanismKind"],
            "__WTI_FINDINGS_DEMONSTRATES__": spec["demonstrates"],
            "__WTI_FINDINGS_CONSTRAINTS__": spec["constraints"],
            "__WTI_FINDINGS_VERIFICATION_STATUS__": spec["verification"]["status"],
            "__WTI_FINDINGS_MECHANISM_RELATIONSHIP__": spec["verification"]["relationship"],
            "__WTI_FINDINGS_VERIFICATION_SUMMARY__": spec["verification"]["summary"],
            "__WTI_RUN_COMMAND__": run_command,
            "__WTI_DEMO_URL__": demo_url,
        },
    )
    generated = [output / "demo.html", output / "FINDINGS.md"]
    pending: list[tuple[Path, str]] = [(generated[0], demo), (generated[1], findings)]
    if companion:
        companion_source = render_template(
            ASSETS / "browser-companion-template.mjs",
            {"__WTI_COMPANION_CONFIG__": json.dumps(companion, ensure_ascii=False, separators=(",", ":"))},
        )
        generated.append(output / "browser-companion.mjs")
        pending.append((generated[-1], companion_source))
    for path, _ in pending:
        if path.exists() and not force:
            fail(f"Refusing to overwrite existing file: {path}. Use --force to replace generated files.")
    for path, content in pending:
        atomic_write(path, content, force=True)
    if companion:
        generated[-1].chmod(generated[-1].stat().st_mode | 0o111)
    return generated


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, type=Path, help="Path to the non-secret JSON prototype spec.")
    parser.add_argument("--out", required=True, type=Path, help="Directory for demo.html and any companion.")
    parser.add_argument("--force", action="store_true", help="Replace generated files that already exist.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = parse_args(argv or sys.argv[1:])
    try:
        generated = build(arguments.spec.resolve(), arguments.out.resolve(), arguments.force)
    except (OSError, SpecError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    for path in generated:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
