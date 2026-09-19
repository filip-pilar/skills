# Runtime and recovery

## Setup

Requirements: Apple Silicon, macOS 14+, Python 3.10+, ffmpeg/ffprobe, and Swift 6.2+ for the first build. Check the executables used by this task and help install missing dependencies through the host's normal permission mechanism; do not stop at a missing-tool error. On a Mac with Homebrew, `brew install ffmpeg` supplies both audio utilities. Xcode or compatible Command Line Tools provide Swift. Resolve setup before starting the recording; do not replace working global tools unnecessarily.

The helper caches its compiled Swift executable, isolated yt-dlp, and model weights in `~/Library/Caches/codex-transcribe/`. `TRANSCRIBE_CACHE` overrides this for testing or constrained installations. SwiftPM may also use its normal user caches. A filesystem lock serializes helper runs to avoid simultaneous builds/model downloads. A waiting invocation prints its preparation stage but has not started recognition yet.

For fresh URL downloads, use the helper's isolated `yt-dlp` environment. The helper creates it on first use with `yt-dlp[default]`, including the matching EJS challenge solver, on yt-dlp's recommended nightly channel. To prepare, repair, or update it when needed, create the venv if missing, then run its `bin/python -m pip install -U --pre 'yt-dlp[default]'`. Reuse a working installation; do not upgrade on every request or modify another skill's environment. Local files and verified retained audio do not require yt-dlp or a network check.

YouTube also needs a supported JavaScript runtime. Reuse compatible Deno or Node; if neither is available, install Deno (on Homebrew, `brew install deno`). Deno is enabled by default, and the helper explicitly enables Node with `--js-runtimes node`. Use the same option for agent-run commands when relying on Node; the helper ignores global yt-dlp configuration. Check versions and EJS compatibility against the [official setup guide](https://github.com/yt-dlp/yt-dlp/wiki/EJS). For a new or changed environment, inspect verbose diagnostics during the first extraction and resolve setup warnings before downloading. The helper retains download warnings in `run.log` and reports extraction warnings on stderr.

Keep yt-dlp's default player clients. Do not pin client lists, import browser cookies, or install token-provider plugins as routine setup. Consult upstream [update guidance](https://github.com/yt-dlp/yt-dlp#update) and [YouTube guidance](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#youtube) when setup or diagnostics need it.

## Recognition runtime

FluidAudio is pinned to commit `b68f484789d81fda21efbf81e2ca9fcfd9dc22aa`. The SDK downloads its CoreML models on demand. Metadata records the model repository, SDK revision, helper fingerprint, settings, and local model-cache fingerprint. Upstream model files are fetched using the SDK's model-hub mechanism, not a separately pinned Hugging Face revision. Changes to the cached model files invalidate reuse. There is no automatic SDK upgrade or alternate transcription model.

The int8 full-attention encoder runs with CPU + Apple Neural Engine; decoding is on CPU. FluidAudio handles overlapping 15-second windows internally. Recognition currently loads the decoded audio into memory: very long recordings can require substantial RAM. On memory exhaustion, report the incomplete run; do not silently truncate or switch engines. Speaker labeling uses FluidAudio's offline diarizer, with emission-time alignment and a 350 ms nearest-boundary tolerance; overlap and unmatched words are labeled explicitly. Labels can be wrong, especially around rapid turns or overlapping voices.

## Recording folder

- `transcript.md`: readable paragraphs, no visible timestamps.
- `recognition.json`: unmodified recognizer text, tokens, word timings, and decoded duration.
- `metadata.json`: source identity/hash, model/runtime settings, completion state, and output hashes.
- `speakers.json`: raw diarization segments, only when labeling is requested.
- `source.*`: retained URL download; local source paths are recorded instead.
- `audio.mp3` and `mp3.json`: optional export and reuse record; an existing MP3 input is not duplicated.
- `run.log`: model/download diagnostics; `decode.log`: audio decoder diagnostics. Successful exits with decoder diagnostics are surfaced as warnings, not silently ignored.
- `history/`: previous durable results when a recording is regenerated, including manually edited transcripts.
- `.work/`: temporary conversion/download files, removed after success and retained on failure.

The destination flag selects the parent, and the helper creates a title plus identity suffix beneath it. Reusing a URL checks retained source integrity without contacting the platform. Use `--refresh-source` when the remote recording changed. Local identity includes absolute path and content hash. Relevant settings and output hashes govern completed-result reuse. A user-edited transcript is preserved in history before regeneration.

A local source that contains multiple audio streams uses its first audio stream. If the user needs another local track, establish the appropriate input first. URL downloads use yt-dlp's ranked `bestaudio/best` selection; preserve the original audio unless another track was requested. One invocation handles one completed recording; ongoing streams and playlist expansion are rejected.

## Recovery

Read the reported error and relevant diagnostics (`metadata.json` and the tail of `run.log` when present). Do not dump entire logs or raw recognition into model context. A failed run exits nonzero and reports incomplete processing; a preceding successful transcript is not the new result. The helper bounds ordinary network, extractor, and fragment retries at three and refuses to skip unavailable fragments. It does not update yt-dlp and repeat every failed command automatically.

For URL failures, diagnose before retrying: fix missing runtime/EJS components, update a stale isolated downloader, or refresh expired metadata when supported by the error. A 403 alone does not establish missing authentication, a token problem, or a ban. If one stream is blocked, inspect fresh metadata for a viable audio stream, preserving the original language. Pass `--audio-format 'FORMAT_SELECTOR'` to the helper for that source-specific selection; this implies `--refresh-source`. Use argument arrays and current metadata, never hard-coded IDs from another recording. Temporary downloads are separated by format so a changed selection cannot resume incompatible bytes. For recovery requiring other yt-dlp options, fetch and verify audio separately and run the helper on that local file; do not change the transcription engine.

For YouTube token diagnostics, consult the current [PO Token guide](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide): tokens are separate from JavaScript challenge solving. Keep default clients unless current diagnostics and upstream guidance justify an override. Stop on DRM or explicit access requirements; use account cookies only for user-directed authentication when actually needed.

Make at most two targeted recovery attempts after the initial failure, each based on new evidence or a concrete correction. This is a limit, not a mandatory sequence. If nothing relevant can change, stop. Keep quick recovery quiet; if it takes time, explain briefly what is being fixed. On failure, state that no new transcript was completed and give one useful next step supported by the evidence. Do not expose raw logs/signed URLs or request an upload before considering available recovery.

Interrupted same-format downloads can resume through yt-dlp. Model loading uses FluidAudio's incomplete-download recovery. Re-run after resolving the concrete cause. Dependency installation/build and output writes may require the host's normal permission mechanism.

Model and build setup need network access, even though inference is offline. With dependencies/models cached, local files can be transcribed without fetching their media from a service. Missing Mac access is a host limitation, not a reason to install a Linux/cloud substitute.

## Sources

Runtime source: [FluidAudio](https://github.com/FluidInference/FluidAudio/tree/b68f484789d81fda21efbf81e2ca9fcfd9dc22aa). Model: [Parakeet Unified CoreML](https://huggingface.co/FluidInference/parakeet-unified-en-0.6b-coreml).
