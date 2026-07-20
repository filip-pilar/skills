from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent.parent
SCAFFOLD = ROOT / "scripts" / "scaffold_prototype.py"


class SyntheticHandler(BaseHTTPRequestHandler):
    demo_file: Path | None = None
    allowed_cors_origin: str | None = None

    def log_message(self, format: str, *args: object) -> None:
        return

    def send_cors_headers(self) -> None:
        origin = self.headers.get("Origin")
        if origin and origin == self.allowed_cors_origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")

    def send_body(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_cors_headers()
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        if self.path == "/demo.html" and self.demo_file:
            body = self.demo_file.read_bytes()
            self.send_body(200, body, "text/html; charset=utf-8")
            return
        if self.path.startswith("/api/status-json"):
            self.send_body(503, b'{"error":"synthetic unavailable"}', "application/json")
            return
        if self.path.startswith("/api/status-text"):
            self.send_body(500, b"synthetic failure", "text/plain; charset=utf-8")
            return
        if self.path.startswith("/api/plain"):
            self.send_body(200, b"synthetic plain response", "text/plain; charset=utf-8")
            return
        if self.path.startswith("/api/malformed"):
            self.send_body(200, b'{"broken":', "application/json")
            return
        if self.path.startswith("/api/large"):
            self.send_body(200, b"x" * 5_000_001, "text/plain; charset=utf-8")
            return
        if self.path.startswith("/api/search"):
            query = parse_qs(urlparse(self.path).query).get("q", [""])[0]
            results = (
                [{"name": f"Synthetic result {index}"} for index in range(60)]
                if query == "many"
                else [{"name": "Synthetic result"}]
            )
            body = json.dumps({"results": results, "access_token": "must-redact"}).encode()
            self.send_body(200, body, "application/json")
            return
        if self.path.split("?", 1)[0] == "/runtime/catalogue":
            body = b'''<!doctype html><title>Runtime catalogue</title>
<main><h1>Runtime catalogue</h1><ul id="runtime-items"></ul></main>
<script>
const records = [{id: "runtime-1", name: "Runtime one"}, {id: "runtime-2", name: "Runtime two"}];
document.querySelector("#runtime-items").replaceChildren(...records.map((record) => {
  const item = document.createElement("li"); item.dataset.id = record.id; item.textContent = record.name; return item;
}));
</script>'''
            self.send_body(200, body, "text/html; charset=utf-8")
            return
        self.send_body(200, b"<!doctype html><title>Synthetic target</title><h1>Synthetic target</h1>", "text/html")

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length) or b"{}")
        if self.path.startswith("/api/detail"):
            body = json.dumps({"details": [{"name": f"Detail {payload.get('id', 'missing')}"}]}).encode()
        else:
            query = payload.get("query", "missing")
            body = json.dumps({"results": [{"id": query, "name": query}]}).encode()
        self.send_body(200, body, "application/json")


class PrototypeHandler(BaseHTTPRequestHandler):
    demo_file: Path | None = None

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:
        if self.path.split("?", 1)[0] in {"/", "/demo.html"} and self.demo_file:
            body = self.demo_file.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()


class CompanionIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.target = ThreadingHTTPServer(("127.0.0.1", 0), SyntheticHandler)
        cls.target_thread = threading.Thread(target=cls.target.serve_forever, daemon=True)
        cls.target_thread.start()
        cls.target_origin = f"http://127.0.0.1:{cls.target.server_address[1]}"
        cls.prototype = ThreadingHTTPServer(("127.0.0.1", 0), PrototypeHandler)
        cls.prototype_thread = threading.Thread(target=cls.prototype.serve_forever, daemon=True)
        cls.prototype_thread.start()
        cls.prototype_origin = f"http://127.0.0.1:{cls.prototype.server_address[1]}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.target.shutdown()
        cls.target.server_close()
        cls.prototype.shutdown()
        cls.prototype.server_close()

    def spec(self, mode: str) -> dict:
        request = {
            "url": f"{self.target_origin}/api/search",
            "method": "GET" if mode == "relay" else "POST",
            "headers": {"Accept": "application/json"},
        }
        if mode == "relay":
            request["query"] = {"q": "{{query}}"}
        else:
            request["body"] = {"query": "{{query}}"}
        return {
            "title": "Synthetic search",
            "description": "Exercises the generated companion.",
            "demonstrates": "A fixed synthetic request.",
            "constraints": "Local integration test only.",
            "mode": mode,
            "localPort": 8765,
            "sideEffect": mode == "browser",
            "verification": {
                "status": "verified",
                "relationship": "same-mechanism",
                "summary": "Synthetic execution verifies the generated transport.",
            },
            "actionLabel": "Run",
            "inputs": [{"name": "query", "label": "Query", "type": "text", "required": True}],
            "request": request,
            "renderer": {"type": "table", "itemsPath": "results"},
            "companion": {
                "transport": "node" if mode == "relay" else "browser",
                **({} if mode == "relay" else {"targetUrl": self.target_origin}),
                "allowedEndpointOrigins": [self.target_origin],
                **({} if mode == "relay" else {"allowedPageOrigins": [self.target_origin]}),
            },
        }

    def direct_spec(self) -> dict:
        spec = self.spec("relay")
        spec["mode"] = "direct"
        spec.pop("companion")
        return spec

    def workflow_spec(self, mode: str) -> dict:
        spec = {
            "title": "Synthetic search and detail",
            "description": "Exercises an explicit two-stage workflow.",
            "demonstrates": "A selected search result supplies the detail request identifier.",
            "constraints": "Local integration test only.",
            "mode": mode,
            "localPort": 8765,
            "sideEffect": False,
            "verification": {
                "status": "verified",
                "relationship": "same-mechanism",
                "summary": "Synthetic workflow verifies explicit selection and detail loading.",
            },
            "actionLabel": "Search",
            "inputs": [{"name": "query", "label": "Query", "type": "text", "required": True}],
            "request": {
                "url": f"{self.target_origin}/api/search",
                "method": "POST",
                "headers": {"Accept": "application/json"},
                "body": {"query": "{{query}}"},
            },
            "renderer": {"type": "auto"},
            "workflow": {
                "type": "search-select-detail",
                "itemsPath": "results",
                "valuePath": "id",
                "titlePath": "name",
                "selectionActionLabel": "Load details",
                "detailRequest": {
                    "url": f"{self.target_origin}/api/detail",
                    "method": "POST",
                    "headers": {"Accept": "application/json"},
                    "body": {"id": "{{selectedValue}}"},
                },
                "detailRenderer": {"type": "table", "itemsPath": "details"},
            },
        }
        if mode != "direct":
            spec["companion"] = {
                "transport": "node" if mode == "relay" else "browser",
                **({} if mode == "relay" else {"targetUrl": self.target_origin}),
                "allowedEndpointOrigins": [self.target_origin],
                **({} if mode == "relay" else {"allowedPageOrigins": [self.target_origin]}),
            }
        return spec

    def page_runtime_spec(self) -> dict:
        return {
            "title": "Synthetic runtime catalogue",
            "description": "Exercises a fixed generated page projection.",
            "demonstrates": "Client-computed DOM records are projected as bounded JSON.",
            "constraints": "One fixed synthetic page and projection.",
            "mode": "browser",
            "mechanismKind": "page-runtime-extraction",
            "localPort": 8765,
            "sideEffect": False,
            "verification": {
                "status": "verified",
                "relationship": "same-mechanism",
                "summary": "Synthetic browser execution verifies the page-runtime transport.",
            },
            "actionLabel": "Inspect",
            "inputs": [{"name": "query", "label": "Query", "type": "text", "required": True}],
            "renderer": {"type": "table", "itemsPath": "items"},
            "companion": {
                "transport": "browser",
                "targetUrl": f"{self.target_origin}/runtime/catalogue?view=cards",
                "targetStatePolicy": "allow-consumed",
                "allowedPageOrigins": [self.target_origin],
                "allowedEndpointOrigins": [],
            },
        }

    def scaffold(self, directory: Path, mode: str) -> Path:
        spec_path = directory / "spec.json"
        output = directory / "output"
        spec_path.write_text(json.dumps(self.spec(mode)), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCAFFOLD), "--spec", str(spec_path), "--out", str(output)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return output

    def scaffold_spec(self, directory: Path, spec: dict) -> Path:
        spec_path = directory / "spec.json"
        output = directory / "output"
        spec_path.write_text(json.dumps(spec), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCAFFOLD), "--spec", str(spec_path), "--out", str(output)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return output

    def install_page_runtime_recipe(self, output: Path) -> None:
        companion = output / "browser-companion.mjs"
        source = companion.read_text(encoding="utf-8")
        old = '''async function projectPageRuntime({ inputs, evaluate }) {
  throw new Error("WTI_PAGE_RUNTIME_RECIPE_REQUIRED: replace this fixed generated recipe with a narrowly projected JSON extraction.");
}'''
        new = '''async function projectPageRuntime({ inputs, evaluate }) {
  return evaluate((pageInputs) => {
    const query = pageInputs.query.trim().toLowerCase();
    const items = [...document.querySelectorAll("#runtime-items > li")]
      .map((item) => ({ id: item.dataset.id || "", name: item.textContent?.trim() || "" }))
      .filter((item) => !query || item.name.toLowerCase().includes(query));
    return { query, items };
  });
}'''
        self.assertEqual(source.count(old), 1)
        companion.write_text(source.replace(old, new), encoding="utf-8")

    def start_companion(self, output: Path, *arguments: str, env: dict[str, str] | None = None) -> tuple[subprocess.Popen[str], str]:
        arguments = arguments if "--port" in arguments else ("--port", "0", *arguments)
        process = subprocess.Popen(
            ["node", str(output / "browser-companion.mjs"), *arguments],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        assert process.stdout is not None
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            line = process.stdout.readline().strip()
            if line.startswith("Web Traffic Inspector companion: "):
                return process, line.removeprefix("Web Traffic Inspector companion: ")
            if process.poll() is not None:
                break
        assert process.stderr is not None
        diagnostics = process.stderr.read()
        process.terminate()
        self.fail(f"Companion did not start: {diagnostics}")

    def execute(self, origin: str, query: str = "hello", request_key: str | None = None, selected_value: str | None = None) -> tuple[int, dict]:
        config = json.loads(urllib.request.urlopen(f"{origin}__wti/config", timeout=5).read())
        inputs = {"query": query}
        if selected_value is not None:
            inputs["selectedValue"] = selected_value
        payload = {"inputs": inputs}
        if request_key is not None:
            payload["requestKey"] = request_key
        body = json.dumps(payload).encode()
        request = urllib.request.Request(
            f"{origin}__wti/execute",
            data=body,
            method="POST",
            headers={"Content-Type": "application/json", "Origin": origin.rstrip("/"), "X-WTI-Token": config["token"]},
        )
        try:
            response = urllib.request.urlopen(request, timeout=30)
            return response.status, json.loads(response.read())
        except urllib.error.HTTPError as error:
            try:
                return error.code, json.loads(error.read())
            finally:
                error.close()

    def stop_process(self, process: subprocess.Popen[str]) -> None:
        process.terminate()
        process.wait(timeout=5)
        if process.stdout:
            process.stdout.close()
        if process.stderr:
            process.stderr.close()

    def test_node_transport_executes_fixed_request_and_redacts(self) -> None:
        if not shutil.which("node"):
            self.skipTest("node is unavailable")
        with tempfile.TemporaryDirectory() as directory:
            output = self.scaffold(Path(directory), "relay")
            process, origin = self.start_companion(output, "--no-prepare")
            try:
                status, payload = self.execute(origin)
                self.assertEqual(status, 200)
                self.assertEqual(payload["response"]["body"]["results"][0]["name"], "Synthetic result")
                self.assertEqual(payload["response"]["body"]["access_token"], "[REDACTED]")
            finally:
                self.stop_process(process)

    def test_node_transport_enforces_generated_input_constraints(self) -> None:
        if not shutil.which("node"):
            self.skipTest("node is unavailable")
        with tempfile.TemporaryDirectory() as directory:
            spec = self.spec("relay")
            spec["inputs"][0]["maxLength"] = 5
            output = self.scaffold_spec(Path(directory), spec)
            process, origin = self.start_companion(output, "--no-prepare")
            try:
                status, payload = self.execute(origin, "too-long")
                self.assertEqual(status, 502)
                self.assertIn("exceeds 5 characters", payload["error"])
            finally:
                self.stop_process(process)

    def test_companion_custom_execute_hook_handles_fixed_chain_result(self) -> None:
        if not shutil.which("node"):
            self.skipTest("node is unavailable")
        with tempfile.TemporaryDirectory() as directory:
            output = self.scaffold(Path(directory), "relay")
            companion = output / "browser-companion.mjs"
            source = companion.read_text(encoding="utf-8")
            old = "async function customExecute(context) {\n  return undefined;\n}"
            new = "async function customExecute(context) {\n  return { request: { url: context.request.url, method: context.request.method }, response: { ok: true, status: 200, statusText: 'OK', url: context.request.url, headers: {}, body: { results: [{ name: 'custom-chain' }] } } };\n}"
            self.assertEqual(source.count(old), 1)
            companion.write_text(source.replace(old, new), encoding="utf-8")
            process, origin = self.start_companion(output, "--no-prepare")
            try:
                status, payload = self.execute(origin)
                self.assertEqual(status, 200)
                self.assertEqual(payload["response"]["body"]["results"][0]["name"], "custom-chain")
            finally:
                self.stop_process(process)

    def test_companion_serves_head_for_prototype_routes(self) -> None:
        if not shutil.which("node"):
            self.skipTest("node is unavailable")
        with tempfile.TemporaryDirectory() as directory:
            output = self.scaffold(Path(directory), "relay")
            process, origin = self.start_companion(output, "--no-prepare")
            try:
                for path in ("", "demo.html"):
                    request = urllib.request.Request(f"{origin}{path}", method="HEAD")
                    with urllib.request.urlopen(request, timeout=5) as response:
                        self.assertEqual(response.status, 200)
                        self.assertEqual(response.headers["Allow"], "GET, HEAD")
                        self.assertEqual(response.read(), b"")
            finally:
                self.stop_process(process)

    def test_node_transport_executes_allowlisted_workflow_stages(self) -> None:
        if not shutil.which("node"):
            self.skipTest("node is unavailable")
        with tempfile.TemporaryDirectory() as directory:
            output = self.scaffold_spec(Path(directory), self.workflow_spec("relay"))
            process, origin = self.start_companion(output, "--no-prepare")
            try:
                status, search = self.execute(origin, "chosen", request_key="search")
                self.assertEqual(status, 200)
                self.assertEqual(search["response"]["body"]["results"][0]["id"], "chosen")
                status, detail = self.execute(origin, "chosen", request_key="detail", selected_value="chosen")
                self.assertEqual(status, 200)
                self.assertEqual(detail["response"]["body"]["details"][0]["name"], "Detail chosen")
                status, error = self.execute(origin, "chosen", request_key="unknown")
                self.assertEqual(status, 502)
                self.assertIn("not allowlisted", error["error"])
            finally:
                self.stop_process(process)

    def test_interactive_profile_runtime_launches_with_safe_generated_defaults(self) -> None:
        if not shutil.which("node"):
            self.skipTest("node is unavailable")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = root / "runtime-profile"
            profile.mkdir()
            secret_marker = "cookie-material-must-not-be-copied"
            (profile / "Cookies").write_text(secret_marker, encoding="utf-8")
            spec = self.spec("browser")
            spec["companion"]["runtime"] = {
                "authMode": "interactive-profile",
                "session": "wti-auth-runtime",
                "profile": str(profile),
            }
            output = self.scaffold_spec(root, spec)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            log_path = root / "agent-args.json"
            fake_agent = fake_bin / "agent-browser"
            fake_agent.write_text(
                '''#!/usr/bin/env python3
import json, os, sys
with open(os.environ["WTI_FAKE_AGENT_ARGS"], "w", encoding="utf-8") as handle:
    json.dump(sys.argv[1:], handle)
print(json.dumps({"data": {"result": None}}))
''',
                encoding="utf-8",
            )
            fake_agent.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{fake_bin}{os.pathsep}{env.get('PATH', '')}"
            env["WTI_FAKE_AGENT_ARGS"] = str(log_path)
            process, _ = self.start_companion(output, env=env)
            try:
                arguments = json.loads(log_path.read_text(encoding="utf-8"))
                self.assertIn("--session", arguments)
                self.assertEqual(arguments[arguments.index("--session") + 1], "wti-auth-runtime")
                self.assertIn("--profile", arguments)
                self.assertEqual(arguments[arguments.index("--profile") + 1], str(profile))
                self.assertIn("--headed", arguments)
                self.assertEqual(arguments[-2:], ["open", self.target_origin])
                deliverable_text = "\n".join(
                    path.read_text(encoding="utf-8")
                    for path in output.iterdir()
                    if path.is_file()
                )
                self.assertNotIn(secret_marker, deliverable_text)
            finally:
                self.stop_process(process)

    def test_page_runtime_companion_enforces_fixed_path_stage_and_projection_bounds(self) -> None:
        if not shutil.which("node"):
            self.skipTest("node is unavailable")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = self.scaffold_spec(root, self.page_runtime_spec())
            self.install_page_runtime_recipe(output)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            fake_agent = fake_bin / "agent-browser"
            fake_agent.write_text(
                '''#!/usr/bin/env python3
import json, os, sys
args = sys.argv[1:]
if "get" in args and "url" in args:
    result = os.environ["WTI_FAKE_PAGE_URL"]
elif "eval" in args:
    result = json.loads(os.environ["WTI_FAKE_PROJECTED_JSON"])
else:
    result = None
print(json.dumps({"data": {"result": result}}))
''',
                encoding="utf-8",
            )
            fake_agent.chmod(0o755)
            base_env = os.environ.copy()
            base_env["PATH"] = f"{fake_bin}{os.pathsep}{base_env.get('PATH', '')}"
            base_env["WTI_FAKE_PAGE_URL"] = f"{self.target_origin}/runtime/catalogue"
            base_env["WTI_FAKE_PROJECTED_JSON"] = json.dumps({
                "query": "runtime", "items": [{"id": "runtime-1", "name": "Runtime one"}],
                "access_token": "must-redact",
            })
            process, origin = self.start_companion(output, "--no-prepare", env=base_env)
            try:
                status, payload = self.execute(origin, "runtime")
                self.assertEqual(status, 200, payload)
                self.assertEqual(payload["request"]["mechanismKind"], "page-runtime-extraction")
                self.assertEqual(payload["response"]["body"]["items"][0]["id"], "runtime-1")
                self.assertEqual(payload["response"]["body"]["access_token"], "[REDACTED]")
                status, error = self.execute(origin, "runtime", request_key="detail")
                self.assertEqual(status, 502)
                self.assertIn("fixed main stage", error["error"])
            finally:
                self.stop_process(process)

            wrong_path_env = {**base_env, "WTI_FAKE_PAGE_URL": f"{self.target_origin}/runtime/other?view=cards"}
            process, origin = self.start_companion(output, "--no-prepare", env=wrong_path_env)
            try:
                status, error = self.execute(origin, "runtime")
                self.assertEqual(status, 502)
                self.assertIn("configured page-runtime path", error["error"])
            finally:
                self.stop_process(process)

            wrong_query_env = {**base_env, "WTI_FAKE_PAGE_URL": f"{self.target_origin}/runtime/catalogue?view=list"}
            process, origin = self.start_companion(output, "--no-prepare", env=wrong_query_env)
            try:
                status, error = self.execute(origin, "runtime")
                self.assertEqual(status, 502)
                self.assertIn("allowed page-runtime query/fragment state", error["error"])
            finally:
                self.stop_process(process)

            oversized_env = {
                **base_env,
                "WTI_FAKE_PROJECTED_JSON": json.dumps({"items": list(range(2_001))}),
            }
            process, origin = self.start_companion(output, "--no-prepare", env=oversized_env)
            try:
                status, error = self.execute(origin, "runtime")
                self.assertEqual(status, 502)
                self.assertIn("exceeded 2000 array items", error["error"])
            finally:
                self.stop_process(process)

            migrated_root = root / "migrated"
            migrated_root.mkdir()
            migrated_spec = self.page_runtime_spec()
            migrated_spec["companion"]["targetStatePolicy"] = "allow-query-to-fragment"
            migrated_output = self.scaffold_spec(migrated_root, migrated_spec)
            self.install_page_runtime_recipe(migrated_output)
            migrated_env = {
                **base_env,
                "WTI_FAKE_PAGE_URL": f"{self.target_origin}/runtime/catalogue#view=cards",
            }
            process, origin = self.start_companion(migrated_output, "--no-prepare", env=migrated_env)
            try:
                status, payload = self.execute(origin, "runtime")
                self.assertEqual(status, 200, payload)
                self.assertEqual(payload["response"]["body"]["items"][0]["id"], "runtime-1")
            finally:
                self.stop_process(process)

    @unittest.skipUnless(os.environ.get("WTI_AGENT_BROWSER_INTEGRATION") == "1", "set WTI_AGENT_BROWSER_INTEGRATION=1")
    def test_demo_ui_runs_and_exposes_sanitized_raw_response(self) -> None:
        if not shutil.which("agent-browser"):
            self.skipTest("agent-browser is unavailable")
        session = f"wti-ui-{uuid.uuid4().hex[:10]}"
        with tempfile.TemporaryDirectory() as directory:
            output = self.scaffold(Path(directory), "relay")
            process, origin = self.start_companion(output, "--no-prepare")
            try:
                commands = [
                    ["agent-browser", "--session", session, "open", origin],
                    ["agent-browser", "--session", session, "fill", "#input-query", "many"],
                    ["agent-browser", "--session", session, "click", "#run"],
                    ["agent-browser", "--session", session, "wait", "750"],
                ]
                for command in commands:
                    result = subprocess.run(command, text=True, capture_output=True, check=False)
                    self.assertEqual(result.returncode, 0, result.stderr)
                status = subprocess.run(
                    ["agent-browser", "--session", session, "get", "text", "#status"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(status.returncode, 0, status.stderr)
                self.assertIn("Completed successfully", status.stdout)
                raw = subprocess.run(
                    ["agent-browser", "--session", session, "get", "text", "#raw"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(raw.returncode, 0, raw.stderr)
                self.assertIn("Synthetic result", raw.stdout)
                self.assertIn("[REDACTED]", raw.stdout)
                json.loads(raw.stdout)
                rendered_rows = subprocess.run(
                    ["agent-browser", "--session", session, "get", "count", "#results tbody tr"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                limit_note = subprocess.run(
                    ["agent-browser", "--session", session, "get", "text", "#results .limit-note"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(rendered_rows.returncode, 0, rendered_rows.stderr)
                self.assertEqual(rendered_rows.stdout.strip(), "50")
                self.assertIn("Showing 50 of 60", limit_note.stdout)
                mechanism = subprocess.run(
                    ["agent-browser", "--session", session, "get", "text", "#mechanism-stages"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(mechanism.returncode, 0, mechanism.stderr)
                self.assertIn("GET", mechanism.stdout)
                self.assertIn("/api/search", mechanism.stdout)
                copied = subprocess.run(
                    ["agent-browser", "--session", session, "click", "#copy"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(copied.returncode, 0, copied.stderr)
                status_after_copy = subprocess.run(
                    ["agent-browser", "--session", session, "get", "text", "#status"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                utility = subprocess.run(
                    ["agent-browser", "--session", session, "get", "text", "#utility-status"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertIn("Completed successfully", status_after_copy.stdout)
                self.assertIn("copy", utility.stdout.lower())
            finally:
                self.stop_process(process)
                subprocess.run(["agent-browser", "--session", session, "close"], capture_output=True, check=False)

    @unittest.skipUnless(os.environ.get("WTI_AGENT_BROWSER_INTEGRATION") == "1", "set WTI_AGENT_BROWSER_INTEGRATION=1")
    def test_direct_demo_runs_without_companion_on_same_origin(self) -> None:
        if not shutil.which("agent-browser"):
            self.skipTest("agent-browser is unavailable")
        session = f"wti-direct-{uuid.uuid4().hex[:10]}"
        with tempfile.TemporaryDirectory() as directory:
            output = self.scaffold_spec(Path(directory), self.direct_spec())
            SyntheticHandler.demo_file = output / "demo.html"
            try:
                commands = [
                    ["agent-browser", "--session", session, "open", f"{self.target_origin}/demo.html"],
                    ["agent-browser", "--session", session, "fill", "#input-query", "direct"],
                    ["agent-browser", "--session", session, "click", "#run"],
                    ["agent-browser", "--session", session, "wait", "750"],
                ]
                for command in commands:
                    result = subprocess.run(command, text=True, capture_output=True, check=False)
                    self.assertEqual(result.returncode, 0, result.stderr)
                status = subprocess.run(
                    ["agent-browser", "--session", session, "get", "text", "#status"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(status.returncode, 0, status.stderr)
                self.assertIn("Completed successfully", status.stdout)
                self.assertFalse((output / "browser-companion.mjs").exists())
            finally:
                SyntheticHandler.demo_file = None
                subprocess.run(["agent-browser", "--session", session, "close"], capture_output=True, check=False)

    @unittest.skipUnless(os.environ.get("WTI_AGENT_BROWSER_INTEGRATION") == "1", "set WTI_AGENT_BROWSER_INTEGRATION=1")
    def test_direct_mode_requires_cors_from_exact_prototype_origin(self) -> None:
        if not shutil.which("agent-browser"):
            self.skipTest("agent-browser is unavailable")
        session = f"wti-cors-{uuid.uuid4().hex[:10]}"
        with tempfile.TemporaryDirectory() as directory:
            output = self.scaffold_spec(Path(directory), self.direct_spec())
            PrototypeHandler.demo_file = output / "demo.html"
            try:
                SyntheticHandler.allowed_cors_origin = "https://www.justwatch.com"
                commands = [
                    ["agent-browser", "--session", session, "open", f"{self.prototype_origin}/demo.html?phase=wrong-origin"],
                    ["agent-browser", "--session", session, "fill", "#input-query", "cors"],
                    ["agent-browser", "--session", session, "click", "#run"],
                    ["agent-browser", "--session", session, "wait", "750"],
                ]
                for command in commands:
                    result = subprocess.run(command, text=True, capture_output=True, check=False)
                    self.assertEqual(result.returncode, 0, result.stderr)
                failed = subprocess.run(
                    ["agent-browser", "--session", session, "get", "text", "#status"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(failed.returncode, 0, failed.stderr)
                self.assertNotIn("Completed successfully", failed.stdout)

                SyntheticHandler.allowed_cors_origin = self.prototype_origin
                commands = [
                    ["agent-browser", "--session", session, "open", f"{self.prototype_origin}/demo.html?phase=exact-origin"],
                    ["agent-browser", "--session", session, "fill", "#input-query", "cors"],
                    ["agent-browser", "--session", session, "click", "#run"],
                    ["agent-browser", "--session", session, "wait", "750"],
                ]
                for command in commands:
                    result = subprocess.run(command, text=True, capture_output=True, check=False)
                    self.assertEqual(result.returncode, 0, result.stderr)
                succeeded = subprocess.run(
                    ["agent-browser", "--session", session, "get", "text", "#status"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(succeeded.returncode, 0, succeeded.stderr)
                self.assertIn("Completed successfully", succeeded.stdout)

                SyntheticHandler.allowed_cors_origin = "https://www.justwatch.com"
                for command in (
                    ["agent-browser", "--session", session, "click", "#run"],
                    ["agent-browser", "--session", session, "wait", "750"],
                ):
                    result = subprocess.run(command, text=True, capture_output=True, check=False)
                    self.assertEqual(result.returncode, 0, result.stderr)
                failed_again = subprocess.run(
                    ["agent-browser", "--session", session, "get", "text", "#status"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                raw_after_failure = subprocess.run(
                    ["agent-browser", "--session", session, "get", "text", "#raw"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertNotIn("Completed successfully", failed_again.stdout)
                self.assertIn('"responseReceived": false', raw_after_failure.stdout)
                self.assertNotIn("Synthetic result", raw_after_failure.stdout)
            finally:
                SyntheticHandler.allowed_cors_origin = None
                PrototypeHandler.demo_file = None
                subprocess.run(["agent-browser", "--session", session, "close"], capture_output=True, check=False)

    @unittest.skipUnless(os.environ.get("WTI_AGENT_BROWSER_INTEGRATION") == "1", "set WTI_AGENT_BROWSER_INTEGRATION=1")
    def test_direct_demo_handles_status_text_and_malformed_responses(self) -> None:
        if not shutil.which("agent-browser"):
            self.skipTest("agent-browser is unavailable")
        session = f"wti-responses-{uuid.uuid4().hex[:10]}"
        cases = [
            ("status-json", 503, "synthetic unavailable"),
            ("status-text", 500, "synthetic failure"),
            ("plain", None, "synthetic plain response"),
            ("malformed", None, '\\"broken\\":'),
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            SyntheticHandler.allowed_cors_origin = self.prototype_origin
            try:
                for name, error_status, raw_fragment in cases:
                    case_directory = root / name
                    case_directory.mkdir()
                    spec = self.direct_spec()
                    spec["request"]["url"] = f"{self.target_origin}/api/{name}"
                    spec["renderer"] = {"type": "auto"}
                    output = self.scaffold_spec(case_directory, spec)
                    PrototypeHandler.demo_file = output / "demo.html"
                    commands = [
                        ["agent-browser", "--session", session, "open", f"{self.prototype_origin}/demo.html?case={name}"],
                        ["agent-browser", "--session", session, "fill", "#input-query", name],
                        ["agent-browser", "--session", session, "click", "#run"],
                        ["agent-browser", "--session", session, "wait", "500"],
                    ]
                    for command in commands:
                        result = subprocess.run(command, text=True, capture_output=True, check=False)
                        self.assertEqual(result.returncode, 0, result.stderr)
                    status = subprocess.run(
                        ["agent-browser", "--session", session, "get", "text", "#status"],
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(status.returncode, 0, status.stderr)
                    if error_status is None:
                        self.assertIn("Completed successfully", status.stdout)
                    else:
                        self.assertIn(f"HTTP {error_status}", status.stdout)
                    raw = subprocess.run(
                        ["agent-browser", "--session", session, "get", "text", "#raw"],
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(raw.returncode, 0, raw.stderr)
                    self.assertIn(raw_fragment, raw.stdout)
            finally:
                SyntheticHandler.allowed_cors_origin = None
                PrototypeHandler.demo_file = None
                subprocess.run(["agent-browser", "--session", session, "close"], capture_output=True, check=False)

    @unittest.skipUnless(os.environ.get("WTI_AGENT_BROWSER_INTEGRATION") == "1", "set WTI_AGENT_BROWSER_INTEGRATION=1")
    def test_direct_demo_rejects_http_success_without_domain_shape(self) -> None:
        if not shutil.which("agent-browser"):
            self.skipTest("agent-browser is unavailable")
        session = f"wti-domain-shape-{uuid.uuid4().hex[:10]}"
        with tempfile.TemporaryDirectory() as directory:
            spec = self.direct_spec()
            spec["request"]["url"] = f"{self.target_origin}/api/plain"
            spec["renderer"] = {"type": "table", "itemsPath": "results"}
            output = self.scaffold_spec(Path(directory), spec)
            SyntheticHandler.allowed_cors_origin = self.target_origin
            SyntheticHandler.demo_file = output / "demo.html"
            try:
                commands = [
                    ["agent-browser", "--session", session, "open", f"{self.target_origin}/demo.html"],
                    ["agent-browser", "--session", session, "fill", "#input-query", "shape"],
                    ["agent-browser", "--session", session, "click", "#run"],
                    ["agent-browser", "--session", session, "wait", "500"],
                ]
                for command in commands:
                    result = subprocess.run(command, text=True, capture_output=True, check=False)
                    self.assertEqual(result.returncode, 0, result.stderr)
                status = subprocess.run(
                    ["agent-browser", "--session", session, "get", "text", "#status"],
                    text=True, capture_output=True, check=False,
                )
                self.assertEqual(status.returncode, 0, status.stderr)
                self.assertIn("did not contain structured domain data", status.stdout)
            finally:
                SyntheticHandler.allowed_cors_origin = None
                SyntheticHandler.demo_file = None
                subprocess.run(["agent-browser", "--session", session, "close"], capture_output=True, check=False)

    @unittest.skipUnless(os.environ.get("WTI_AGENT_BROWSER_INTEGRATION") == "1", "set WTI_AGENT_BROWSER_INTEGRATION=1")
    def test_response_hook_normalizes_html_without_losing_provenance(self) -> None:
        if not shutil.which("agent-browser"):
            self.skipTest("agent-browser is unavailable")
        session = f"wti-normalize-{uuid.uuid4().hex[:10]}"
        with tempfile.TemporaryDirectory() as directory:
            spec = self.direct_spec()
            spec["request"]["url"] = f"{self.target_origin}/api/plain"
            spec["renderer"] = {"type": "table", "itemsPath": "results"}
            output = self.scaffold_spec(Path(directory), spec)
            demo = output / "demo.html"
            source = demo.read_text(encoding="utf-8")
            old = "function customizeResponse(payload, context) {\n      return payload;\n    }"
            new = "function customizeResponse(payload, context) {\n      payload.normalizedBody = { results: [{ name: 'normalized-domain-record' }] };\n      return payload;\n    }"
            self.assertEqual(source.count(old), 1)
            demo.write_text(source.replace(old, new), encoding="utf-8")
            SyntheticHandler.demo_file = demo
            try:
                for command in (["open", f"{self.target_origin}/demo.html"], ["fill", "#input-query", "normalize"], ["click", "#run"], ["wait", "500"]):
                    result = subprocess.run(["agent-browser", "--session", session, *command], text=True, capture_output=True, check=False)
                    self.assertEqual(result.returncode, 0, result.stderr)
                status = subprocess.run(["agent-browser", "--session", session, "get", "text", "#status"], text=True, capture_output=True, check=False)
                raw = subprocess.run(["agent-browser", "--session", session, "get", "text", "#raw"], text=True, capture_output=True, check=False)
                self.assertIn("Completed successfully", status.stdout)
                self.assertIn("normalized-domain-record", raw.stdout)
                self.assertIn("synthetic plain response", raw.stdout)
            finally:
                SyntheticHandler.demo_file = None
                subprocess.run(["agent-browser", "--session", session, "close"], capture_output=True, check=False)

    @unittest.skipUnless(os.environ.get("WTI_AGENT_BROWSER_INTEGRATION") == "1", "set WTI_AGENT_BROWSER_INTEGRATION=1")
    def test_custom_workflow_hook_preserves_acknowledgement_and_stage_raw_view(self) -> None:
        if not shutil.which("agent-browser"):
            self.skipTest("agent-browser is unavailable")
        session = f"wti-workflow-hook-{uuid.uuid4().hex[:10]}"
        with tempfile.TemporaryDirectory() as directory:
            spec = self.direct_spec()
            spec["sideEffect"] = True
            output = self.scaffold_spec(Path(directory), spec)
            demo = output / "demo.html"
            source = demo.read_text(encoding="utf-8")
            old = "async function customWorkflow(context) {\n      return null;\n    }"
            new = "async function customWorkflow(context) {\n      return { handled: true, raw: { stages: ['mutate', 'verify', 'cleanup', 'verify-clean'] }, body: { results: [{ name: 'restored' }] }, message: 'Cleanup verified.', kind: 'success' };\n    }"
            self.assertEqual(source.count(old), 1)
            demo.write_text(source.replace(old, new), encoding="utf-8")
            SyntheticHandler.demo_file = demo
            try:
                for command in (["open", f"{self.target_origin}/demo.html"], ["fill", "#input-query", "round-trip"], ["click", "#ack"], ["click", "#run"], ["wait", "250"]):
                    result = subprocess.run(["agent-browser", "--session", session, *command], text=True, capture_output=True, check=False)
                    self.assertEqual(result.returncode, 0, result.stderr)
                status = subprocess.run(["agent-browser", "--session", session, "get", "text", "#status"], text=True, capture_output=True, check=False)
                raw = subprocess.run(["agent-browser", "--session", session, "get", "text", "#raw"], text=True, capture_output=True, check=False)
                self.assertIn("Cleanup verified", status.stdout)
                self.assertIn("verify-clean", raw.stdout)
                acknowledged = subprocess.run(
                    ["agent-browser", "--session", session, "is", "checked", "#ack"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                run_enabled = subprocess.run(
                    ["agent-browser", "--session", session, "is", "enabled", "#run"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(acknowledged.returncode, 0, acknowledged.stderr)
                self.assertEqual(run_enabled.returncode, 0, run_enabled.stderr)
                self.assertEqual(acknowledged.stdout.strip(), "false")
                self.assertEqual(run_enabled.stdout.strip(), "false")
            finally:
                SyntheticHandler.demo_file = None
                subprocess.run(["agent-browser", "--session", session, "close"], capture_output=True, check=False)

    @unittest.skipUnless(os.environ.get("WTI_AGENT_BROWSER_INTEGRATION") == "1", "set WTI_AGENT_BROWSER_INTEGRATION=1")
    def test_demo_surfaces_oversized_companion_response(self) -> None:
        if not shutil.which("node"):
            self.skipTest("node is unavailable")
        if not shutil.which("agent-browser"):
            self.skipTest("agent-browser is unavailable")
        session = f"wti-large-{uuid.uuid4().hex[:10]}"
        with tempfile.TemporaryDirectory() as directory:
            spec = self.spec("relay")
            spec["request"]["url"] = f"{self.target_origin}/api/large"
            output = self.scaffold_spec(Path(directory), spec)
            process, origin = self.start_companion(output, "--no-prepare")
            try:
                commands = [
                    ["agent-browser", "--session", session, "open", origin],
                    ["agent-browser", "--session", session, "fill", "#input-query", "large"],
                    ["agent-browser", "--session", session, "click", "#run"],
                    ["agent-browser", "--session", session, "wait", "1000"],
                ]
                for command in commands:
                    result = subprocess.run(command, text=True, capture_output=True, check=False)
                    self.assertEqual(result.returncode, 0, result.stderr)
                status = subprocess.run(
                    ["agent-browser", "--session", session, "get", "text", "#status"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(status.returncode, 0, status.stderr)
                self.assertIn("Response exceeded 5000000 bytes", status.stdout)
            finally:
                self.stop_process(process)
                subprocess.run(["agent-browser", "--session", session, "close"], capture_output=True, check=False)

    @unittest.skipUnless(os.environ.get("WTI_AGENT_BROWSER_INTEGRATION") == "1", "set WTI_AGENT_BROWSER_INTEGRATION=1")
    def test_search_select_detail_demo_preserves_shared_selected_object(self) -> None:
        if not shutil.which("agent-browser"):
            self.skipTest("agent-browser is unavailable")
        session = f"wti-workflow-{uuid.uuid4().hex[:10]}"
        with tempfile.TemporaryDirectory() as directory:
            output = self.scaffold_spec(Path(directory), self.workflow_spec("direct"))
            SyntheticHandler.demo_file = output / "demo.html"
            try:
                commands = [
                    ["agent-browser", "--session", session, "open", f"{self.target_origin}/demo.html"],
                    ["agent-browser", "--session", session, "fill", "#input-query", "chosen"],
                    ["agent-browser", "--session", session, "click", "#run"],
                    ["agent-browser", "--session", session, "click", "text=Load details"],
                    ["agent-browser", "--session", session, "wait", "500"],
                ]
                for command in commands:
                    result = subprocess.run(command, text=True, capture_output=True, check=False)
                    self.assertEqual(result.returncode, 0, result.stderr)
                raw = subprocess.run(
                    ["agent-browser", "--session", session, "get", "text", "#raw"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(raw.returncode, 0, raw.stderr)
                self.assertIn("Detail chosen", raw.stdout)
                self.assertNotIn('"selected": "[CIRCULAR]"', raw.stdout)
            finally:
                SyntheticHandler.demo_file = None
                subprocess.run(["agent-browser", "--session", session, "close"], capture_output=True, check=False)

    @unittest.skipUnless(os.environ.get("WTI_AGENT_BROWSER_INTEGRATION") == "1", "set WTI_AGENT_BROWSER_INTEGRATION=1")
    def test_browser_transport_executes_inside_target_origin(self) -> None:
        if not shutil.which("agent-browser"):
            self.skipTest("agent-browser is unavailable")
        session = f"wti-test-{uuid.uuid4().hex[:10]}"
        with tempfile.TemporaryDirectory() as directory:
            output = self.scaffold(Path(directory), "browser")
            process, origin = self.start_companion(output, "--session", session)
            try:
                status, payload = self.execute(origin, "browser result")
                self.assertEqual(status, 200, payload)
                self.assertEqual(payload["response"]["body"]["results"][0]["name"], "browser result")
            finally:
                self.stop_process(process)
                subprocess.run(["agent-browser", "--session", session, "close"], capture_output=True, check=False)

    @unittest.skipUnless(os.environ.get("WTI_AGENT_BROWSER_INTEGRATION") == "1", "set WTI_AGENT_BROWSER_INTEGRATION=1")
    def test_page_runtime_projects_client_computed_dom_with_real_browser(self) -> None:
        if not shutil.which("agent-browser"):
            self.skipTest("agent-browser is unavailable")
        session = f"wti-runtime-{uuid.uuid4().hex[:10]}"
        with tempfile.TemporaryDirectory() as directory:
            output = self.scaffold_spec(Path(directory), self.page_runtime_spec())
            self.install_page_runtime_recipe(output)
            process, origin = self.start_companion(output, "--session", session)
            try:
                status, payload = self.execute(origin, "one")
                self.assertEqual(status, 200, payload)
                self.assertEqual(payload["response"]["body"]["query"], "one")
                self.assertEqual(payload["response"]["body"]["items"], [{"id": "runtime-1", "name": "Runtime one"}])
            finally:
                self.stop_process(process)
                subprocess.run(["agent-browser", "--session", session, "close"], capture_output=True, check=False)


if __name__ == "__main__":
    unittest.main()
