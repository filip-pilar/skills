# Preparation and recovery

Use a local shell with Python 3.10+, yt-dlp, and FFmpeg/ffprobe. Unlike Transcribe,
this skill has no Apple Silicon or speech-model dependency. The inline controls
need a host supporting Visualize and its follow-up-message bridge. Inspect the
installed Visualize skill when presenting them; do not install a plugin silently.
The HTML does not fetch metadata, embed a remote player, browse folders, or run a
download. Its button asks the agent to execute the selected configuration.

## Setup

Check the executables actually used by this task before first use: Python,
FFmpeg/ffprobe, and yt-dlp for URLs. Reuse working tools and help install missing
dependencies through the host's normal permission mechanism; do not stop at a
missing-tool error. On a Mac with Homebrew, `brew install ffmpeg` supplies both
media utilities. They are executables, not the similarly named Python packages.

For missing or outdated yt-dlp, use an isolated environment owned by this skill,
such as `~/Library/Caches/codex-download-media/yt-dlp`, created with `python3 -m venv`.
Install with that environment's Python: `-m pip install -U --pre 'yt-dlp[default]'`.
This includes the matching EJS challenge solver and follows yt-dlp's recommended
nightly channel. Reuse a working installation; do not upgrade on every request or
modify another skill's environment or global tools to fix this skill. Put its
`bin` directory on this process's PATH, or extract metadata with its executable
and pass `--metadata` to the helper. Use the same environment for downloading.

YouTube also needs a supported JavaScript runtime. Reuse compatible Deno or Node;
if neither is available, install Deno (on Homebrew, `brew install deno`). Deno is
enabled by yt-dlp by default. The helper also enables Node with `--js-runtimes node`;
use that option for agent-run commands when relying on Node. Do not rely on a
global yt-dlp configuration: this skill ignores it. Check runtime versions and
matching EJS components against the [official setup guide](https://github.com/yt-dlp/yt-dlp/wiki/EJS).
For a new or changed environment, inspect verbose diagnostics during the first
metadata extraction, resolve setup warnings, and reuse that metadata for the panel.
Skip downloader setup for local files.

Keep yt-dlp's default player clients. Do not pin client lists, import browser
cookies, or install token-provider plugins as routine setup. Its
[update guidance](https://github.com/yt-dlp/yt-dlp#update) and
[YouTube guidance](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#youtube) own these
changing details; consult them when the installed setup or diagnostics need it.

## Preparation inputs

`scripts/prepare.py` accepts a URL or an explicitly supplied local media path.
It inspects a URL with yt-dlp (no playlists, inherited config, or disk cache), or
a local file with ffprobe. It emits only a small configuration summary and the
HTML path. It does not download media or install dependencies.

Supply a settings JSON file with `--settings` to prefill natural-language choices:

```json
{
  "content": "audio",
  "format": "m4a",
  "clips": [{"start": 50, "end": 80}, {"start": 120, "end": 140}]
}
```

Content is `video-audio`, `video`, or `audio`. Optional `resolution` is a source
height such as `1080`; optional `format` is an ID reported by the helper. The helper
rejects unavailable settings instead of silently changing a user's explicit choice.
With no settings it chooses source-derived defaults. Available source formats and
resolutions become UI options, with MP3/WAV conversions available for audio and
H.264 conversion as a fallback for otherwise unsupported video codecs.

All user-facing ranges are integer seconds. For a fractional source duration,
the timeline ends at the next whole second; an out point at that endpoint is sent
as “end”, meaning the actual end of the recording. Do not pad the file.
Metadata may retain exact fractional duration; the controls and filenames do not.

`--metadata '/absolute/metadata.json'` uses an existing yt-dlp metadata document
instead of making a network request. For a local input, it accepts an ffprobe
document. This supports task-local reuse and offline fixtures. Do not display raw
metadata: it may contain signed media URLs or request headers. The renderer keeps
only the source identity, title, duration, and necessary codec/resolution choices.
Source URLs with embedded credentials are rejected; use user-directed authorized
access through the agent instead. Keep authentication material out of widget state.

## Failures

Use bounded network retries (`--retries 3 --fragment-retries 3 --extractor-retries 3`)
and `--abort-on-unavailable-fragments` so missing segments cannot silently produce
an incomplete recording. A 403 is a symptom, not a diagnosis. Inspect the actual
error and relevant diagnostics before choosing a recovery action. Fix missing
runtime/EJS components, update a stale isolated downloader, or refresh expired
metadata when the evidence supports it. Do not update and repeat every failed
command automatically. Metadata success does not establish media access, and
missing duration/stream details need inspection before rendering the panel.

If a particular stream or download method is blocked, choose a viable alternative
from fresh metadata while preserving requested quality, timing, and original audio.
The requested output codec/container need not match the downloaded source; FFmpeg
can convert it. Do not hard-code format IDs or routinely rotate player clients.
For YouTube token diagnostics, consult the current
[PO Token guide](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide): these tokens are
separate from JavaScript challenge solving. Do not infer missing tokens or login
from 403 alone. Stop on DRM or explicit access requirements; use account cookies
only for user-directed authentication when actually needed.

Make at most two targeted recovery attempts after the initial failure, each based
on new evidence or a concrete correction. This is a limit, not a sequence to run
for every error. If nothing relevant can change, stop instead of cycling commands.

Keep quick recovery quiet. If it takes extra time, say what is happening plainly,
for example: “The first download method was blocked. I’m trying another.” On
success, deliver the files. If recovery fails, state the outcome and any successful
clips, then one useful next step supported by the evidence. For example: “YouTube
refused the download after I tried another available method. No file was saved.”
Offer a later retry or a local source file when appropriate; do not ask for an
upload before trying available recovery. Include the HTTP code when useful, but
keep signed URLs, raw logs, and unverified claims about bans out of the response.

For a changed source, inspect it and generate a new card from its metadata.
Rendered options are a snapshot, so refresh expired stream metadata at download
time without silently changing the user's requested output.
