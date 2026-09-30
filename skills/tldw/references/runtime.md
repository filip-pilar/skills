# Runtime and recovery

## Setup

Requires Apple Silicon, macOS 14+, Python 3.10+, FFmpeg/ffprobe, and Swift 6.2+
for the first build. Reuse working tools and help resolve missing dependencies
within host permissions. Homebrew's `ffmpeg` package provides both media tools;
Xcode or compatible Command Line Tools provides Swift.

The helper caches its executable, isolated yt-dlp, and models in
`~/Library/Caches/codex-transcribe/`; `TRANSCRIBE_CACHE` overrides that location.
Builds and model downloads need network access. Cached local-file recognition
does not require downloader setup or media-service access.

For URLs, the helper creates its own yt-dlp environment with `yt-dlp[default]`.
Repair or update that environment only when needed, using its
`bin/python -m pip install -U --pre 'yt-dlp[default]'`. YouTube also requires a
supported JavaScript runtime and matching EJS components. Deno is enabled by
default; the helper explicitly enables Node. Use the
[EJS guide](https://github.com/yt-dlp/yt-dlp/wiki/EJS) for setup diagnostics.
Keep default player clients; cookies and token plugins are not routine setup.

## Recognition and outputs

The bundled [Swift package](../runtime/Package.swift) pins FluidAudio and uses
[Parakeet Unified CoreML](https://huggingface.co/FluidInference/parakeet-unified-en-0.6b-coreml).
Model files are fetched on demand; changed cached weights invalidate reuse.
Long recordings load decoded audio into memory. On memory exhaustion, report
incomplete processing rather than truncating audio or changing engines.
Speaker labels are estimates; overlap and unmatched words are marked explicitly.

Each recording folder contains the transcript, raw `recognition.json`, reuse and
completion metadata, and diagnostics. Speaker and MP3 artifacts are optional.
URL audio is retained; local inputs are referenced. Previous results, including
edited transcripts, move to `history/` before regeneration. Temporary `.work/`
files are removed on success and retained on failure.

Reuse checks source integrity, relevant settings, and output hashes. URL reuse
does not contact the platform; use `--refresh-source` for a changed recording.
Local files use their first audio stream, so prepare another track explicitly
when needed. One invocation handles one completed recording, without playlist
expansion or ongoing streams.

## Recovery

Inspect the reported error, `metadata.json`, and relevant log excerpts. Decode
warnings can accompany a completed result and must be surfaced. Keep raw logs,
recognition text, and signed URLs out of routine status messages.

The helper bounds network retries and rejects unavailable fragments. For URL
failures, fix observed EJS/runtime issues, repair a stale downloader, or refresh
expired metadata. A 403 alone does not identify a login, token, or ban problem.
Consult current [YouTube guidance](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#youtube)
or the [PO Token guide](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide) when
those diagnostics apply.

For a blocked stream, choose a viable audio format from current metadata,
preserving the original language, and pass `--audio-format 'FORMAT_SELECTOR'`.
This implies `--refresh-source`; temporary downloads are separated by format.
For other download options, obtain verified audio separately and pass the local
file to the helper. Do not replace the transcription engine.

Retry after a concrete correction; stop when no evidence-based recovery remains
or access requires unavailable authorization or DRM circumvention. Use cookies
only for user-directed authentication. Same-format interrupted downloads can
resume. Report incomplete processing and the needed next step when blocked.
