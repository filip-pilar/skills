#!/usr/bin/env node
import { createServer } from "node:http";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { randomBytes } from "node:crypto";
import { spawn } from "node:child_process";

const CONFIG = __WTI_COMPANION_CONFIG__;
const DIRECTORY = dirname(fileURLToPath(import.meta.url));
const MAX_REQUEST_BYTES = 1_000_000;
const MAX_RESPONSE_BYTES = 5_000_000;
const MAX_PROJECTED_BYTES = 1_000_000;
const MAX_PROJECTED_NODES = 20_000;
const MAX_PROJECTED_DEPTH = 20;
const MAX_PROJECTED_ARRAY_ITEMS = 2_000;
const MAX_PROJECTED_OBJECT_KEYS = 200;
const SECRET_KEY = /(?:authorization|cookie|password|passwd|secret|credential|session|private.?key|access.?token|refresh.?token|api.?key)/i;
const RUNTIME = CONFIG.runtime || {
  authMode: "none", session: "wti-demo", profile: "", cdp: "", prepare: true, runtimeHeadersStdin: false
};

function usage() {
  console.log(`Usage: node browser-companion.mjs [options]\n\nConfigured authentication posture: ${RUNTIME.authMode}\n\nOptions:\n  --port <number>                 Loopback port; 0 chooses an available port (configured default: ${CONFIG.localPort})\n  --session <name>                agent-browser session name\n  --profile <path>                Dedicated agent-browser profile for interactive login\n  --cdp <port-or-url>             Connect agent-browser to an approved CDP endpoint\n  --no-prepare                    Do not open the configured target page\n  --runtime-headers-stdin         Read a JSON header object from stdin into memory\n  --help                          Show this help\n`);
}

function parseArguments(argv) {
  const options = {
    port: CONFIG.localPort,
    session: RUNTIME.session || "wti-demo",
    profile: RUNTIME.profile || undefined,
    cdp: RUNTIME.cdp || undefined,
    prepare: RUNTIME.prepare !== false,
    runtimeHeadersStdin: Boolean(RUNTIME.runtimeHeadersStdin)
  };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--help") options.help = true;
    else if (argument === "--no-prepare") options.prepare = false;
    else if (argument === "--runtime-headers-stdin") options.runtimeHeadersStdin = true;
    else if (["--port", "--session", "--profile", "--cdp"].includes(argument)) {
      const value = argv[index + 1];
      if (!value) throw new Error(`${argument} requires a value.`);
      index += 1;
      if (argument === "--port") options.port = Number(value);
      else options[argument.slice(2)] = value;
    } else throw new Error(`Unknown option: ${argument}`);
  }
  if (!Number.isInteger(options.port) || options.port < 0 || options.port > 65535) throw new Error("--port must be an integer from 0 to 65535.");
  if (!/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$/.test(options.session)) throw new Error("--session must contain only letters, numbers, underscores, and hyphens.");
  if (options.profile && options.cdp) throw new Error("--profile and --cdp cannot be used together.");
  return options;
}

function authenticationGuidance(session) {
  if (RUNTIME.authMode === "interactive-profile") {
    return `Authentication uses a dedicated headed profile in session ${session}. Sign in interactively if prompted; never copy cookies, storage, credentials, or profile contents into this proof.`;
  }
  if (RUNTIME.authMode === "existing-session") {
    return `Authentication reuses the named agent-browser session ${session}. Sign in interactively in that session if needed; never import browser secrets into this proof.`;
  }
  if (RUNTIME.authMode === "cdp") {
    return "Authentication stays in the explicitly approved CDP browser. Do not inspect or copy its cookies, storage, credentials, or profile files.";
  }
  if (RUNTIME.authMode === "runtime-headers") {
    return "Authentication headers are accepted from stdin for this process only and must never be echoed, logged, or written into the deliverable.";
  }
  return "No authentication material is configured or embedded in this proof.";
}

function runAgentBrowser(args, timeoutMs = 60_000) {
  return new Promise((resolve, reject) => {
    const child = spawn("agent-browser", args, { stdio: ["ignore", "pipe", "pipe"], shell: false });
    let stdout = "";
    let stderr = "";
    const timer = setTimeout(() => {
      child.kill("SIGTERM");
      reject(new Error("agent-browser timed out."));
    }, timeoutMs);
    child.stdout.on("data", (chunk) => { stdout += chunk; });
    child.stderr.on("data", (chunk) => { stderr += chunk; });
    child.on("error", (error) => {
      clearTimeout(timer);
      reject(error.code === "ENOENT" ? new Error("agent-browser is not installed or is not on PATH.") : error);
    });
    child.on("close", (code) => {
      clearTimeout(timer);
      if (code === 0) resolve(stdout.trim());
      else {
        const diagnostic = args.includes("eval") ? "evaluation failed; runtime details were suppressed" : stderr.trim() || "no diagnostic output";
        reject(new Error(`agent-browser failed (${code}): ${diagnostic}`));
      }
    });
  });
}

function unwrapAgentJson(text) {
  const parsed = JSON.parse(text);
  if (parsed && typeof parsed === "object" && "data" in parsed) {
    if (parsed.data && typeof parsed.data === "object" && "result" in parsed.data) return parsed.data.result;
    return parsed.data;
  }
  if (parsed && typeof parsed === "object" && "result" in parsed) return parsed.result;
  return parsed;
}

function interpolate(value, inputs) {
  if (Array.isArray(value)) return value.map((item) => interpolate(item, inputs));
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, interpolate(item, inputs)]));
  }
  if (typeof value !== "string") return value;
  const exact = value.match(/^\{\{([a-zA-Z][a-zA-Z0-9_-]*)\}\}$/);
  if (exact) return inputs[exact[1]];
  return value.replace(/\{\{([a-zA-Z][a-zA-Z0-9_-]*)\}\}/g, (_, name) => String(inputs[name] ?? ""));
}

function validateInputs(inputs) {
  if (!inputs || typeof inputs !== "object" || Array.isArray(inputs)) throw new Error("Request must contain an inputs object.");
  const definitions = new Map(CONFIG.inputDefinitions.map((definition) => [definition.name, definition]));
  const runtimeNames = new Set(CONFIG.runtimeInputNames || []);
  if (Object.keys(inputs).some((name) => !definitions.has(name) && !runtimeNames.has(name))) throw new Error("Request contains an unknown input.");
  for (const definition of CONFIG.inputDefinitions) {
    const value = inputs[definition.name];
    const missing = value === undefined || value === null || value === "";
    if (definition.required && missing) throw new Error(`Input ${definition.name} is required.`);
    if (missing) continue;
    if (definition.type === "checkbox") {
      if (typeof value !== "boolean") throw new Error(`Input ${definition.name} must be a boolean.`);
      continue;
    }
    if (definition.type === "number") {
      if (typeof value !== "number" || !Number.isFinite(value)) throw new Error(`Input ${definition.name} must be a finite number.`);
      if (definition.min !== undefined && value < definition.min) throw new Error(`Input ${definition.name} is below its allowed minimum.`);
      if (definition.max !== undefined && value > definition.max) throw new Error(`Input ${definition.name} exceeds its allowed maximum.`);
      continue;
    }
    if (typeof value !== "string") throw new Error(`Input ${definition.name} must be text.`);
    const maximum = definition.maxLength ?? 10_000;
    if (value.length > maximum) throw new Error(`Input ${definition.name} exceeds ${maximum} characters.`);
    if (definition.minLength !== undefined && value.length < definition.minLength) throw new Error(`Input ${definition.name} is shorter than allowed.`);
    if (definition.type === "select" && !definition.options.some((option) => option.value === value)) throw new Error(`Input ${definition.name} is not an allowed option.`);
    if (definition.type === "url") {
      let parsed;
      try { parsed = new URL(value); } catch { throw new Error(`Input ${definition.name} must be a valid URL.`); }
      if (!["http:", "https:"].includes(parsed.protocol)) throw new Error(`Input ${definition.name} must use http or https.`);
    }
    if (definition.pattern && !(new RegExp(definition.pattern)).test(value)) throw new Error(`Input ${definition.name} does not match the allowed format.`);
  }
  for (const name of runtimeNames) {
    if (!(name in inputs)) continue;
    const value = inputs[name];
    if (!["string", "number", "boolean"].includes(typeof value) || (typeof value === "string" && value.length > 10_000)) {
      throw new Error(`Runtime input ${name} has an invalid value.`);
    }
  }
  return inputs;
}

function requestFromInputs(inputs, runtimeHeaders, requestKey = "main") {
  const definitions = CONFIG.requests || { main: CONFIG.request, search: CONFIG.request };
  const definition = definitions[requestKey];
  if (!definition) throw new Error("Request stage is not allowlisted.");
  const request = interpolate(definition, inputs);
  const url = new URL(request.url);
  if (!CONFIG.allowedEndpointOrigins.includes(url.origin)) throw new Error("The generated endpoint is not allowlisted.");
  for (const [name, value] of Object.entries(request.query || {})) {
    if (value !== undefined && value !== null && value !== "") url.searchParams.set(name, String(value));
  }
  const headers = { ...(request.headers || {}), ...runtimeHeaders };
  let body;
  if (request.body !== undefined) {
    body = typeof request.body === "string" ? request.body : JSON.stringify(request.body);
    if (!Object.keys(headers).some((name) => name.toLowerCase() === "content-type")) headers["Content-Type"] = "application/json";
  }
  return { url: url.href, method: request.method, headers, body, credentials: request.credentials || "include" };
}

async function readBoundedResponse(response) {
  const chunks = [];
  let bytes = 0;
  if (response.body) {
    for await (const chunk of response.body) {
      bytes += chunk.length;
      if (bytes > MAX_RESPONSE_BYTES) throw new Error(`Response exceeded ${MAX_RESPONSE_BYTES} bytes.`);
      chunks.push(chunk);
    }
  }
  const text = Buffer.concat(chunks).toString("utf8");
  let body = text;
  try { body = text === "" ? null : JSON.parse(text); } catch {}
  return { body, headers: Object.fromEntries(response.headers.entries()) };
}

async function executeNode(request) {
  const response = await fetch(request.url, {
    method: request.method,
    headers: request.headers,
    body: request.body,
    redirect: "manual"
  });
  const { body, headers } = await readBoundedResponse(response);
  if (response.status >= 300 && response.status < 400) {
    const location = response.headers.get("location");
    if (location && !CONFIG.allowedEndpointOrigins.includes(new URL(location, request.url).origin)) {
      throw new Error("The endpoint redirected to an origin that is not allowlisted.");
    }
  }
  return {
    request: { url: request.url, method: request.method },
    response: { ok: response.ok, status: response.status, statusText: response.statusText, url: response.url, headers, body }
  };
}

async function activeBrowserUrl(session) {
  const output = await runAgentBrowser(["--session", session, "--json", "get", "url"]);
  const value = unwrapAgentJson(output);
  if (typeof value === "string") return value;
  if (value && typeof value === "object") return value.url || value.value || value.result;
  throw new Error("Could not determine the active agent-browser tab URL.");
}

async function assertActiveBrowserPage(session, requireExactPath = false) {
  const pageUrl = new URL(await activeBrowserUrl(session));
  if (!CONFIG.allowedPageOrigins.includes(pageUrl.origin)) {
    throw new Error(`The active agent-browser tab is on ${pageUrl.origin}, not an allowlisted target origin. Open the configured target page in session ${session}. ${authenticationGuidance(session)}`);
  }
  if (requireExactPath && pageUrl.pathname !== CONFIG.targetPath) {
    throw new Error(`The active agent-browser tab is on path ${pageUrl.pathname}, not the configured page-runtime path ${CONFIG.targetPath}. Open the configured target page in session ${session}. ${authenticationGuidance(session)}`);
  }
  if (requireExactPath) {
    const activeSearchParams = [...pageUrl.searchParams.entries()];
    const activeFragmentRaw = pageUrl.hash.slice(1);
    let activeFragment;
    try { activeFragment = decodeURIComponent(activeFragmentRaw); }
    catch { throw new Error("The active page fragment is malformed."); }
    const targetSearchParams = CONFIG.targetSearchParams || [];
    const targetFragment = CONFIG.targetFragment || "";
    const exactState = JSON.stringify(activeSearchParams) === JSON.stringify(targetSearchParams)
      && activeFragment === targetFragment;
    const consumedState = CONFIG.targetStatePolicy === "allow-consumed"
      && (targetSearchParams.length > 0 || targetFragment !== "")
      && activeSearchParams.length === 0
      && activeFragment === "";
    const migratedState = CONFIG.targetStatePolicy === "allow-query-to-fragment"
      && targetSearchParams.length > 0
      && targetFragment === ""
      && activeSearchParams.length === 0
      && JSON.stringify([...new URLSearchParams(activeFragmentRaw).entries()]) === JSON.stringify(targetSearchParams);
    if (!exactState && !consumedState && !migratedState) {
      throw new Error(`The active agent-browser tab does not match an allowed page-runtime query/fragment state. Open the generated target in session ${session}.`);
    }
  }
  return { origin: pageUrl.origin, pathname: pageUrl.pathname };
}

async function executeBrowser(request, session) {
  await assertActiveBrowserPage(session);
  const payload = Buffer.from(JSON.stringify(request), "utf8").toString("base64");
  const expression = `(async () => {
    const bytes = Uint8Array.from(atob(${JSON.stringify(payload)}), character => character.charCodeAt(0));
    const request = JSON.parse(new TextDecoder().decode(bytes));
    const response = await fetch(request.url, {
      method: request.method,
      headers: request.headers,
      body: request.body,
      credentials: request.credentials,
      redirect: "manual"
    });
    const text = await response.text();
    let body = text;
    try { body = text === "" ? null : JSON.parse(text); } catch {}
    return {
      request: { url: request.url, method: request.method },
      response: {
        ok: response.ok,
        status: response.status,
        statusText: response.statusText,
        url: response.url,
        headers: Object.fromEntries(response.headers.entries()),
        body
      }
    };
  })()`;
  const output = await runAgentBrowser(["--session", session, "--json", "eval", expression], 120_000);
  const result = unwrapAgentJson(output);
  if (typeof result === "string") {
    try { return JSON.parse(result); } catch {}
  }
  return result;
}

function validateProjectedJson(value, budget = { nodes: 0 }, depth = 0) {
  budget.nodes += 1;
  if (budget.nodes > MAX_PROJECTED_NODES) throw new Error(`Page projection exceeded ${MAX_PROJECTED_NODES} JSON nodes.`);
  if (depth > MAX_PROJECTED_DEPTH) throw new Error(`Page projection exceeded JSON depth ${MAX_PROJECTED_DEPTH}.`);
  if (value === null || typeof value === "string" || typeof value === "boolean") return value;
  if (typeof value === "number") {
    if (!Number.isFinite(value)) throw new Error("Page projection returned a non-finite number.");
    return value;
  }
  if (Array.isArray(value)) {
    if (value.length > MAX_PROJECTED_ARRAY_ITEMS) throw new Error(`Page projection exceeded ${MAX_PROJECTED_ARRAY_ITEMS} array items.`);
    for (const item of value) validateProjectedJson(item, budget, depth + 1);
    return value;
  }
  if (!value || typeof value !== "object") throw new Error("Page projection must return JSON-compatible data only.");
  const entries = Object.entries(value);
  if (entries.length > MAX_PROJECTED_OBJECT_KEYS) throw new Error(`Page projection exceeded ${MAX_PROJECTED_OBJECT_KEYS} keys in one object.`);
  for (const [, item] of entries) validateProjectedJson(item, budget, depth + 1);
  return value;
}

function boundedProjectedJson(value) {
  validateProjectedJson(value);
  let serialized;
  try { serialized = JSON.stringify(value); }
  catch { throw new Error("Page projection must return serializable JSON data."); }
  if (serialized === undefined) throw new Error("Page projection returned no JSON value.");
  if (Buffer.byteLength(serialized) > MAX_PROJECTED_BYTES) throw new Error(`Page projection exceeded ${MAX_PROJECTED_BYTES} bytes.`);
  return value;
}

async function evaluateFixedPageProjection(session, recipe, inputs) {
  if (typeof recipe !== "function") throw new Error("The generated page projection recipe is invalid.");
  const payload = Buffer.from(JSON.stringify(inputs), "utf8").toString("base64");
  const expression = `(async () => {
    const bytes = Uint8Array.from(atob(${JSON.stringify(payload)}), character => character.charCodeAt(0));
    const inputs = JSON.parse(new TextDecoder().decode(bytes));
    return await (${recipe.toString()})(inputs);
  })()`;
  const output = await runAgentBrowser(["--session", session, "--json", "eval", expression], 120_000);
  let projected = unwrapAgentJson(output);
  if (typeof projected === "string") {
    try { projected = JSON.parse(projected); } catch {}
  }
  return boundedProjectedJson(projected);
}

function assertAllowlistedRequest(request) {
  const parsed = new URL(request.url);
  if (!CONFIG.allowedEndpointOrigins.includes(parsed.origin)) throw new Error("The custom request origin is not allowlisted.");
  return request;
}

// WTI-CUSTOMIZE: companion:start
async function customExecute(context) {
  return undefined;
}

function customizeCompanionResult(result, context) {
  return result;
}
// WTI-CUSTOMIZE: companion:end

// WTI-CUSTOMIZE: page-runtime:start
async function projectPageRuntime({ inputs, evaluate }) {
  throw new Error("WTI_PAGE_RUNTIME_RECIPE_REQUIRED: replace this fixed generated recipe with a narrowly projected JSON extraction.");
}
// WTI-CUSTOMIZE: page-runtime:end

async function executePageRuntime(inputs, session) {
  const activePage = await assertActiveBrowserPage(session, true);
  const projected = await projectPageRuntime({
    inputs: Object.freeze({ ...inputs }),
    evaluate: (recipe) => evaluateFixedPageProjection(session, recipe, inputs)
  });
  boundedProjectedJson(projected);
  return {
    request: {
      mechanismKind: "page-runtime-extraction",
      target: activePage
    },
    response: {
      ok: true,
      status: 200,
      statusText: "Projected",
      url: `${activePage.origin}${activePage.pathname}`,
      headers: { "content-type": "application/json" },
      body: projected
    }
  };
}

function sanitize(value, key = "", seen = new WeakSet(), depth = 0) {
  if (SECRET_KEY.test(key)) return "[REDACTED]";
  if (value === null || typeof value !== "object") return value;
  if (seen.has(value)) return "[CIRCULAR]";
  if (depth > 20) return "[MAX DEPTH]";
  seen.add(value);
  try {
    if (Array.isArray(value)) return value.slice(0, 5_000).map((item) => sanitize(item, "", seen, depth + 1));
    return Object.fromEntries(Object.entries(value).slice(0, 5_000).map(([childKey, childValue]) => [childKey, sanitize(childValue, childKey, seen, depth + 1)]));
  } finally {
    seen.delete(value);
  }
}

function sendJson(response, status, value) {
  const body = JSON.stringify(sanitize(value));
  response.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(body),
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff"
  });
  response.end(body);
}

function readJsonRequest(request) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let bytes = 0;
    let tooLarge = false;
    request.on("data", (chunk) => {
      bytes += chunk.length;
      if (bytes > MAX_REQUEST_BYTES) {
        tooLarge = true;
        return;
      }
      if (!tooLarge) chunks.push(chunk);
    });
    request.on("end", () => {
      if (tooLarge) {
        reject(new Error(`Request exceeded ${MAX_REQUEST_BYTES} bytes.`));
        return;
      }
      try { resolve(JSON.parse(Buffer.concat(chunks).toString("utf8"))); }
      catch { reject(new Error("Request body must be valid JSON.")); }
    });
    request.on("error", reject);
  });
}

async function main() {
  const options = parseArguments(process.argv.slice(2));
  if (options.help) { usage(); return; }
  console.log(authenticationGuidance(options.session));
  let runtimeHeaders = {};
  if (options.runtimeHeadersStdin) {
    runtimeHeaders = JSON.parse(readFileSync(0, "utf8"));
    if (!runtimeHeaders || typeof runtimeHeaders !== "object" || Array.isArray(runtimeHeaders)) throw new Error("Runtime headers must be a JSON object.");
  }

  if (CONFIG.transport === "browser" && options.prepare) {
    const launchArgs = ["--session", options.session, "--json"];
    if (options.profile) launchArgs.push("--profile", options.profile, "--headed");
    if (options.cdp) launchArgs.push("--cdp", options.cdp);
    launchArgs.push("open", CONFIG.targetUrl);
    try {
      await runAgentBrowser(launchArgs, 120_000);
    } catch (error) {
      const reason = error instanceof Error ? error.message : String(error);
      throw new Error(`${reason} Open the configured target manually in session ${options.session}, then restart this companion with --no-prepare.`);
    }
  }

  const token = randomBytes(24).toString("base64url");
  let busy = false;
  const server = createServer(async (request, response) => {
    const address = server.address();
    const port = typeof address === "object" && address ? address.port : options.port;
    const allowedHosts = new Set([`127.0.0.1:${port}`, `localhost:${port}`, `[::1]:${port}`]);
    if (!allowedHosts.has(request.headers.host || "")) { sendJson(response, 403, { error: "Host is not allowed." }); return; }
    const localOrigin = `http://${request.headers.host}`;
    const url = new URL(request.url, localOrigin);

    if (["GET", "HEAD"].includes(request.method) && (url.pathname === "/" || url.pathname === "/demo.html")) {
      const body = readFileSync(join(DIRECTORY, "demo.html"));
      response.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Content-Length": body.length, "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", "Allow": "GET, HEAD" });
      response.end(request.method === "HEAD" ? undefined : body);
      return;
    }
    if (request.method === "GET" && url.pathname === "/__wti/config") { sendJson(response, 200, { token }); return; }
    if (request.method !== "POST" || url.pathname !== "/__wti/execute") { sendJson(response, 404, { error: "Not found." }); return; }
    if (request.headers.origin !== localOrigin) { sendJson(response, 403, { error: "Origin is not allowed." }); return; }
    if (request.headers["x-wti-token"] !== token) { sendJson(response, 403, { error: "Request token is invalid." }); return; }
    if (busy) { sendJson(response, 409, { error: "An operation is already running." }); return; }

    busy = true;
    try {
      const payload = await readJsonRequest(request);
      validateInputs(payload?.inputs);
      const requestKey = payload.requestKey || "main";
      if (typeof requestKey !== "string") throw new Error("Request stage must be a string.");
      let context;
      let executed;
      if (CONFIG.mechanismKind === "page-runtime-extraction") {
        if (requestKey !== "main") throw new Error("Page-runtime extraction supports only the fixed main stage.");
        context = { inputs: payload.inputs, requestKey, request: undefined };
        executed = await executePageRuntime(payload.inputs, options.session);
      } else {
        const built = requestFromInputs(payload.inputs, runtimeHeaders, requestKey);
        context = {
          inputs: payload.inputs,
          requestKey,
          request: built,
          executeNode: (candidate) => executeNode(assertAllowlistedRequest(candidate)),
          executeBrowser: (candidate) => executeBrowser(assertAllowlistedRequest(candidate), options.session)
        };
        const customResult = await customExecute(context);
        executed = customResult === undefined
          ? (CONFIG.transport === "browser" ? await executeBrowser(built, options.session) : await executeNode(built))
          : customResult;
      }
      const result = await customizeCompanionResult(executed, context);
      sendJson(response, 200, result);
    } catch (error) {
      sendJson(response, 502, { error: error instanceof Error ? error.message : String(error) });
    } finally {
      busy = false;
    }
  });

  server.listen(options.port, "127.0.0.1", () => {
    const address = server.address();
    const port = typeof address === "object" && address ? address.port : options.port;
    console.log(`Web Traffic Inspector companion: http://127.0.0.1:${port}/`);
    if (CONFIG.transport === "browser") console.log(`Authenticated execution uses agent-browser session: ${options.session}`);
    console.log("Press Ctrl+C to stop. Runtime authentication material is held in memory only.");
  });
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});
