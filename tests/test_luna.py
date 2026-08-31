from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from luna.scanner import Track, scan_library
from luna.filenames import sanitize_component
from luna.normalize import normalize_text, normalize_track_number
from luna.planner import build_rename_plan, validate_plan
from luna.duplicates import find_probable_duplicates
from luna.safety import safe_component
from luna.config import LibraryProfile, save_config, load_config
from luna import cli

class LunaTests(unittest.TestCase):
    def test_scanner_is_recursive_and_ignores_unsupported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'nested').mkdir(); (root/'a.mp3').write_bytes(b'not-real-audio'); (root/'nested'/'b.flac').write_bytes(b'x'); (root/'note.txt').write_text('x')
            tracks=scan_library(root,workers=1)
            self.assertEqual([p.name for p in (t.path for t in tracks)],['a.mp3','b.flac']); self.assertTrue(all(t.metadata_error for t in tracks))
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
            groups=find_probable_duplicates(tracks); self.assertEqual(len(groups),1); self.assertEqual(groups[0].confidence,.95); self.assertTrue(a.exists() and b.exists())
    def test_profile_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'config.json'; profile=LibraryProfile(['Music'],['.mp3'],['Music/cache'],2); save_config(profile,path); self.assertEqual(load_config(path),profile)
    def test_scan_skips_unrelated_analysis(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with patch.object(cli, 'load_tracks', return_value=[]), \
                 patch.object(cli, 'validate_library', side_effect=AssertionError('validation should run for scan')), \
                 patch.object(cli, 'find_duplicates', side_effect=AssertionError('duplicates should not run for scan')), \
                 patch.object(cli, 'find_probable_duplicates', side_effect=AssertionError('probable duplicates should not run for scan')), \
                 patch.object(cli, 'audit_artwork', side_effect=AssertionError('artwork audit should not run for scan')), \
                 patch.object(cli, 'build_rename_plan', side_effect=AssertionError('rename planning should not run for scan')):
                cli.main(['scan', str(root)])

if __name__=='__main__': unittest.main()
