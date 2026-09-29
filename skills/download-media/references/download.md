# Export selected media

Use the submitted source, clips, and shared settings, or the user's explicit
selection when bypassing controls. Resolve settings against inspected metadata;
never silently substitute quality, timing, or format.

## Streams and cuts

- Select streams by current properties, not remembered format IDs. Preserve
  requested resolution, frame rate, and audio; never upscale a selected height.
  Prefer original audio over dubs unless another language was requested. Silent
  video is valid, and audio-only output does not need a video download.
- Set container and codecs explicitly: MP4 does not imply H.264. Source and
  output codecs may differ when conversion is needed.
- Use yt-dlp's default player clients with
  `--ignore-config --no-cache-dir --no-playlist --abort-on-unavailable-fragments`.
  Pass argument arrays and `--` before the URL. Follow
  [runtime.md](runtime.md) for JavaScript setup and bounded recovery.
- Prefer section downloads for excerpts; overlapping clips can share a retained
  input. `--download-sections '*START-END'` uses FFmpeg, and
  `--force-keyframes-at-cuts` re-encodes. Accurate FFmpeg trimming is another
  option. Whole-second UI precision does not permit keyframe-rounded cuts;
  neither successful exit nor matching duration proves the right boundaries.
- An out point of “end” means EOF. The rounded UI endpoint
  may exceed exact duration by less than a second; do not pad with silence or
  frozen frames.

## Files and verification

Keep working media, metadata, settings, and logs in task-owned storage. Save only
verified media in `~/Downloads/`, without sidecars or a persistent history cache.

Build names from the inspected title normalized to letters, digits, and
underscores, whole-second source timestamps, content type, video resolution,
and the next unused `_vNNN` suffix:

`Source_Title_00-50_to_01-20_video_audio_1080p_v001.mp4`

Titles and suggested names cannot supply paths. Allocate separate versions even
for identical clips in one batch;
use exclusive reservation or no-clobber publication to prevent overwrites.

Generate temporary outputs, then check streams, codecs, container, dimensions,
and duration with ffprobe. Decode or inspect cut boundaries when needed,
especially after section downloads. Allow normal codec priming/frame-duration
variation without accepting truncated or incorrectly selected footage. Preserve
successful outputs on partial failure and link only files verified for this run.

## Reuse

Reuse media only when this task establishes its source identity, original
interval, sufficient quality, and full coverage; inspect actual streams and any
recorded hash. Prefer original inputs to repeatedly re-encoding exports. A
filename alone cannot establish identity or offsets.

URL clip times refer to the original recording: subtract a retained excerpt's
original start when trimming it. Times for an explicitly supplied local file
refer to that file. Map back to original titles and offsets only when known;
otherwise use its filename stem and local times. Refetch a URL when retained
media cannot be identified reliably.

For option details, use the [yt-dlp guide](https://github.com/yt-dlp/yt-dlp#format-selection)
and [FFmpeg documentation](https://ffmpeg.org/ffmpeg.html#Main-options).
