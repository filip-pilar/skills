#!/usr/bin/env python3
"""Inspect media and render task-owned inline controls; no media downloads."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.parse import urlsplit

SKILL = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL / 'assets' / 'controls.html'
MARKER = '/*__DOWNLOAD_MEDIA_SOURCE__*/null'


def run(args):
    result = subprocess.run(args, capture_output=True, text=True, timeout=120)
    if result.returncode:
        # Error output can include signed URLs/headers: keep it out of stdout.
        raise ValueError(f'{Path(args[0]).name} inspection failed (exit {result.returncode}); '
                         'inspect the source and tool diagnostics separately.')
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError('Inspection did not return valid JSON.') from exc


def tool(name):
    path = shutil.which(name)
    if not path:
        raise ValueError(f'Missing {name}; see references/runtime.md for setup.')
    return path


def positive(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def location(value):
    parsed = urlsplit(value)
    if parsed.scheme in ('http', 'https'):
        if not parsed.hostname or parsed.username or parsed.password:
            raise ValueError('Use an HTTP(S) source without embedded login credentials.')
        return 'url', value
    if '://' in value:
        raise ValueError('Use an HTTP(S) URL or a local media file.')
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise ValueError('Local input is not a regular media file.')
    return 'local', str(path)


def local_metadata(raw, path):
    """Map ffprobe to the small subset of yt-dlp fields used below."""
    format_info = raw.get('format', {})
    try:
        duration = float(format_info.get('duration', 'nan'))
    except (ValueError, TypeError):
        duration = float('nan')
    names = {'h264': 'avc1', 'hevc': 'hvc1', 'av1': 'av01', 'aac': 'mp4a'}
    formats = []
    for stream in raw.get('streams', []):
        kind = stream.get('codec_type')
        if kind not in ('video', 'audio') or stream.get('disposition', {}).get('attached_pic'):
            continue
        codec = names.get(stream.get('codec_name'), stream.get('codec_name') or 'unknown')
        # Containers below describe viable output profiles, not the input suffix.
        ext = 'mp4' if codec.startswith(('avc1', 'hvc1', 'av01')) else 'webm' if codec in ('vp9', 'vp8', 'opus', 'vorbis') else 'm4a' if codec == 'mp4a' else codec
        formats.append({'vcodec': codec if kind == 'video' else 'none',
                        'acodec': codec if kind == 'audio' else 'none',
                        'height': stream.get('height'), 'ext': ext})
    stat = Path(path).stat()
    return {'id': hashlib.sha256(path.encode()).hexdigest()[:16],
            'extractor_key': 'local', 'title': Path(path).stem,
            'duration': duration, 'formats': formats,
            '_local_stamp': [stat.st_size, stat.st_mtime_ns]}


def build_source(raw, kind, source_location, settings=None):
    if not isinstance(raw, dict):
        raise ValueError('Expected one metadata object.')
    if raw.get('_type') in ('playlist', 'multi_video') or 'entries' in raw:
        raise ValueError('Choose one recording; playlists are not expanded.')
    if raw.get('is_live') or raw.get('live_status') in ('is_live', 'is_upcoming', 'post_live'):
        raise ValueError('Use a completed recording with a known duration.')
    duration = raw.get('duration')
    if not positive(duration):
        raise ValueError('Source duration is unknown; inspect it before preparing controls.')
    duration = float(duration)
    end = math.ceil(duration)
    candidates = raw.get('formats') or [raw]
    formats = [f for f in candidates if isinstance(f, dict) and not f.get('has_drm')]
    videos = [f for f in formats if f.get('vcodec') not in (None, 'none') and positive(f.get('height'))]
    audios = [f for f in formats if f.get('acodec') not in (None, 'none')]
    if not videos and not audios:
        raise ValueError('No usable stream details; inspect the media before rendering options.')
    profiles = [('mp4', 'mp4', 'H.264', ('avc1',), 'AAC'),
                ('webm', 'webm', 'VP9', ('vp9', 'vp09'), 'Opus'),
                ('mp4_av1', 'mp4', 'AV1', ('av01',), 'AAC'),
                ('mp4_hevc', 'mp4', 'HEVC', ('hvc1', 'hev1'), 'AAC')]
    video_formats = []
    for ident, ext, codec, prefixes, audio in profiles:
        heights = sorted({int(f['height']) for f in videos if str(f['vcodec']).startswith(prefixes)}, reverse=True)
        if heights:
            video_formats.append({'id': ident, 'label': f'{ext.upper() if ext != "webm" else "WebM"} · {codec}', 'ext': ext,
                                  'codec': codec, 'audio': audio, 'heights': heights})
    if videos and not video_formats:
        video_formats.append({'id': 'mp4', 'label': 'MP4 · H.264 (convert)', 'ext': 'mp4',
                              'codec': 'H.264', 'audio': 'AAC',
                              'heights': sorted({int(f['height']) for f in videos}, reverse=True)})
    video_formats.sort(key=lambda f: f['heights'][0], reverse=True)
    audio_formats = []
    for ident, label, codec, prefixes in [('m4a', 'M4A · AAC', 'AAC', ('mp4a', 'aac')),
                                          ('webm', 'WebM · Opus', 'Opus', ('opus',)),
                                          ('flac', 'FLAC', 'FLAC', ('flac',))]:
        if any(str(f['acodec']).startswith(prefixes) for f in audios):
            audio_formats.append({'id': ident, 'label': label, 'ext': ident, 'audio': codec})
    if audios:
        native_mp3 = any(str(f['acodec']).startswith('mp3') for f in audios)
        audio_formats += [{'id': 'mp3', 'label': 'MP3' if native_mp3 else 'MP3 · convert', 'ext': 'mp3', 'audio': 'MP3'},
                          {'id': 'wav', 'label': 'WAV · PCM', 'ext': 'wav', 'audio': 'PCM'}]
    content = (['video-audio', 'video', 'audio'] if videos and audios else ['video'] if videos else ['audio'])
    canonical = raw.get('webpage_url') if kind == 'url' else None
    if canonical:
        p = urlsplit(str(canonical))
        if p.scheme not in ('https', 'http') or not p.hostname or p.username or p.password:
            canonical = None
    canonical = canonical or (source_location if kind == 'url' else None)
    provider = str(raw.get('extractor_key') or raw.get('extractor') or 'media')
    identifier = f'{provider}:{raw.get("id") or hashlib.sha256(source_location.encode()).hexdigest()[:16]}'
    # A digest identifies state; the saved widget state contains no source URL.
    key = hashlib.sha256(json.dumps([identifier, source_location, raw.get('_local_stamp')]).encode()).hexdigest()
    source = {'id': identifier, 'key': key, 'kind': kind, 'url': canonical,
              'local_path': source_location if kind == 'local' else None,
              'title': str(raw.get('title') or raw.get('id') or 'Media'),
              'duration': end, 'media_duration': duration, 'available_content': content,
              'video_formats': video_formats, 'audio_formats': audio_formats}
    initial = {'clips': [{'id': 1, 'start': 0, 'end': end}], 'active': 1, 'nextId': 2,
               'content': content[0], 'resolution': video_formats[0]['heights'][0] if videos else None,
               'videoFormat': video_formats[0]['id'] if videos else '',
               'audioFormat': audio_formats[0]['id'] if audios else ''}
    if settings is not None:
        if not isinstance(settings, dict) or set(settings) - {'content', 'resolution', 'format', 'clips'}:
            raise ValueError('Settings support content, resolution, format, and clips only.')
        requested = settings.get('content', initial['content'])
        if requested not in content:
            raise ValueError('Requested content is not available in this source.')
        initial['content'] = requested
        key_name = 'audioFormat' if requested == 'audio' else 'videoFormat'
        choices = audio_formats if requested == 'audio' else video_formats
        choice = settings.get('format', initial[key_name])
        selected = next((f for f in choices if f['id'] == choice), None)
        if selected is None:
            raise ValueError('Requested format is unavailable; use a reported format ID.')
        initial[key_name] = choice
        resolution = settings.get('resolution', selected.get('heights', [None])[0])
        if requested == 'audio' and 'resolution' in settings:
            raise ValueError('Audio-only output has no resolution.')
        if requested != 'audio':
            if not integer(resolution) or resolution not in selected['heights']:
                raise ValueError('Requested source resolution is unavailable; no upscaling was chosen.')
            initial['resolution'] = resolution
        clips = settings.get('clips')
        if clips is not None:
            if not isinstance(clips, list) or not clips:
                raise ValueError('Provide at least one clip.')
            for c in clips:
                if not isinstance(c, dict) or set(c) != {'start', 'end'} or not all(integer(c[k]) for k in ('start', 'end')) or not 0 <= c['start'] < c['end'] <= end:
                    raise ValueError('Clips need whole-second start/end values within the source duration.')
            initial['clips'] = [dict(c, id=i + 1) for i, c in enumerate(clips)]
            initial['nextId'] = len(clips) + 1
    source['initial'] = initial
    return source


def render(source):
    template = TEMPLATE.read_text(encoding='utf-8')
    if template.count(MARKER) != 1:
        raise ValueError('Controls template must contain exactly one data marker.')
    data = json.dumps(source, ensure_ascii=True, allow_nan=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    return template.replace(MARKER, data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--settings', type=Path)
    parser.add_argument('--metadata', type=Path)
    args = parser.parse_args()
    try:
        kind, source_location = location(args.source)
        output = args.output.expanduser().absolute()
        if not args.output.is_absolute() or output.is_symlink() or SKILL in output.resolve().parents:
            raise ValueError('Write HTML to an absolute task-owned path outside the installed skill.')
        protected = [p.resolve() for p in (args.settings, args.metadata) if p]
        if kind == 'local':
            protected.append(Path(source_location))
        if output.resolve() in protected:
            raise ValueError('Output must not overwrite an input file.')
        if args.metadata:
            raw = json.loads(args.metadata.read_text(encoding='utf-8'))
        elif kind == 'url':
            raw = run([tool('yt-dlp'), '--ignore-config', '--no-cache-dir', '--no-playlist',
                       '--no-progress', '--skip-download', '--dump-single-json', '--retries', '3',
                       '--extractor-retries', '3', '--', source_location])
        else:
            raw = run([tool('ffprobe'), '-v', 'error', '-show_format', '-show_streams', '-of', 'json', source_location])
        if kind == 'local':
            raw = local_metadata(raw, source_location)
        settings = json.loads(args.settings.read_text(encoding='utf-8')) if args.settings else None
        source = build_source(raw, kind, source_location, settings)
        html = render(source)
        output.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            handle.write(html)
        print(json.dumps({'status': 'prepared', 'html': str(output), 'title': source['title'],
                          'duration_seconds': source['duration'], 'content': source['available_content'],
                          'video_formats': source['video_formats'], 'audio_formats': source['audio_formats']}))
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print(f'prepare: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
