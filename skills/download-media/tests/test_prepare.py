import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SKILL = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('prepare', SKILL / 'scripts' / 'prepare.py')
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)
URL = 'https://example.org/watch?v=fixture'


def metadata():
    return {'id': 'fixture', 'extractor_key': 'Example', 'title': 'Fixture Recording',
            'webpage_url': URL, 'duration': 90.25,
            'formats': [
                {'ext': 'mp4', 'height': 1080, 'vcodec': 'avc1.64', 'acodec': 'none', 'url': 'https://secret.test/?sig=private'},
                {'ext': 'mp4', 'height': 720, 'vcodec': 'avc1.64', 'acodec': 'none'},
                {'ext': 'webm', 'height': 720, 'vcodec': 'vp9', 'acodec': 'none'},
                {'ext': 'm4a', 'vcodec': 'none', 'acodec': 'mp4a.40.2', 'http_headers': {'Cookie': 'private'}},
                {'ext': 'mhtml', 'vcodec': 'none', 'acodec': 'none', 'height': 9999}]}


class PrepareTests(unittest.TestCase):
    def source(self, settings=None, raw=None):
        return prepare.build_source(metadata() if raw is None else raw, 'url', URL, settings)

    def test_profiles_and_full_length_defaults(self):
        s = self.source()
        self.assertEqual(s['duration'], 91)
        self.assertEqual(s['media_duration'], 90.25)
        self.assertEqual(s['initial']['clips'], [{'id': 1, 'start': 0, 'end': 91}])
        self.assertEqual(s['initial']['resolution'], 1080)
        self.assertEqual([f['heights'] for f in s['video_formats']], [[1080, 720], [720]])

    def test_prefills_shared_settings_and_independent_clips(self):
        s = self.source({'content': 'audio', 'format': 'mp3', 'clips': [{'start': 0, 'end': 10}, {'start': 20, 'end': 91}]})
        self.assertEqual(s['initial']['audioFormat'], 'mp3')
        self.assertEqual(s['initial']['nextId'], 3)
        self.assertEqual(s['initial']['clips'][1], {'id': 2, 'start': 20, 'end': 91})

    def test_default_does_not_sacrifice_source_resolution_for_codec(self):
        raw = metadata()
        raw['formats'][2]['height'] = 2160
        source = self.source(raw=raw)
        self.assertEqual(source['initial']['resolution'], 2160)
        self.assertEqual(source['initial']['videoFormat'], 'webm')

    def test_hls_vp09_codec_keeps_its_available_resolution(self):
        raw = metadata()
        raw['formats'].append({'ext': 'mp4', 'height': 2160,
                               'vcodec': 'vp09.00.51.08', 'acodec': 'none'})
        source = self.source(raw=raw)
        self.assertEqual(source['initial']['videoFormat'], 'webm')
        self.assertEqual(source['initial']['resolution'], 2160)
        self.assertEqual(source['video_formats'][0]['heights'], [2160, 720])

    def test_rejects_fractional_empty_and_invalid_ranges(self):
        for clips in [[], [{'start': 0.1, 'end': 10}], [{'start': True, 'end': 5}], [{'start': 10, 'end': 10}], [{'start': 0, 'end': 92}], [{'start': -1, 'end': 10}]]:
            with self.subTest(clips=clips), self.assertRaises(ValueError):
                self.source({'clips': clips})

    def test_rejects_silent_setting_changes(self):
        for settings in [{'resolution': 2160}, {'format': 'webm', 'resolution': 1080}, {'content': 'audio', 'resolution': 1080}, {'format': 'auto'}, {'destination': '/tmp'}]:
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                self.source(settings)

    def test_audio_only_source(self):
        raw = metadata()
        raw['formats'] = [raw['formats'][3]]
        s = self.source(raw=raw)
        self.assertEqual(s['available_content'], ['audio'])
        self.assertEqual(s['video_formats'], [])
        self.assertIsNone(s['initial']['resolution'])
        with self.assertRaises(ValueError):
            self.source({'content': 'video'}, raw)

    def test_silent_source(self):
        raw = metadata()
        raw['formats'] = raw['formats'][:2]
        s = self.source(raw=raw)
        self.assertEqual(s['available_content'], ['video'])
        self.assertEqual(s['audio_formats'], [])

    def test_unavailable_or_nonfinite_sources(self):
        for update in [{'entries': []}, {'_type': 'multi_video'}, {'is_live': True}, {'live_status': 'is_upcoming'}, {'duration': None}, {'duration': float('nan')}, {'duration': float('inf')}, {'duration': 0}, {'formats': []}]:
            with self.subTest(update=update), self.assertRaises(ValueError):
                self.source(raw=dict(metadata(), **update))

    def test_ignores_drm_and_storyboards(self):
        raw = metadata()
        for f in raw['formats']:
            if f.get('height'):
                f['has_drm'] = True
        self.assertEqual(self.source(raw=raw)['available_content'], ['audio'])

    def test_no_stream_credentials_and_safe_script_embedding(self):
        raw = metadata()
        raw['title'] = '</script><img src=x onerror=alert(1)>\u2028&'
        source = self.source(raw=raw)
        html = prepare.render(source)
        self.assertNotIn('secret.test', html)
        self.assertNotIn('Cookie', html)
        self.assertNotIn(raw['title'], html)
        self.assertIn('\\u003c/script\\u003e', html)
        self.assertNotIn(prepare.MARKER, html)
        self.assertEqual(len(source['key']), 64)

    def test_unknown_video_codec_gets_explicit_conversion(self):
        raw = metadata()
        raw['formats'] = [{'ext': 'avi', 'height': 480, 'vcodec': 'mpeg4', 'acodec': 'none'}]
        s = self.source(raw=raw)
        self.assertIn('convert', s['video_formats'][0]['label'])
        self.assertEqual(s['initial']['resolution'], 480)

    def test_embedded_credentials_and_unsupported_protocol(self):
        for value in ['https://user:secret@example.org/v', 'ftp://example.org/v', 'https://']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                prepare.location(value)

    def test_local_inspection_excludes_cover_art(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'Local sample.mp3'
            path.write_bytes(b'fixture')
            raw = {'format': {'duration': '5.5'}, 'streams': [
                {'codec_type': 'video', 'codec_name': 'mjpeg', 'height': 1080, 'disposition': {'attached_pic': 1}},
                {'codec_type': 'audio', 'codec_name': 'mp3'}]}
            info = prepare.local_metadata(raw, str(path))
            s = prepare.build_source(info, 'local', str(path))
            self.assertEqual(s['title'], 'Local sample')
            self.assertEqual(s['available_content'], ['audio'])
            self.assertEqual(s['initial']['audioFormat'], 'mp3')
            self.assertIsNone(s['url'])

    def test_cli_offline_render_and_input_protection(self):
        with tempfile.TemporaryDirectory() as tmp:
            info = Path(tmp) / 'metadata.json'
            info.write_text(json.dumps(metadata()))
            output = Path(tmp) / 'controls.html'
            cmd = [sys.executable, str(SKILL / 'scripts' / 'prepare.py'), URL, '--metadata', str(info), '--output', str(output)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'], 'prepared')
            self.assertIn('Fixture Recording', output.read_text())
            original = info.read_bytes()
            result = subprocess.run(cmd[:-1] + [str(info)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(info.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
