"""B grouping/resource/source-bound evidence regressions; optional native runtime."""
from dataclasses import replace
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
HAS_RUNTIME = bool(importlib.util.find_spec("av") and importlib.util.find_spec("numpy"))
if HAS_RUNTIME:
    import av
    import numpy as np
    from bscout.corpus import make_frame
    from bscout.common import sha256
    from bscout.regional import RegionalConfig, TileSignals, BudgetExceeded, scan
    from bscout.ledger import validate_traversal, recover


@unittest.skipUnless(HAS_RUNTIME,"Checkpoint B tests require pinned av/numpy")
class RegionalTests(unittest.TestCase):
    def frame(self,index,panels=(),chroma=None):
        planes = [np.full((64,64),40,np.uint8),np.full((32,32),128,np.uint8),np.full((32,32),128,np.uint8)]
        for x,y,w,h,value in panels:
            planes[0][y:y+h,x:x+w] = value
        if chroma is not None:
            planes[1][8:16,8:16] = chroma
        f = make_frame(planes)
        f.pts,f.time_base = index,Fraction(1,60)
        return f

    def intervals(self,frames):
        state = TileSignals()
        rows = []
        for index,frame in enumerate(frames):
            closed,raw = state.observe(frame,index)
            rows.extend(closed)
            self.assertEqual(len(raw),16)
        return rows+state.finish()

    def test_one_frame_start_end_and_phase_are_preserved(self):
        for onset in (0,1,7,8,15):
            fs = [self.frame(i,[(16,16,16,16,220)] if i==onset else []) for i in range(16)]
            candidates = self.intervals(fs)
            actual = [r for r in candidates if r["region_xywh"]==[16,16,16,16] and r["start_position"]==onset and r["trigger"]!="structural_inspection"]
            self.assertEqual(len(actual),1)
            self.assertEqual(actual[0]["end_position_exclusive"],onset+1)
            self.assertEqual(actual[0]["evidence_positions"],[onset])

    def test_replacement_and_identical_reopen_are_separate_occurrences(self):
        values = [40,220,220,110,40,40,220,40]
        rows = self.intervals([self.frame(i,[(16,16,16,16,v)]) for i,v in enumerate(values)])
        tile = [r for r in rows if r["region_xywh"]==[16,16,16,16] and r["trigger"]!="structural_inspection"]
        a = next(r for r in tile if r["start_position"]==1)
        b = next(r for r in tile if r["start_position"]==3)
        reopened = next(r for r in tile if r["start_position"]==6)
        self.assertEqual((a["end_position_exclusive"],b["end_position_exclusive"]),(3,4))
        self.assertNotEqual(a["id"],reopened["id"])
        self.assertGreater(reopened["occurrence"],a["occurrence"])
        self.assertEqual(reopened["evidence_positions"],[6])

    def test_hud_overlap_activates_existing_and_new_tiles(self):
        fs = [self.frame(i,[(0,16,32,16,150)]+([(16,16,32,32,220)] if i==2 else [])) for i in range(5)]
        rows = self.intervals(fs)
        for region in ([16,16,16,16],[32,16,16,16],[16,32,16,16]):
            self.assertTrue(any(r["region_xywh"]==region and r["start_position"]==2 and 2 in r["evidence_positions"] for r in rows))
        self.assertTrue(any(r["region_xywh"]==[0,16,16,16] and r["start_position"]==0 for r in rows))

    def test_accumulated_fade_and_chroma_are_not_only_consecutive_deltas(self):
        state = TileSignals(replace(RegionalConfig(),bright_luma=240,short_delta=100,stable_delta=25,reference_alpha=0.01))
        rows = []
        for i in range(12):
            closed,raw = state.observe(self.frame(i,[(16,16,16,16,40+i*4)]),i)
            rows.extend(closed)
        rows += state.finish()
        self.assertTrue(any(r["region_xywh"]==[16,16,16,16] and r["raw_signals"]["stable_luma_delta"]>=25 for r in rows))
        rows = self.intervals([self.frame(i,chroma=200 if i==1 else 128) for i in range(3)])
        self.assertTrue(any(r["start_position"]==1 and r["raw_signals"]["stable_chroma_delta"]>=18 for r in rows))

    def test_scale_mapping_and_edge_tile_clipping(self):
        f = make_frame([np.full((66,70),220,np.uint8),np.full((33,35),128,np.uint8),np.full((33,35),128,np.uint8)])
        state = TileSignals();state.observe(f,0)
        rows = state.finish()
        self.assertTrue(any(r["region_xywh"]==[64,64,6,2] for r in rows))

    def test_no_frame_gaps_and_pixel_budget_no_fallback(self):
        state = TileSignals()
        with self.assertRaisesRegex(ValueError,"contiguous"):
            state.observe(self.frame(0),1)
        state = TileSignals(replace(RegionalConfig(),max_analysis_pixels=1))
        with self.assertRaises(BudgetExceeded):
            state.observe(self.frame(0),0)

    def test_live_tile_state_bounded_while_occurrence_count_grows(self):
        state = TileSignals()
        emitted = 0
        for i in range(1000):
            rows,_ = state.observe(self.frame(i,[(16,16,16,16,220 if i%2 else 40)]),i)
            emitted += len(rows)
            self.assertLessEqual(len(state.tracks),16)
            self.assertLessEqual(len(state.occurrences),16)
        self.assertGreater(emitted,900)
        self.assertLess(state.max_state_bytes,200000)

    def test_structural_windows_localize_uninterrupted_visual_runs_without_new_occurrences(self):
        rows = self.intervals([self.frame(i,[(16,16,16,16,220)]) for i in range(8)])
        tile = [r for r in rows if r["region_xywh"]==[16,16,16,16]]
        track = next(r for r in tile if r["trigger"]=="initial_structure")
        windows = [r for r in tile if r["trigger"]=="structural_inspection"]
        self.assertTrue(any(r["start_position"]==0 and r["end_position_exclusive"]==3 for r in windows))
        self.assertTrue(any(r["start_position"]==3 and r["end_position_exclusive"]==8 for r in windows))
        self.assertTrue(all(r["occurrence"]==track["occurrence"] and r["observation_of"]==track["id"] for r in windows))

    def encode(self,path):
        with av.open(str(path),"w") as output:
            stream = output.add_stream("libx264",rate=60)
            stream.width=stream.height=64;stream.pix_fmt="yuv420p"
            stream.codec_context.thread_count=1
            stream.options={"crf":"18","x264-params":"keyint=4:min-keyint=4:bframes=2:b-adapt=0:scenecut=0:threads=1"}
            for i in range(8):
                frame = self.frame(i,[(16,16,16,16,220)] if i in (1,7) else [])
                for packet in stream.encode(frame):output.mux(packet)
            for packet in stream.encode():output.mux(packet)

    def test_real_seek_evidence_unicode_no_audio_source_unchanged(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/"synthetic space \u03b4.mp4";self.encode(source)
            before=sha256(source)
            out=Path(d)/"evidence \u03b4"
            result=scan(source,out)
            self.assertEqual(result["status"],"complete")
            self.assertEqual(result["scanned_frames"],8)
            self.assertEqual(result["validation_traversals"],1)
            self.assertEqual(sha256(source),before)
            evidence=[json.loads(x) for x in (out/"evidence.jsonl").read_text().splitlines()]
            self.assertTrue({1,7}.issubset({r["position"] for r in evidence}))
            for r in evidence:
                self.assertTrue(r["verified"] and r["recovery"]["backward"])
                self.assertEqual(r["recovery"]["target_position"],r["position"])
                self.assertEqual(r["native_sha256"],r["recovery"]["sha256"])
                for asset in r["assets"]:
                    self.assertEqual(sha256(out/asset["path"]),asset["sha256"])
            self.assertFalse(list(Path(d).glob(".bscout-b-*")))

    def test_spool_and_evidence_budget_explicit_partial_no_complete(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/"source.mp4";self.encode(source)
            for index,config in enumerate((replace(RegionalConfig(),max_spool_bytes=1),replace(RegionalConfig(),max_evidence_bytes=1))):
                result=scan(source,Path(d)/str(index),config)
                self.assertNotEqual(result["status"],"complete")
                self.assertTrue(result["errors"])
                self.assertEqual(result["evidence_count"],0)
                self.assertTrue(result["source_unchanged"])

    def test_traversal_storage_budget_cannot_create_prefix_authority(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/"source.mp4";self.encode(source)
            with validate_traversal(source,max_storage_bytes=1) as vt:
                self.assertFalse(vt.trailer["decode_eof"])
                self.assertNotEqual(vt.trailer["status"],"complete")
                with self.assertRaisesRegex(ValueError,"unsupported"):
                    recover(source,vt,vt.identity(0))

    def test_source_mutation_after_seek_cannot_publish_complete(self):
        from bscout.regional import recover as original_recover
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/"source.mp4";self.encode(source)
            def mutate(*args,**kwargs):
                result=original_recover(*args,**kwargs)
                with source.open("ab") as sink:sink.write(b"synthetic mutation")
                return result
            with patch("bscout.regional.recover",side_effect=mutate):
                result=scan(source,Path(d)/"out")
            self.assertEqual(result["status"],"failed")
            self.assertFalse(result["source_unchanged"])
            self.assertTrue(result["errors"])

    def test_dropped_l0_frame_rejects_native_alignment_and_reports_gap(self):
        from bscout.regional import presented as original_presented
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/"source.mp4";self.encode(source)
            def skip(container,stream):
                for position,frame in enumerate(original_presented(container,stream)):
                    if position!=3:yield frame
            with patch("bscout.regional.presented",side_effect=skip):
                result=scan(source,Path(d)/"out")
            self.assertEqual(result["decoded_frames"],8)
            self.assertEqual(result["scanned_frames"],3)
            self.assertEqual(result["status"],"partial")
            self.assertFalse(result["scan_eof"])
            self.assertTrue(any("differs from validated" in e for e in result["errors"]))

    def test_cli_candidates_complete_vs_failed_and_configuration_drift(self):
        from contextlib import redirect_stdout,redirect_stderr
        from dataclasses import asdict
        import io
        from bscout.cli import main
        from bscout.common import canonical
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/"source.mp4";self.encode(source)
            output=Path(d)/"out"
            with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
                rc=main(["candidates",str(source),"--out",str(output)])
            self.assertEqual(rc,0)
            config=Path(d)/"bad-config.json"
            config.write_bytes(canonical({"configuration":asdict(RegionalConfig()),"configuration_sha256":"0"*64}))
            with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
                rc=main(["candidates",str(source),"--out",str(Path(d)/"bad"),"--config",str(config)])
            self.assertEqual(rc,2)
            self.assertFalse((Path(d)/"bad").exists())

    def test_publication_failure_removes_owned_output(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/"source.mp4";self.encode(source)
            with patch("bscout.regional.os.rename",side_effect=OSError("synthetic publication failure")):
                with self.assertRaisesRegex(ValueError,"publication failure"):scan(source,Path(d)/"out")
            self.assertFalse((Path(d)/"out").exists())
            self.assertFalse(list(Path(d).glob(".bscout-b-*")))

    def test_unsupported_media_and_output_alias_fail_honestly(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/"unsupported.mp4";source.write_bytes(b"synthetic unsupported input")
            result=scan(source,Path(d)/"out")
            self.assertEqual(result["status"],"failed")
            self.assertEqual(result["scanned_frames"],0)
            self.assertTrue(result["source_unchanged"])
            with self.assertRaises(ValueError):scan(source,source)
