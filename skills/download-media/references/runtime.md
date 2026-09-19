# Preparation and recovery

Use a local shell with Python 3.10+, yt-dlp, and FFmpeg/ffprobe. Unlike Transcribe,
this skill has no Apple Silicon or speech-model dependency. The inline controls
need a host supporting Visualize and its follow-up-message bridge. Inspect the
installed Visualize skill when presenting them; do not install a plugin silently.
The HTML does not fetch metadata, embed a remote player, browse folders, or run a
download. Its button asks the agent to execute the selected configuration.

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
the timeline ends at the next whole second; an out point at that endpoint carries
`through_end: true`, meaning the actual end of the recording. Do not pad the file.
Metadata may retain exact fractional duration; the controls and filenames do not.

`--metadata '/absolute/metadata.json'` uses an existing yt-dlp metadata document
instead of making a network request. For a local input, it accepts an ffprobe
document. This supports task-local reuse and offline fixtures. Do not display raw
metadata: it may contain signed media URLs or request headers. The renderer keeps
only the source identity, title, duration, and necessary codec/resolution choices.
Source URLs with embedded credentials are rejected; use user-directed authorized
access through the agent instead. Keep authentication material out of widget state.

## Failures

If dependencies are missing, use an existing environment first. A task-local or
user-cache virtual environment can isolate yt-dlp setup when installation is
authorized; do not modify another skill's runtime or global tool versions.
FFmpeg is a system executable, not the similarly named Python package. Some sites
also need a JavaScript runtime supported by the installed yt-dlp version.

For extractor failures, inspect the concise error and the installed tool's help.
For media HTTP 403 responses, check the yt-dlp version and any newer existing
environment before repeating downloads; successful metadata extraction alone does
not establish media access. Refresh format choices after changing extractors.
Refresh metadata or update an isolated yt-dlp installation when authorized. Do
not keep retrying login/DRM/access failures, import browser cookies automatically,
or claim unsupported sources are downloadable. Metadata availability does not
guarantee the selected media can be fetched. Unknown duration or missing stream
details need further inspection before rendering an accurate timeline.

Source changes require a fresh panel. The rendered options are a snapshot, so
refresh expired stream metadata at download time without silently changing the
user's requested output.
