# Runtime and preparation

Requires a local shell, Python 3.10+, FFmpeg/ffprobe, and yt-dlp for URLs.
Visualize supplies the inline card and follow-up bridge; use its installed skill
when displaying the card. The HTML itself neither fetches media nor downloads it.

## Setup

Reuse working tools; help set up missing dependencies within host permissions.
FFmpeg and ffprobe are executables (`brew install ffmpeg` on Homebrew), not the
similarly named Python packages. Local files do not require yt-dlp setup.

For missing or outdated yt-dlp, use a dedicated virtual environment such as
`~/Library/Caches/codex-download-media/yt-dlp`, with its Python running
`-m pip install -U --pre 'yt-dlp[default]'`. Reuse that environment for inspection
and downloading; do not modify another skill's environment or upgrade every run.
Put its `bin` on this process's PATH, or pass extracted metadata to the helper.

YouTube needs matching EJS components and a supported JavaScript runtime. Deno
is enabled by default; the helper enables Node with `--js-runtimes node`, which
agent-run commands also need when relying on Node. Resolve first-extraction setup
warnings using the [EJS guide](https://github.com/yt-dlp/yt-dlp/wiki/EJS).
Keep default player clients. Browser cookies, pinned client lists, and token
plugins are not routine setup.

## Inputs

The helper inspects URLs with yt-dlp and local files with ffprobe. It writes the
card and emits a small configuration summary; it does not install tools or
export media. Prefill natural-language choices with `--settings`:

```json
{
  "content": "audio",
  "format": "m4a",
  "clips": [{"start": 50, "end": 80}, {"start": 120, "end": 140}]
}
```

`content` is `video-audio`, `video`, or `audio`. Optional `resolution` is a source
height, such as `1080`; `format` is an ID reported by the helper. Unsupported
explicit settings fail instead of silently falling back. Audio options include
MP3/WAV conversions; unsupported video codecs can use H.264 conversion.

Ranges use integer seconds. A fractional duration rounds up for the timeline;
selecting that endpoint means actual EOF, not padding.

Use `--metadata '/absolute/metadata.json'` for retained yt-dlp metadata or local
ffprobe output. Keep raw metadata private: it can contain signed URLs or headers.
The renderer retains only source identity, title, duration, and necessary media
choices. URLs with embedded usernames/passwords are rejected; query strings are
retained. Keep signed source URLs private and out of shared cards or reports.

## Failures

Bound network retries with `--retries 3 --fragment-retries 3 --extractor-retries 3`
and abort unavailable fragments. Diagnose actual errors: successful metadata
extraction does not establish stream access, and a 403 does not prove missing
tokens, login requirements, or a ban.

Repair missing EJS/runtime support, update a stale dedicated downloader, refresh
expired metadata, or try a viable stream/method when evidence supports it.
Preserve selected quality, original audio, and timing. Consult the current
[YouTube guidance](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#youtube) or
[PO Token guide](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide) for relevant
diagnostics; JavaScript challenges and PO tokens are separate mechanisms.

Stop when no evidence-based recovery remains, or access requires unavailable
authorization or DRM circumvention. Use account cookies only for user-directed
authentication. Report unresolved clips and a useful next step without exposing
signed URLs or raw logs. A changed source needs a new card; refreshing expired
metadata must not change the selected output.
