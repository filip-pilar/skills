const MAX_RESPONSE_BYTES = 5_000_000;
const MAX_OUTPUT_CHARS = 1_000_000;
const SECRET_KEY = /(?:authorization|cookie|password|passwd|secret|credential|session|private.?key|access.?token|refresh.?token|api.?key|csrf|xsrf|signature|signed.?token)|^(?:token|nonce|ticket)$/i;
const SECRET_QUERY = /(?:^|[-_])(?:authorization|credential|secret|session|token|signature|sig|signed|private[-_]?key|api[-_]?key|access[-_]?key|key[-_]?pair[-_]?id|x[-_]?amz[-_](?:credential|signature|security[-_]?token)|code|nonce|ticket)(?:$|[-_])/i;
const SAFE_HEADERS = new Set(['cache-control', 'content-language', 'content-length', 'content-type', 'etag', 'last-modified', 'retry-after', 'x-ratelimit-limit', 'x-ratelimit-remaining', 'x-ratelimit-reset']);

function safeData(value, key = '', depth = 0, seen = new WeakSet()) {
  if (SECRET_KEY.test(key)) return '[REDACTED]';
  if (depth > 20) return '[MAX DEPTH]';
  if (typeof value === 'string') {
    if (/(?:^|[-_])(?:url|uri|href|link|location)(?:$|[-_])/i.test(key)) {
      try {
        const absolute = /^(?:[a-z][a-z0-9+.-]*:|\/\/)/i.test(value);
        const url = new URL(value, 'http://wti.invalid');
        if (!['http:', 'https:'].includes(url.protocol)) return '[UNSAFE URL]';
        url.username = ''; url.password = ''; url.hash = '';
        for (const name of [...url.searchParams.keys()]) if (SECRET_QUERY.test(name)) url.searchParams.set(name, '[REDACTED]');
        value = absolute ? url.href : url.pathname + url.search;
      } catch { return '[INVALID URL]'; }
    }
    value = value.replace(/\bBearer\s+[A-Za-z0-9._~+\/-]+=*/gi, 'Bearer [REDACTED]')
      .replace(/([?&](?:authorization|credential|secret|session|token|signature|sig|private[-_]?key|api[-_]?key|access[-_]?key|key[-_]?pair[-_]?id|x[-_]?amz[-_](?:credential|signature|security[-_]?token)|nonce|ticket)=)[^&#\s"']+/gi, '$1[REDACTED]');
    return value.length > MAX_OUTPUT_CHARS ? value.slice(0, MAX_OUTPUT_CHARS) + '[TRUNCATED]' : value;
  }
  if (value === null || typeof value !== 'object') return value;
  if (seen.has(value)) return '[CIRCULAR]';
  seen.add(value);
  try {
    if (Array.isArray(value)) {
      const items = value.slice(0, 5000).map(item => safeData(item, '', depth + 1, seen));
      if (value.length > items.length) items.push('[TRUNCATED]');
      return items;
    }
    const entries = Object.entries(value);
    const output = Object.fromEntries(entries.slice(0, 5000)
      .filter(([name]) => !/headers$/i.test(key) || SAFE_HEADERS.has(name.toLowerCase()))
      .map(([name, item]) => [name, safeData(item, name, depth + 1, seen)]));
    if (entries.length > 5000) output._truncated = true;
    return output;
  } finally { seen.delete(value); }
}

function safeJson(value) {
  const text = JSON.stringify(safeData(value), null, 2);
  if (text === undefined) throw new Error('No JSON result was returned.');
  if (text.length <= MAX_OUTPUT_CHARS) return text;
  let length = Math.floor(MAX_OUTPUT_CHARS / 2);
  for (;;) {
    const preview = JSON.stringify({truncated: true, originalCharacters: text.length, preview: text.slice(0, length)});
    if (preview.length <= MAX_OUTPUT_CHARS) return preview;
    length = Math.floor(length / 2);
  }
}

async function responseData(response) {
  const reader = response.body?.getReader();
  const chunks = [];
  let size = 0;
  if (reader) {
    try {
      for (;;) {
        const {done, value} = await reader.read();
        if (done) break;
        size += value.length;
        if (size > MAX_RESPONSE_BYTES) throw new Error('Response exceeded the size limit.');
        chunks.push(value);
      }
    } finally { await reader.cancel(); }
  }
  const bytes = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
  const text = new TextDecoder().decode(bytes);
  let body = text;
  try { body = text === '' ? null : JSON.parse(text); } catch {}
  return {ok: response.ok, status: response.status, url: response.url,
    headers: Object.fromEntries(response.headers.entries()), body};
}
