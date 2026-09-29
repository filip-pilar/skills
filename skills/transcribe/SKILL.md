---
name: transcribe
description: Transcribe English recording URLs or local audio/video files into Markdown on an Apple Silicon Mac.
---

# Transcribe

Produce a durable `transcript.md` with readable paragraphs and no visible
timestamps. Recognize actual audio using Parakeet Unified EN 0.6B through
FluidAudio/CoreML; never substitute captions or rewrite recognized speech.
Formatting may add paragraph breaks and Markdown escapes only.

Run the bundled helper on the Apple Silicon Mac:

```sh
python3 <skill-dir>/scripts/transcribe.py 'URL_OR_LOCAL_FILE'
```

Use [runtime.md](references/runtime.md) for missing dependencies or recovery.
First use downloads dependencies and model weights; recognition runs locally.
A cloud-only or non-Mac shell cannot substitute for this runtime.

- Default destination: one recording folder under `~/Documents/Transcriptions/`.
  `--destination '/absolute/parent'` changes the parent.
- Add `--speakers` only when requested; labels estimate speakers, not identities.
- Retain downloaded audio without duplicating local inputs. Add `--mp3` on request.
- Matching results are reused. `--rerun` repeats recognition from retained audio;
  `--refresh-source` fetches the URL again.

Return the absolute transcript link after `complete` or `reused`, along with
reported warnings. An incomplete run does not make an older transcript a new
result. Do not paste a long transcript into chat.
