from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from mutagen import MutagenError
from luna.scanner import Track, scan_library, inspect_file
from luna.filenames import sanitize_component
from luna.normalize import normalize_text, normalize_track_number
from luna.planner import build_rename_plan, validate_plan
from luna.duplicates import find_probable_duplicates, probable_duplicate_score
from luna.safety import safe_component
from luna.config import LibraryProfile, save_config, load_config
from luna.index import LibraryIndex
from luna import cli

class LunaTests(unittest.TestCase):
    def test_scanner_is_recursive_and_ignores_unsupported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'nested').mkdir(); (root/'a.mp3').write_bytes(b'not-real-audio'); (root/'nested'/'b.flac').write_bytes(b'x'); (root/'note.txt').write_text('x')
            index=LibraryIndex(root/'index.sqlite3')
            try:
                tracks=scan_library(root,workers=1,index=index)
            finally:
                index.close()
            self.assertEqual([p.name for p in (t.path for t in tracks)],['a.mp3','b.flac']); self.assertTrue(all(t.metadata_error for t in tracks))
    def test_scanner_handles_expected_mutagen_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'broken.mp3'; path.write_bytes(b'broken')
            with patch('luna.scanner.File', side_effect=MutagenError('invalid audio')):
                track=inspect_file(path)
            self.assertEqual(track.metadata_error,'invalid audio')
    def test_scanner_does_not_swallow_unexpected_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'broken.mp3'; path.write_bytes(b'broken')
            with patch('luna.scanner.File', side_effect=RuntimeError('programming failure')):
                with self.assertRaises(RuntimeError):
                    inspect_file(path)
    def test_index_reuses_unchanged_track_without_reparsing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); path=root/'song.mp3'; path.write_bytes(b'not-real-audio'); index=LibraryIndex(root/'index.sqlite3')
            try:
                first=scan_library(root,workers=1,index=index)
                self.assertTrue(first[0].metadata_error)
                with patch('luna.scanner.inspect_file', side_effect=AssertionError('unchanged file should be served from the index')):
                    second=scan_library(root,workers=1,index=index)
                self.assertEqual(second[0].path, path)
                self.assertEqual(second[0].size, first[0].size)
            finally:
                index.close()
    def test_normalization_preserves_unicode_and_numbers(self):
        self.assertEqual(normalize_text('  Björk   |  Vespertine  '),'Björk | Vespertine'); self.assertEqual(normalize_track_number('03/12'),3)
    def test_cross_platform_reserved_names(self):
        self.assertEqual(sanitize_component('CON'),'_CON'); self.assertEqual(safe_component('a:b'),'a-b')
    def test_rename_plan_is_dry_run_and_collision_aware(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); a=root/'old.mp3'; b=root/'01 - Artist - Song.mp3'; a.write_bytes(b'a'); b.write_bytes(b'b'); track=Track(a,'Song','Artist','Album',1)
            plan=build_rename_plan([track]); self.assertEqual(plan[0].status,'blocked'); self.assertTrue(a.exists()); self.assertTrue(validate_plan(plan)==[])
    def test_probable_duplicates_never_delete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); a=root/'one.mp3'; b=root/'renamed.flac'; a.write_bytes(b'abc'); b.write_bytes(b'abc'); tracks=[Track(a,'Song','Artist','Album',1,size=3),Track(b,'Song','Artist','Album',1,size=3)]
            groups=find_probable_duplicates(tracks); self.assertEqual(len(groups),1); self.assertEqual(groups[0].confidence,.95); self.assertIn('artist matches',groups[0].reasons); self.assertIn('title matches',groups[0].reasons); self.assertTrue(a.exists() and b.exists())
    def test_probable_duplicate_score_is_explainable_and_multi_signal(self):
        first=Track(Path('one.mp3'),'Song','Artist','Album',1,size=100,year='2020')
        second=Track(Path('two.mp3'),'Song','Artist','Other Album',2,size=101,year='2021')
        confidence,reasons=probable_duplicate_score(first,second)
        self.assertEqual(confidence,.60)
        self.assertEqual(reasons,('artist matches','title matches'))
    def test_profile_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'config.json'; profile=LibraryProfile(['Music'],['.mp3'],['Music/cache'],2); save_config(profile,path); self.assertEqual(load_config(path),profile)
    def test_artwork_plan_skips_unrelated_analysis(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with patch.object(cli, 'load_tracks', return_value=[]), \
                 patch.object(cli, 'validate_library', side_effect=AssertionError('validation should not run for artwork-plan')), \
                 patch.object(cli, 'find_duplicates', side_effect=AssertionError('duplicates should not run for artwork-plan')), \
                 patch.object(cli, 'find_probable_duplicates', side_effect=AssertionError('probable duplicates should not run for artwork-plan')), \
                 patch.object(cli, 'audit_artwork', side_effect=AssertionError('artwork audit should not run for artwork-plan')), \
                 patch.object(cli, 'build_rename_plan', side_effect=AssertionError('rename planning should not run for artwork-plan')):
                cli.main(['artwork-plan', str(root)])

if __name__=='__main__': unittest.main()
