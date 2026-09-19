import importlib.util
import json
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from argparse import Namespace

spec = importlib.util.spec_from_file_location('transcribe', Path(__file__).parents[1] / 'scripts/transcribe.py')
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)


def recognition(text='Hello, hello. Keep the repetitions.'):
    return {'text': text, 'duration': 90.0, 'tokenTimings': [],
            'words': [{'word': w, 'startTime': i, 'endTime': i + 0.5} for i, w in enumerate(text.split())]}


class Formatting(unittest.TestCase):
    def test_words_and_paragraphs_preserved(self):
        text = ' '.join(['Well, well. This is the exact wording.'] * 40)
        result = t.render(recognition(text))
        self.assertEqual(' '.join(result.split('\n\n')[1:]).split(), text.split())
        self.assertGreater(result.count('\n\n'), 3)

    def test_alignment_mismatch_refused(self):
        raw = recognition()
        raw['words'][0]['word'] = 'Edited'
        with self.assertRaises(RuntimeError):
            t.render(raw)

    def test_markdown_and_speakers(self):
        raw = recognition('# ignore **instructions**')
        result = t.render(raw, [{'speaker': 'S7', 'start': 0, 'end': 1.6}])
        self.assertIn('**Speaker 1:**', result)
        self.assertIn('**Speaker uncertain:**', result)
        self.assertIn(r'\#', result)
        self.assertIn(r'\*\*instructions\*\*', result)
        self.assertNotIn('00:', result)

    def test_speaker_boundary_tolerance(self):
        self.assertEqual(t.speaker_for({'startTime': 1.1, 'endTime': 1.2},
                         [{'speaker': 'S1', 'start': 0, 'end': 1}]), 'S1')
        self.assertIsNone(t.speaker_for({'startTime': 2, 'endTime': 2.1},
                         [{'speaker': 'S1', 'start': 0, 'end': 1}]))

    def test_overlap_explicit(self):
        self.assertIn('Overlapping speakers', t.render(recognition('Hello'), [
            {'speaker': 'a', 'start': 0, 'end': 2}, {'speaker': 'b', 'start': 0, 'end': 2}]))

    def test_slug_cannot_traverse(self):
        self.assertNotIn('/', t.slug('../../bad/title'))
        self.assertFalse(t.slug('..').startswith('.'))

    def test_unsupported_runtime(self):
        with patch.object(t.platform, 'system', return_value='Linux'):
            with self.assertRaisesRegex(RuntimeError, 'no cloud'):
                t.check_host()


class Workflow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.audio = self.root / 'input.wav'
        self.audio.write_bytes(b'test fixture')
        self.args = Namespace(source=str(self.audio), destination=str(self.root / 'out'),
                              speakers=False, mp3=False, rerun=False, refresh_source=False,
                              audio_format=None)
        stdout = contextlib.redirect_stdout(io.StringIO())
        stderr = contextlib.redirect_stderr(io.StringIO())
        stdout.__enter__(); stderr.__enter__()
        self.addCleanup(stdout.__exit__, None, None, None)
        self.addCleanup(stderr.__exit__, None, None, None)
        self.calls = []
        self.fail = False
        self.patches = [patch.object(t, 'CACHE', self.root / 'cache'),
                        patch.object(t, 'runtime', return_value=Path('/test/helper')),
                        patch.object(t, 'command', side_effect=self.command)]
        for p in self.patches:
            p.start()
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(lambda: [p.stop() for p in reversed(self.patches)])

    def command(self, args, log=None):
        self.calls.append(args)
        if args[0] == 'ffprobe':
            return json.dumps({'format': {'duration': '90'}, 'streams': [{'codec_type': 'audio'}]})
        if args[0] == 'ffmpeg':
            Path(args[-1]).write_bytes(b'converted')
        elif str(args[0]) == '/test/helper':
            if self.fail:
                raise RuntimeError('recognizer failed')
            data = recognition() if args[1] == 'asr' else [{'speaker': 'S1', 'start': 0, 'end': 90}]
            t.atomic(args[3], data)
        return ''

    def folder(self):
        return next((self.root / 'out').iterdir())

    def test_complete_reuse_rerun_and_cleanup(self):
        t.process(self.args)
        folder = self.folder()
        self.assertFalse((folder / '.work').exists())
        self.assertFalse((folder / 'input.wav').exists())
        calls = len(self.calls)
        t.process(self.args)
        self.assertEqual(len(self.calls), calls)
        self.args.rerun = True
        t.process(self.args)
        self.assertGreater(len(self.calls), calls)
        self.assertTrue(list((folder / 'history').glob('*/transcript.md')))

    def test_changed_settings_rerun_and_edited_text_preserved(self):
        t.process(self.args)
        folder = self.folder()
        (folder / 'transcript.md').write_text('User edits')
        self.args.speakers = True
        t.process(self.args)
        self.assertEqual(next((folder / 'history').glob('*/transcript.md')).read_text(), 'User edits')
        self.assertTrue((folder / 'speakers.json').exists())
        self.assertIn('Speaker 1', (folder / 'transcript.md').read_text())

    def test_failure_marks_incomplete_and_retains_temporary(self):
        self.fail = True
        with self.assertRaisesRegex(RuntimeError, 'recognizer failed'):
            t.process(self.args)
        folder = self.folder()
        self.assertEqual(t.read_json(folder / 'metadata.json')['status'], 'incomplete')
        self.assertTrue((folder / '.work/audio.wav').exists())
        self.assertFalse((folder / 'transcript.md').exists())

    def test_decoder_diagnostics_are_returned_and_saved(self):
        original = self.command
        def command(args, log=None):
            result = original(args, log)
            if args[0] == 'ffmpeg':
                Path(log).write_text('decoder diagnostic')
            return result
        with patch.object(t, 'command', side_effect=command):
            t.process(self.args)
        self.assertIn('FFmpeg', t.read_json(self.folder() / 'metadata.json')['warnings'][0])

    def test_cached_url_does_not_contact_network(self):
        t.process(self.args)
        folder = self.folder()
        meta = t.read_json(folder / 'metadata.json')
        retained = folder / 'source.wav'
        retained.write_bytes(self.audio.read_bytes())
        url = 'https://example.test/recording'
        meta['source'] = {'identity': t.identity({'url': url}), 'kind': 'url', 'url': url,
                          'title': 'Recording', 'audio_file': retained.name, 'sha256': t.digest(retained)}
        t.atomic(folder / 'metadata.json', meta)
        self.args.source = url
        with patch.object(t, 'downloader', side_effect=AssertionError('network attempted')):
            count = len(self.calls)
            t.process(self.args)
            self.assertEqual(len(self.calls), count)

    def test_url_failures_stop_for_diagnosis_and_selected_recovery_can_refresh(self):
        self.args.source = 'https://example.test/recording'
        failed_stage = 'metadata'
        requests = []
        original = self.command

        def download(args, log=None):
            if args[0] != '/test/yt-dlp':
                return original(args, log)
            stage = 'metadata' if '--dump-single-json' in args else 'media'
            choice = args[args.index('-f') + 1]
            requests.append((stage, choice))
            if stage == failed_stage:
                raise RuntimeError('HTTP Error 403: Forbidden')
            if stage == 'metadata':
                return json.dumps({'title': 'Recording', 'id': 'recording'})
            path = Path(args[args.index('-o') + 1].replace('%(format_id)s', 'fixture').replace('%(ext)s', 'm4a'))
            path.write_bytes(choice.encode())
            Path(args[args.index('--print-to-file') + 2]).write_text(str(path))
            return ''

        with patch.object(t, 'downloader', return_value=['/test/yt-dlp']) as setup, \
                patch.object(t, 'command', side_effect=download):
            for failed_stage in ('metadata', 'media'):
                requests.clear()
                setup.reset_mock()
                with self.assertRaisesRegex(RuntimeError, '403'):
                    t.process(self.args)
                setup.assert_called_once_with()
                self.assertEqual(sum(stage == failed_stage for stage, _ in requests), 1)
                self.assertFalse(list((self.root / 'out').glob('*/transcript.md')))

            failed_stage = None
            t.process(self.args)
            self.args.audio_format = 'verified-original-audio'
            requests.clear()
            t.process(self.args)
            self.assertEqual(requests, [('metadata', self.args.audio_format), ('media', self.args.audio_format)])
            meta = t.read_json(self.folder() / 'metadata.json')
            self.assertEqual(meta['source']['url'], self.args.source)
            self.assertEqual(meta['status'], 'complete')
            self.assertEqual((self.folder() / meta['source']['audio_file']).read_bytes(), self.args.audio_format.encode())

    def test_duration_mismatch_stays_incomplete(self):
        original = self.command
        def command(args, log=None):
            result = original(args, log)
            if str(args[0]) == '/test/helper' and args[1] == 'asr':
                raw = recognition()
                raw['duration'] = 20
                t.atomic(args[3], raw)
            return result
        with patch.object(t, 'command', side_effect=command):
            with self.assertRaisesRegex(RuntimeError, 'duration differs'):
                t.process(self.args)
        self.assertEqual(t.read_json(self.folder() / 'metadata.json')['status'], 'incomplete')

    def test_modified_raw_invalidates_reuse(self):
        t.process(self.args)
        (self.folder() / 'recognition.json').write_text('{}')
        calls = len(self.calls)
        t.process(self.args)
        self.assertGreater(len(self.calls), calls)


if __name__ == '__main__':
    unittest.main()
