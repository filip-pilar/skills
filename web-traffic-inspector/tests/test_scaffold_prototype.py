from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "scaffold_prototype.py"
VALIDATOR = ROOT / "scripts" / "validate_prototype.py"


def base_spec() -> dict:
    return {
        "title": "Catalogue search",
        "description": "Shows the search mechanism.",
        "demonstrates": "The endpoint returns catalogue items.",
        "constraints": "Disposable proof only.",
        "mode": "direct",
        "localPort": 8765,
        "sideEffect": False,
        "verification": {
            "status": "verified",
            "relationship": "same-mechanism",
            "summary": "Synthetic reduced replay returned the expected records.",
        },
        "actionLabel": "Search",
        "inputs": [{"name": "query", "label": "Query", "type": "text", "required": True}],
        "request": {
            "url": "https://example.test/api/search",
            "method": "GET",
            "headers": {"Accept": "application/json"},
            "query": {"q": "{{query}}"},
        },
        "renderer": {"type": "table", "itemsPath": "results"},
    }


def page_runtime_spec() -> dict:
    spec = base_spec()
    spec["mode"] = "browser"
    spec["mechanismKind"] = "page-runtime-extraction"
    spec.pop("request")
    spec["verification"]["summary"] = "A fixed page projection returned the expected records."
    spec["companion"] = {
        "transport": "browser",
        "targetUrl": "https://example.test/catalogue/runtime?view=cards#ready",
        "targetStatePolicy": "allow-consumed",
        "allowedPageOrigins": ["https://example.test"],
        "allowedEndpointOrigins": [],
    }
    return spec


class ScaffoldTests(unittest.TestCase):
    def run_scaffold(self, spec: dict, output: Path, *extra: str) -> subprocess.CompletedProcess[str]:
        spec_path = output.parent / "spec.json"
        spec_path.write_text(json.dumps(spec), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--spec", str(spec_path), "--out", str(output), *extra],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_direct_mode_generates_demo_and_findings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            result = self.run_scaffold(base_spec(), output)
            self.assertEqual(result.returncode, 0, result.stderr)
            demo = (output / "demo.html").read_text(encoding="utf-8")
            self.assertIn("Catalogue search", demo)
            self.assertIn('"mode":"direct"', demo)
            self.assertIn('"mechanismKind":"http-replay"', demo)
            self.assertIn("WTI-CUSTOMIZE: request:start", demo)
            self.assertNotIn("__WTI_", demo)
            findings = (output / "FINDINGS.md").read_text(encoding="utf-8")
            self.assertIn("Catalogue search — findings", findings)
            self.assertIn("python3 -m http.server 8765", findings)
            self.assertIn("Status: `verified`", findings)
            self.assertIn("Mechanism kind: `http-replay`", findings)
            self.assertIn("## Scraping and integration readiness", findings)
            self.assertIn('id="verification-status"', demo)
            self.assertIn('id="execution-mode"', demo)
            self.assertIn('id="mechanism-kind"', demo)
            self.assertIn('id="mechanism-summary"', demo)
            self.assertIn('id="mechanism-stages"', demo)
            self.assertIn('id="raw-summary"', demo)
            self.assertIn('id="utility-status"', demo)
            self.assertIn('href="#main-content"', demo)
            self.assertIn(':focus-visible', demo)
            self.assertIn('control.autocomplete = "off"', demo)
            self.assertIn('const MAX_RENDERED_ITEMS = 50', demo)
            self.assertIn('consumeAcknowledgement();', demo)
            self.assertIn("WTI-CUSTOMIZE: response:start", demo)
            self.assertIn("WTI-CUSTOMIZE: workflow:start", demo)
            self.assertFalse((output / "browser-companion.mjs").exists())

    def test_page_runtime_generates_browser_only_fixed_recipe_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            result = self.run_scaffold(page_runtime_spec(), output)
            self.assertEqual(result.returncode, 0, result.stderr)
            demo = (output / "demo.html").read_text(encoding="utf-8")
            companion = (output / "browser-companion.mjs").read_text(encoding="utf-8")
            findings = (output / "FINDINGS.md").read_text(encoding="utf-8")
            self.assertIn('"mechanismKind":"page-runtime-extraction"', demo)
            self.assertNotIn('"request":', demo)
            self.assertIn('"targetPath":"/catalogue/runtime"', companion)
            self.assertIn('"targetSearchParams":[["view","cards"]]', companion)
            self.assertIn('"targetFragment":"ready"', companion)
            self.assertIn('"targetStatePolicy":"allow-consumed"', companion)
            self.assertIn('"requests":{}', companion)
            self.assertIn("WTI-CUSTOMIZE: page-runtime:start", companion)
            self.assertIn("WTI_PAGE_RUNTIME_RECIPE_REQUIRED", companion)
            self.assertIn("assertActiveBrowserPage(session, true)", companion)
            self.assertIn("Mechanism kind: `page-runtime-extraction`", findings)
            syntax = subprocess.run(
                ["node", "--check", str(output / "browser-companion.mjs")],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(syntax.returncode, 0, syntax.stderr)

    def test_interactive_profile_runtime_generates_exact_safe_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            profile = str(Path(directory) / "runtime profile")
            spec = base_spec()
            spec["mode"] = "browser"
            spec["companion"] = {
                "transport": "browser",
                "targetUrl": "https://example.test/app",
                "allowedPageOrigins": ["https://example.test"],
                "allowedEndpointOrigins": ["https://example.test"],
                "runtime": {
                    "authMode": "interactive-profile",
                    "session": "wti-auth-proof",
                    "profile": profile,
                },
            }
            result = self.run_scaffold(spec, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            demo = (output / "demo.html").read_text(encoding="utf-8")
            companion = (output / "browser-companion.mjs").read_text(encoding="utf-8")
            findings = (output / "FINDINGS.md").read_text(encoding="utf-8")
            self.assertIn('"runtime":{"authMode":"interactive-profile"}', demo)
            self.assertNotIn("wti-auth-proof", demo)
            self.assertNotIn(profile, demo)
            self.assertIn('"authMode":"interactive-profile"', companion)
            self.assertIn('"session":"wti-auth-proof"', companion)
            self.assertIn(profile, companion)
            command = next(line for line in findings.splitlines() if line.startswith("node "))
            self.assertIn("--session wti-auth-proof", command)
            self.assertIn("--profile", command)
            self.assertIn("'" + profile + "'", command)
            help_result = subprocess.run(
                ["node", str(output / "browser-companion.mjs"), "--help"],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(help_result.returncode, 0, help_result.stderr)
            self.assertIn("Configured authentication posture: interactive-profile", help_result.stdout)

            findings_path = output / "FINDINGS.md"
            findings_path.write_text(
                "\n".join(line for line in findings.splitlines() if "WTI-FINDINGS:" not in line),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, str(VALIDATOR), str(output)], text=True, capture_output=True, check=False
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)

            demo_path = output / "demo.html"
            leaked = demo_path.read_text(encoding="utf-8").replace(
                '"runtime":{"authMode":"interactive-profile"}',
                '"runtime":{"authMode":"interactive-profile","session":"wti-auth-proof"}',
            )
            demo_path.write_text(leaked, encoding="utf-8")
            rejected = subprocess.run(
                [sys.executable, str(VALIDATOR), str(output)], text=True, capture_output=True, check=False
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("must expose only authMode", rejected.stderr)

    def test_runtime_metadata_rejects_unsafe_or_incompatible_combinations(self) -> None:
        cases: list[tuple[str, dict, str]] = []
        missing_profile = page_runtime_spec()
        missing_profile["companion"]["runtime"] = {
            "authMode": "interactive-profile", "session": "wti-test"
        }
        cases.append(("missing-profile", missing_profile, "profile is required"))
        remote_cdp = page_runtime_spec()
        remote_cdp["companion"]["runtime"] = {
            "authMode": "cdp", "session": "wti-test", "cdp": "https://remote.example:9222"
        }
        cases.append(("remote-cdp", remote_cdp, "must be a loopback"))
        node_profile = base_spec()
        node_profile["mode"] = "relay"
        node_profile["companion"] = {
            "transport": "node",
            "allowedEndpointOrigins": ["https://example.test"],
            "runtime": {"authMode": "interactive-profile", "profile": "/tmp/profile"},
        }
        cases.append(("node-profile", node_profile, "Node transport supports only"))
        newline_profile = page_runtime_spec()
        newline_profile["companion"]["runtime"] = {
            "authMode": "interactive-profile", "session": "wti-test", "profile": "/tmp/a\n--cdp 1"
        }
        cases.append(("newline-profile", newline_profile, "single-line string"))
        for name, spec, diagnostic in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                result = self.run_scaffold(spec, Path(directory) / "output")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(diagnostic, result.stderr)

    def test_existing_session_and_runtime_headers_generate_restart_flags(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            existing = base_spec()
            existing["mode"] = "browser"
            existing["companion"] = {
                "transport": "browser",
                "targetUrl": "https://example.test/app",
                "allowedPageOrigins": ["https://example.test"],
                "allowedEndpointOrigins": ["https://example.test"],
                "runtime": {"authMode": "existing-session", "session": "prepared-proof"},
            }
            existing_output = root / "existing"
            result = self.run_scaffold(existing, existing_output)
            self.assertEqual(result.returncode, 0, result.stderr)
            existing_findings = (existing_output / "FINDINGS.md").read_text(encoding="utf-8")
            existing_command = next(line for line in existing_findings.splitlines() if line.startswith("node "))
            self.assertIn("--session prepared-proof", existing_command)
            self.assertIn("--no-prepare", existing_command)

            runtime_headers = base_spec()
            runtime_headers["mode"] = "relay"
            runtime_headers["companion"] = {
                "transport": "node",
                "allowedEndpointOrigins": ["https://example.test"],
                "runtime": {"authMode": "runtime-headers"},
            }
            headers_output = root / "headers"
            result = self.run_scaffold(runtime_headers, headers_output)
            self.assertEqual(result.returncode, 0, result.stderr)
            header_findings = (headers_output / "FINDINGS.md").read_text(encoding="utf-8")
            header_command = next(line for line in header_findings.splitlines() if line.startswith("node "))
            self.assertIn("--runtime-headers-stdin", header_command)

    def test_page_runtime_rejects_http_request_non_browser_and_generic_runtime_inputs(self) -> None:
        cases: list[tuple[str, dict, str]] = []
        with_request = page_runtime_spec()
        with_request["request"] = base_spec()["request"]
        cases.append(("request", with_request, "does not accept request"))
        direct = page_runtime_spec()
        direct["mode"] = "direct"
        direct.pop("companion")
        cases.append(("direct", direct, "requires mode browser"))
        url_input = page_runtime_spec()
        url_input["inputs"] = [{"name": "target", "label": "Target", "type": "url", "required": True}]
        cases.append(("url", url_input, "must be action data"))
        selector_input = page_runtime_spec()
        selector_input["inputs"] = [{"name": "selector", "label": "Selector", "type": "text", "required": True}]
        cases.append(("selector", selector_input, "must be action data"))
        sensitive_target = page_runtime_spec()
        sensitive_target["companion"]["targetUrl"] = "https://example.test/catalogue/runtime?access_token=embedded"
        cases.append(("sensitive-target", sensitive_target, "sensitive-looking query parameter"))
        consumed_without_state = page_runtime_spec()
        consumed_without_state["companion"]["targetUrl"] = "https://example.test/catalogue/runtime"
        cases.append(("consumed-without-state", consumed_without_state, "requires fixed query or fragment"))
        migrated_with_fragment = page_runtime_spec()
        migrated_with_fragment["companion"]["targetStatePolicy"] = "allow-query-to-fragment"
        cases.append(("migrated-with-fragment", migrated_with_fragment, "requires fixed query state and no configured fragment"))
        for name, spec, diagnostic in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                result = self.run_scaffold(spec, Path(directory) / "output")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(diagnostic, result.stderr)

    def test_page_runtime_validator_requires_completed_safe_recipe(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            result = self.run_scaffold(page_runtime_spec(), output)
            self.assertEqual(result.returncode, 0, result.stderr)
            findings = output / "FINDINGS.md"
            findings.write_text(
                "\n".join(line for line in findings.read_text(encoding="utf-8").splitlines() if "WTI-FINDINGS:" not in line),
                encoding="utf-8",
            )
            unfinished = subprocess.run(
                [sys.executable, str(VALIDATOR), str(output)], text=True, capture_output=True, check=False
            )
            self.assertNotEqual(unfinished.returncode, 0)
            self.assertIn("unfinished page-runtime recipe", unfinished.stderr)

            companion = output / "browser-companion.mjs"
            source = companion.read_text(encoding="utf-8")
            old = '''async function projectPageRuntime({ inputs, evaluate }) {
  throw new Error("WTI_PAGE_RUNTIME_RECIPE_REQUIRED: replace this fixed generated recipe with a narrowly projected JSON extraction.");
}'''
            safe = '''async function projectPageRuntime({ inputs, evaluate }) {
  return evaluate((pageInputs) => ({ query: pageInputs.query, items: [] }));
}'''
            self.assertEqual(source.count(old), 1)
            companion.write_text(source.replace(old, safe), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(VALIDATOR), str(output)], text=True, capture_output=True, check=False
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)

            unsafe = safe.replace("return evaluate", "void localStorage.length;\n  return evaluate")
            companion.write_text(companion.read_text(encoding="utf-8").replace(safe, unsafe), encoding="utf-8")
            rejected = subprocess.run(
                [sys.executable, str(VALIDATOR), str(output)], text=True, capture_output=True, check=False
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("forbidden browser storage inspection", rejected.stderr)

            dynamic = '''async function projectPageRuntime({ inputs, evaluate }) {
  return evaluate(inputs.query);
}'''
            companion.write_text(companion.read_text(encoding="utf-8").replace(unsafe, dynamic), encoding="utf-8")
            rejected = subprocess.run(
                [sys.executable, str(VALIDATOR), str(output)], text=True, capture_output=True, check=False
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("exactly one fixed inline evaluate function", rejected.stderr)

            geometry = '''async function projectPageRuntime({ inputs, evaluate }) {
  return evaluate(() => {
    const input = document.querySelector("#theme");
    return { visible: input.getClientRects().length > 0 };
  });
}'''
            companion.write_text(companion.read_text(encoding="utf-8").replace(dynamic, geometry), encoding="utf-8")
            rejected = subprocess.run(
                [sys.executable, str(VALIDATOR), str(output)], text=True, capture_output=True, check=False
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("native form-control geometry", rejected.stderr)

            broad_root = '''async function projectPageRuntime({ inputs, evaluate }) {
  return evaluate(() => {
    const root = document.querySelector("main");
    return { controls: root ? root.querySelectorAll("input").length : 0 };
  });
}'''
            companion.write_text(companion.read_text(encoding="utf-8").replace(geometry, broad_root), encoding="utf-8")
            rejected = subprocess.run(
                [sys.executable, str(VALIDATOR), str(output)], text=True, capture_output=True, check=False
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("broad structural page root", rejected.stderr)

    def test_search_select_detail_workflow_is_generated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            spec = base_spec()
            spec["request"]["method"] = "POST"
            spec["request"].pop("query")
            spec["request"]["body"] = {"query": "{{query}}"}
            spec["workflow"] = {
                "type": "search-select-detail",
                "itemsPath": "results",
                "valuePath": "id",
                "titlePath": "name",
                "selectionActionLabel": "Load details",
                "detailRequest": {
                    "url": "https://example.test/api/detail",
                    "method": "POST",
                    "headers": {"Accept": "application/json"},
                    "body": {"id": "{{selectedValue}}"},
                },
                "detailRenderer": {"type": "table", "itemsPath": "details"},
            }
            result = self.run_scaffold(spec, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            demo = (output / "demo.html").read_text(encoding="utf-8")
            self.assertIn('"type":"search-select-detail"', demo)
            self.assertIn("{{selectedValue}}", demo)
            self.assertIn("renderSelectionResults", demo)

    def test_search_select_detail_rejects_unknown_detail_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            spec = base_spec()
            spec["workflow"] = {
                "type": "search-select-detail",
                "itemsPath": "results",
                "valuePath": "id",
                "titlePath": "name",
                "selectionActionLabel": "Load details",
                "detailRequest": {
                    "url": "https://example.test/api/detail",
                    "method": "POST",
                    "headers": {},
                    "body": {"id": "{{missing}}"},
                },
                "detailRenderer": {"type": "auto"},
            }
            result = self.run_scaffold(spec, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unknown input placeholder", result.stderr)

    def test_template_sanitizers_preserve_aliases_and_detect_cycles(self) -> None:
        if not shutil.which("node"):
            self.skipTest("node is unavailable")
        probes = [
            (ROOT / "assets" / "demo-template.html", "function sanitizeUrlValue", "function setRaw"),
            (ROOT / "assets" / "browser-companion-template.mjs", "function sanitize", "function sendJson"),
        ]
        for source_path, start_marker, terminator in probes:
            script = r'''
const fs = require("node:fs");
const source = fs.readFileSync(process.argv[1], "utf8");
const start = source.indexOf(process.argv[2]);
const end = source.indexOf(process.argv[3], start);
if (start < 0 || end < 0) throw new Error("sanitize function not found");
var SECRET_KEY = /(?:authorization|cookie|password|passwd|secret|credential|session|private.?key|access.?token|refresh.?token|api.?key)/i;
var SENSITIVE_EXACT_KEY = /^(?:nonce|ticket)$/i;
var SENSITIVE_QUERY_KEY = /(?:^|[-_])(?:authorization|credential|secret|session|token|signature|sig|signed|private[-_]?key|api[-_]?key|access[-_]?key|key[-_]?pair[-_]?id|x[-_]?amz[-_](?:credential|signature|security[-_]?token)|code|nonce|ticket)(?:$|[-_])/i;
var URL_VALUE_KEY = /(?:^|[-_])(?:url|uri|href|link|location)(?:$|[-_])/i;
var SAFE_HEADER_NAMES = new Set(["content-type"]);
var MAX_RAW_CHARS = 2_000_000;
var MAX_COLLECTION_ITEMS = 5_000;
eval(source.slice(start, end));
const shared = {name: "shared"};
const root = {left: shared, right: shared};
root.self = root;
const result = sanitize(root);
if (result.left.name !== "shared" || result.right.name !== "shared") throw new Error("shared alias was corrupted");
if (result.self !== "[CIRCULAR]") throw new Error("real cycle was not detected");
'''
            result = subprocess.run(
                ["node", "-e", script, str(source_path), start_marker, terminator],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_template_raw_serialization_redacts_and_keeps_truncation_valid_json(self) -> None:
        if not shutil.which("node"):
            self.skipTest("node is unavailable")
        script = r'''
const fs = require("node:fs");
const source = fs.readFileSync(process.argv[1], "utf8");
const start = source.indexOf("function sanitizeUrlValue");
const end = source.indexOf("function setRaw", start);
if (start < 0 || end < 0) throw new Error("raw serialization helpers not found");
var SECRET_KEY = /(?:authorization|cookie|password|passwd|secret|credential|session|private.?key|access.?token|refresh.?token|api.?key|csrf|xsrf|signature|signed.?token)/i;
var SENSITIVE_EXACT_KEY = /^(?:nonce|ticket)$/i;
var SENSITIVE_QUERY_KEY = /(?:^|[-_])(?:authorization|credential|secret|session|token|signature|sig|signed|private[-_]?key|api[-_]?key|access[-_]?key|key[-_]?pair[-_]?id|x[-_]?amz[-_](?:credential|signature|security[-_]?token)|code|nonce|ticket)(?:$|[-_])/i;
var URL_VALUE_KEY = /(?:^|[-_])(?:url|uri|href|link|location)(?:$|[-_])/i;
var SAFE_HEADER_NAMES = new Set(["content-type", "content-length"]);
var MAX_RAW_CHARS = 700;
var MAX_COLLECTION_ITEMS = 5_000;
var location = { href: "http://127.0.0.1:8765/demo.html" };
eval(source.slice(start, end));
const result = serializeSanitized({
  request: { url: "https://example.test/api?q=shoes&token=secret" },
  response: {
    headers: { "content-type": "application/json", "authorization": "Bearer hidden", "x-private": "hidden" },
    body: { html: '<a href="https://cdn.test/file?signature=hidden">x</a>', value: "x".repeat(2_000) }
  }
});
const parsed = JSON.parse(result.text);
if (!result.truncated || parsed.wti?.truncated !== true) throw new Error("large JSON was not wrapped as a valid preview");
const sanitized = sanitize({
  request: { url: "https://example.test/api?q=shoes&token=secret" },
  response: {
    headers: { "content-type": "application/json", "authorization": "hidden", "x-private": "hidden" },
    body: { ticketPrice: 25, ticket: "secret-ticket" }
  }
});
const url = new URL(sanitized.request.url);
if (url.searchParams.get("token") !== "[REDACTED]") throw new Error("sensitive URL query value was not redacted");
if (sanitized.response.headers["content-type"] !== "application/json") throw new Error("safe header was removed");
if ("authorization" in sanitized.response.headers || "x-private" in sanitized.response.headers) throw new Error("unsafe header was retained");
if (sanitized.response.body.ticketPrice !== 25 || sanitized.response.body.ticket !== "[REDACTED]") throw new Error("exact-key redaction overreached");
'''
        result = subprocess.run(
            ["node", "-e", script, str(ROOT / "assets" / "demo-template.html")],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_browser_mode_generates_syntax_valid_companion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            spec = base_spec()
            spec["mode"] = "browser"
            spec["sideEffect"] = True
            spec["request"]["method"] = "POST"
            spec["request"].pop("query")
            spec["request"]["body"] = {"prompt": "{{query}}"}
            spec["companion"] = {
                "transport": "browser",
                "targetUrl": "https://example.test/app",
                "allowedPageOrigins": ["https://example.test"],
                "allowedEndpointOrigins": ["https://example.test"],
            }
            result = self.run_scaffold(spec, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            companion = output / "browser-companion.mjs"
            self.assertTrue(companion.exists())
            self.assertNotIn("__WTI_", companion.read_text(encoding="utf-8"))
            syntax = subprocess.run(["node", "--check", str(companion)], text=True, capture_output=True, check=False)
            self.assertEqual(syntax.returncode, 0, syntax.stderr)
            help_result = subprocess.run(["node", str(companion), "--help"], text=True, capture_output=True, check=False)
            self.assertEqual(help_result.returncode, 0, help_result.stderr)
            self.assertIn("--runtime-headers-stdin", help_result.stdout)
            self.assertIn("WTI-CUSTOMIZE: companion:start", companion.read_text(encoding="utf-8"))

    def test_legacy_spec_gets_safe_port_and_verification_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            spec = base_spec()
            spec.pop("localPort")
            spec.pop("verification")
            result = self.run_scaffold(spec, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            demo = (output / "demo.html").read_text(encoding="utf-8")
            findings = (output / "FINDINGS.md").read_text(encoding="utf-8")
            self.assertIn('"localPort":8000', demo)
            self.assertIn('"status":"provisional"', demo)
            self.assertIn("Status: `provisional`", findings)

    def test_captured_evidence_cannot_claim_verified_replay(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            spec = base_spec()
            spec["verification"]["relationship"] = "captured-evidence-only"
            result = self.run_scaffold(spec, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cannot use captured-evidence-only", result.stderr)

    def test_input_constraints_are_rendered(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            spec = base_spec()
            spec["inputs"] = [{
                "name": "query", "label": "Query", "type": "text", "required": True,
                "minLength": 2, "maxLength": 40, "pattern": "[A-Za-z -]+",
            }]
            result = self.run_scaffold(spec, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            demo = (output / "demo.html").read_text(encoding="utf-8")
            self.assertIn('"maxLength":40', demo)

    def test_sensitive_header_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            spec = base_spec()
            spec["request"]["headers"]["Authorization"] = "Bearer captured-secret"
            result = self.run_scaffold(spec, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("sensitive-looking header Authorization", result.stderr)
            self.assertFalse(output.exists())

    def test_sensitive_body_field_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            spec = base_spec()
            spec["request"]["method"] = "POST"
            spec["request"].pop("query")
            spec["request"]["body"] = {"api_key": "captured-secret", "query": "{{query}}"}
            result = self.run_scaffold(spec, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("sensitive-looking field", result.stderr)

    def test_inline_script_data_escapes_html_breakout_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            spec = base_spec()
            spec["description"] = "</script><script>globalThis.injected = true</script>"
            result = self.run_scaffold(spec, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            demo = (output / "demo.html").read_text(encoding="utf-8")
            self.assertNotIn("</script><script>globalThis.injected", demo)
            self.assertIn("\\u003c/script\\u003e", demo)

    def test_unknown_placeholder_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            spec = base_spec()
            spec["request"]["query"]["page"] = "{{missing}}"
            result = self.run_scaffold(spec, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unknown input placeholder", result.stderr)

    def test_get_body_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            spec = base_spec()
            spec["request"]["body"] = {"query": "{{query}}"}
            result = self.run_scaffold(spec, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not supported for GET", result.stderr)

    def test_existing_output_requires_force(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            first = self.run_scaffold(base_spec(), output)
            self.assertEqual(first.returncode, 0, first.stderr)
            second = self.run_scaffold(base_spec(), output)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("Refusing to overwrite", second.stderr)
            forced = self.run_scaffold(base_spec(), output, "--force")
            self.assertEqual(forced.returncode, 0, forced.stderr)

    def test_completed_findings_validator_rejects_prompts_then_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            result = self.run_scaffold(base_spec(), output)
            self.assertEqual(result.returncode, 0, result.stderr)
            pending = subprocess.run(
                [sys.executable, str(VALIDATOR), str(output)], text=True, capture_output=True, check=False
            )
            self.assertNotEqual(pending.returncode, 0)
            self.assertIn("still contains scaffold prompts", pending.stderr)
            findings = output / "FINDINGS.md"
            findings.write_text(
                "\n".join(line for line in findings.read_text(encoding="utf-8").splitlines() if "WTI-FINDINGS:" not in line),
                encoding="utf-8",
            )
            complete = subprocess.run(
                [sys.executable, str(VALIDATOR), str(output)], text=True, capture_output=True, check=False
            )
            self.assertEqual(complete.returncode, 0, complete.stderr)

    def test_completed_findings_validator_rejects_temporary_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            result = self.run_scaffold(base_spec(), output)
            self.assertEqual(result.returncode, 0, result.stderr)
            findings = output / "FINDINGS.md"
            findings.write_text(
                "\n".join(line for line in findings.read_text(encoding="utf-8").splitlines() if "WTI-FINDINGS:" not in line),
                encoding="utf-8",
            )
            (output / "spec.json").write_text("{}", encoding="utf-8")
            (output / "cors-probe.html").write_text("<!doctype html>", encoding="utf-8")
            (output / "evidence.json").write_text("{}", encoding="utf-8")

            rejected = subprocess.run(
                [sys.executable, str(VALIDATOR), str(output)], text=True, capture_output=True, check=False
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("temporary build or discovery artifacts", rejected.stderr)
            self.assertIn("spec.json", rejected.stderr)
            self.assertIn("cors-probe.html", rejected.stderr)
            self.assertNotIn("evidence.json", rejected.stderr)

            (output / "spec.json").unlink()
            (output / "cors-probe.html").unlink()
            accepted = subprocess.run(
                [sys.executable, str(VALIDATOR), str(output)], text=True, capture_output=True, check=False
            )
            self.assertEqual(accepted.returncode, 0, accepted.stderr)


if __name__ == "__main__":
    unittest.main()
