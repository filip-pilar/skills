# Runtime and recovery

Requirements: Apple Silicon, macOS 14+, Python 3.10+, ffmpeg/ffprobe, and Swift 6.2+ for the first build. Xcode or compatible Command Line Tools provide Swift; Homebrew `ffmpeg` provides the audio utilities. Downloading URLs uses an isolated yt-dlp venv; supported sites may additionally require a JavaScript runtime such as Deno. Do not silently import browser cookies or credentials. If access requires login, explain the site's error and ask for an accessible recording or user-directed authentication.

The helper caches its compiled Swift executable, isolated yt-dlp, and model weights in `~/Library/Caches/codex-transcribe/`. `TRANSCRIBE_CACHE` overrides this for testing or constrained installations. SwiftPM may also use its normal user caches. A filesystem lock serializes helper runs to avoid simultaneous builds/model downloads. A waiting invocation prints its preparation stage but has not started recognition yet.

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

A source that contains multiple audio streams uses its first audio stream, matching the default workflow. If the user needs another language/track, establish the appropriate local input first. One invocation handles one completed recording; ongoing streams and playlist expansion are rejected.

## Recovery

Read the reported error, `metadata.json`, and the tail of `run.log` as needed. Do not dump entire logs or raw recognition into model context. A failed run exits nonzero and leaves an incomplete status; a preceding successful transcript can remain available but is not the new result. Interrupted downloads are resumed by yt-dlp. Model loading uses FluidAudio's incomplete-download recovery. Re-run after resolving the concrete cause. Dependency installation/build and output writes may require the host's normal permission mechanism.

Model and build setup need network access, even though inference is offline. With dependencies/models cached, local files can be transcribed without fetching their media from a service. Missing Mac access is a host limitation, not a reason to install a Linux/cloud substitute.

## Sources

Runtime source: [FluidAudio](https://github.com/FluidInference/FluidAudio/tree/b68f484789d81fda21efbf81e2ca9fcfd9dc22aa). Model: [Parakeet Unified CoreML](https://huggingface.co/FluidInference/parakeet-unified-en-0.6b-coreml).
