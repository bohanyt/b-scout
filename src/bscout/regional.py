"""Checkpoint B: bounded native tile signals and source-bound retained evidence.

This is a classical-CV baseline, not text/UI recognition or a production packet.
The detector receives decoded planes only, never corpus truth or harness geometry.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
import json
import math
import os
from pathlib import Path
import shutil
import sqlite3
import struct
import tempfile
import time
import zlib

import numpy as np

from .common import canonical, digest, fraction, peak_rss, safe_output, sha256
from .frames import native_digest, native_planes
from .ledger import DecodeConfig, presented, public_error, recover, select_video, validate_traversal, verify_source

VERSION = "bscout-regional-v1"


@dataclass(frozen=True, slots=True)
class RegionalConfig:
    version: str = VERSION
    analysis_step: int = 2
    tile_size: int = 8
    bright_luma: float = 100.0
    bright_fraction: float = 0.6
    short_delta: float = 64.0
    stable_delta: float = 64.0
    chroma_delta: float = 18.0
    replacement_delta: float = 24.0
    reference_alpha: float = 0.08
    inspection_lengths: str = "1,3,5"
    max_analysis_pixels: int = 1048576
    max_live_tiles: int = 16384
    max_spool_bytes: int = 268435456
    max_evidence_bytes: int = 268435456
    max_diagnostic_bytes: int = 65536

    def __post_init__(self):
        if self.version != VERSION or self.analysis_step != 2:
            raise ValueError("Unsupported regional version/analysis scale")
        if self.inspection_lengths != "1,3,5":
            raise ValueError("Unsupported structural inspection windows")
        for name in ("tile_size", "max_analysis_pixels", "max_live_tiles", "max_spool_bytes", "max_evidence_bytes", "max_diagnostic_bytes"):
            if type(getattr(self, name)) is not int or getattr(self, name) <= 0:
                raise ValueError("Invalid regional integer budget/geometry")
        for name in ("bright_luma", "bright_fraction", "short_delta", "stable_delta", "chroma_delta", "replacement_delta", "reference_alpha"):
            value = getattr(self, name)
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise ValueError("Invalid regional threshold")
        if self.bright_fraction > 1 or self.reference_alpha > 1:
            raise ValueError("Invalid regional fraction")

    @property
    def sha256(self):
        return digest(asdict(self))


def load_config(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    config = RegionalConfig(**data.get("configuration", data))
    if "configuration_sha256" in data and data["configuration_sha256"] != config.sha256:
        raise ValueError("Regional configuration hash differs from effective configuration")
    return config


class BudgetExceeded(ValueError):
    pass


class TileSignals:
    """Three current/previous/reference planes plus O(tile count) live tracks.

    Native 2x2 luma box means and native U/V samples have exact source mapping.
    No skipped frames or corpus-specific exclusions. EMA updates only inactive
    tiles; active references stay fixed, so accumulated fades remain visible.
    """
    def __init__(self, config=RegionalConfig()):
        self.config = config
        self.previous = self.reference = None
        self.shape = None
        self.tracks = {}
        self.occurrences = {}
        self.position = -1
        self.next_id = 0
        self.max_state_bytes = 0

    def _means(self, plane):
        h,w = plane.shape
        t = self.config.tile_size
        rows,cols = (h+t-1)//t,(w+t-1)//t
        padded = np.pad(plane,((0,rows*t-h),(0,cols*t-w)),constant_values=0)
        counts = np.minimum(t,h-np.arange(rows)*t)[:,None]*np.minimum(t,w-np.arange(cols)*t)[None,:]
        return (padded.reshape(rows,t,cols,t).sum(axis=(1,3))/counts).ravel()

    def _finish(self, key, end, reason):
        track = self.tracks.pop(key)
        first, last = track["start_position"], end-1
        track.update(end_position_exclusive=end, evidence_positions=sorted({first,last}), close_reason=reason)
        return track

    def observe(self, frame, position):
        if position != self.position + 1:
            raise ValueError("L0 requires every contiguous presentation position")
        if frame.format.name != "yuv420p" or frame.width % 2 or frame.height % 2:
            raise ValueError("B baseline requires even-sized native yuv420p")
        h, w = frame.height//2, frame.width//2
        if h*w > self.config.max_analysis_pixels:
            raise BudgetExceeded("Analysis pixel budget exhausted; no frame downsampling fallback")
        if ((h+self.config.tile_size-1)//self.config.tile_size)*((w+self.config.tile_size-1)//self.config.tile_size) > self.config.max_live_tiles:
            raise BudgetExceeded("Live tile budget exhausted; no silent region masking")
        if self.shape is not None and self.shape != (frame.height,frame.width):
            raise ValueError("B baseline does not support changing source dimensions")
        self.shape = frame.height, frame.width
        arrays, _ = native_planes(frame)
        y = arrays[0].astype(np.float32).reshape(h,2,w,2).mean(axis=(1,3))
        current = np.stack([y, arrays[1].astype(np.float32), arrays[2].astype(np.float32)])
        if self.previous is None:
            self.previous = current.copy()
            self.reference = current.copy()
        short = np.abs(current-self.previous)
        stable = current-self.reference
        means = [self._means(p) for p in current]
        bright_values = self._means(current[0] > self.config.bright_luma)
        sd_values,ld_values = self._means(short[0]),self._means(stable[0])
        cd_values = np.maximum(self._means(np.abs(stable[1])),self._means(np.abs(stable[2])))
        active_values = ((bright_values >= self.config.bright_fraction) | (sd_values >= self.config.short_delta)
                         | (ld_values >= self.config.stable_delta) | (cd_values >= self.config.chroma_delta))
        replacements = np.zeros(len(active_values),dtype=np.uint8)
        closed = []
        tile_cols = (w+self.config.tile_size-1)//self.config.tile_size
        for key,(mean,um,vm,bright,sd,ld,cd,active) in enumerate(zip(*means,bright_values,sd_values,ld_values,cd_values,active_values)):
            mean,bright,sd,ld,cd = map(float,(mean,bright,sd,ld,cd))
            signature = [mean,float(um),float(vm)]
            # Positive persistent structure and accumulated/local changes are
            # independent triggers. Darkness/removal can be a noisy short cue.
            prior = self.tracks.get(key)
            replacement = prior is not None and max(abs(a-b) for a,b in zip(signature,prior["signature"])) >= self.config.replacement_delta
            replacements[key] = int(replacement)
            if prior is not None and (not active or replacement):
                closed.append(self._finish(key,position,"content_change" if replacement else "absence"))
                prior = None
            if active and prior is None:
                row, col = divmod(key,tile_cols)
                x, top = col*self.config.tile_size*2, row*self.config.tile_size*2
                region = [x,top,min(self.config.tile_size*2,frame.width-x),min(self.config.tile_size*2,frame.height-top)]
                self.next_id += 1
                self.occurrences[key] = self.occurrences.get(key,0)+1
                prior = dict(id=f"candidate-{self.next_id:08d}", tile=key, occurrence=self.occurrences[key],
                             region_xywh=region,start_position=position,signature=signature,
                             raw_signals=dict(luma_mean=mean,bright_fraction=bright,short_luma_delta=sd,stable_luma_delta=ld,stable_chroma_delta=cd),
                             trigger="initial_structure" if position==0 else "regional_change")
                self.tracks[key] = prior
            if active and (bright >= self.config.bright_fraction or cd >= self.config.chroma_delta):
                # Independent short structural observations do not assert a new
                # appearance/content boundary. They remain useful inside long
                # unchanged visual runs and never consult annotation schedules.
                for length in (1,3,5):
                    first = position-length+1
                    if first >= prior["start_position"]:
                        self.next_id += 1
                        closed.append(dict(id=f"candidate-{self.next_id:08d}",tile=key,occurrence=prior["occurrence"],
                                           observation_of=prior["id"],region_xywh=prior["region_xywh"],
                                           start_position=first,end_position_exclusive=position+1,
                                           evidence_positions=sorted({first,position}),
                                           trigger="structural_inspection",close_reason="fixed_observation_window",
                                           raw_signals=dict(luma_mean=mean,bright_fraction=bright,short_luma_delta=sd,stable_luma_delta=ld,stable_chroma_delta=cd)))
        inactive = ~np.repeat(np.repeat(active_values.reshape(-1,tile_cols),self.config.tile_size,axis=0),self.config.tile_size,axis=1)[:h,:w]
        self.reference[:,inactive] += self.config.reference_alpha*(current[:,inactive]-self.reference[:,inactive])
        metrics = np.column_stack((means[0],bright_values,sd_values,ld_values,cd_values,active_values,replacements))
        diagnostics = np.round(metrics,4).tolist()
        self.previous = current
        self.position = position
        self.max_state_bytes = max(self.max_state_bytes,7*current.nbytes+len(self.tracks)*4096+len(self.occurrences)*32)
        return closed, diagnostics

    def finish(self):
        return [self._finish(key,self.position+1,"eof") for key in list(self.tracks)]


def _pgm(frame):
    y = native_planes(frame)[0][0]
    return f"P5\n{frame.width} {frame.height}\n255\n".encode("ascii") + y.tobytes()


def _luma_png(frame):
    """Lossless grayscale preview of native luma; no RGB identity conversion."""
    y = native_planes(frame)[0][0]
    def chunk(kind,data):
        return struct.pack(">I",len(data))+kind+data+struct.pack(">I",zlib.crc32(kind+data)&0xffffffff)
    header = struct.pack(">IIBBBBB",frame.width,frame.height,8,0,0,0,0)
    scanlines = np.zeros((frame.height,frame.width+1),np.uint8)
    scanlines[:,1:] = y
    return b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",header)+chunk(b"IDAT",zlib.compress(scanlines.tobytes(),3))+chunk(b"IEND",b"")


def scan(source, output, config=RegionalConfig(), decode_config=DecodeConfig()):
    """Validate once, aligned every-frame L0 pass, then exact evidence seeks.

    Metadata is streamed to disk; selected positions are deduplicated in SQLite.
    An incomplete validation still receives L0 diagnostic coverage where it can
    be decoded, but cannot publish verified retained evidence or complete B.
    """
    import av
    if config is None:
        config = RegionalConfig()
    if type(config) is not RegionalConfig or type(decode_config) is not DecodeConfig:
        raise ValueError("Expected immutable B/decode configurations")
    source, output = Path(source).resolve(), Path(output)
    safe_output(source,output)
    if source.is_relative_to(output.resolve()):
        raise ValueError("Source cannot be contained in B output")
    original = sha256(source)
    output.parent.mkdir(parents=True,exist_ok=True)
    pending = Path(tempfile.mkdtemp(prefix=".bscout-b-",dir=output.parent))
    started = time.perf_counter()
    vt = db = None
    scanned = candidates_count = evidence_count = evidence_bytes = spool_bytes = 0
    errors, status, eof = [], "failed", False
    validation = None
    table_bytes = 0
    vt_directory = None
    peak_spool_bytes = peak_owned_bytes = 0
    tracker = TileSignals(config)
    def check_spool():
        nonlocal spool_bytes, peak_spool_bytes, peak_owned_bytes
        spool_bytes = sum(p.stat().st_size for p in pending.iterdir() if p.is_file())
        if db is not None:
            allocated = db.execute("PRAGMA page_count").fetchone()[0]*db.execute("PRAGMA page_size").fetchone()[0]
            spool_bytes += max(0,allocated-(pending/"queue.sqlite").stat().st_size)
        if vt_directory is not None and vt_directory.exists():
            spool_bytes += sum(p.stat().st_size for p in vt_directory.iterdir() if p.is_file())
        peak_spool_bytes = max(peak_spool_bytes,spool_bytes)
        peak_owned_bytes = max(peak_owned_bytes,spool_bytes+evidence_bytes)
        if spool_bytes > config.max_spool_bytes:
            raise BudgetExceeded("B spool budget exhausted; explicit partial run")
    try:
        vt = validate_traversal(source,decode_config,ledger_out=pending/"ledger.jsonl",max_storage_bytes=config.max_spool_bytes)
        header, trailer = vt.header, vt.trailer
        validation, table_bytes = trailer, vt.table_bytes
        vt_directory = vt.temporary_directory
        check_spool()
        if header is None:
            raise ValueError("Source validation failed before first frame")
        if not trailer["decode_eof"]:
            raise ValueError("Incomplete validation; L0 must not treat a prefix as the full source")
        resolved = DecodeConfig(stream_index=header["selected_stream_index"])
        db = sqlite3.connect(pending/"queue.sqlite")
        db.execute("PRAGMA cache_size=-256")
        db.execute("CREATE TABLE evidence(position INTEGER PRIMARY KEY)")
        db.execute("CREATE TABLE candidates(id TEXT PRIMARY KEY,row TEXT)")
        check_spool()
        def candidate(row,sink):
            nonlocal candidates_count
            start, end = row["start_position"],row["end_position_exclusive"]
            row["start"] = {k:vt.entry(start)[k] for k in ("identity","pts","time_base","ordinal")}
            row["end_exclusive"] = ({k:vt.entry(end)[k] for k in ("identity","pts","time_base","ordinal")}
                                    if end < trailer["presented_frames"] else {"ordinal":end,"identity":None,"pts":None,"time_base":header["first_presented_time_base"],"reason":"end_of_traversal; duration separately decoder-reported"})
            data = canonical(row)
            sink.write(data)
            db.execute("INSERT INTO candidates VALUES (?,?)",(row["id"],data.decode()))
            for position in row["evidence_positions"]:
                db.execute("INSERT OR IGNORE INTO evidence VALUES (?)",(position,))
            candidates_count += 1
            if candidates_count % 128 == 0:
                sink.flush()
                check_spool()
        with (pending/"candidates.jsonl").open("xb") as cs, (pending/"signals.jsonl").open("xb") as signals:
            signals.write(canonical(dict(type="header",version=VERSION,configuration=asdict(config),configuration_sha256=config.sha256,
                                         tile_metric_order=["luma_mean","bright_fraction","short_luma_delta","stable_luma_delta","stable_chroma_delta","active","replacement"],
                                         source_mapping="analysis 2x2 native luma box mean; U/V native samples; tile coordinates multiplied by 2; edge tiles clipped")))
            try:
                with av.open(str(source),options=dict(resolved.demux_options)) as container:
                    stream = select_video(container,resolved.stream_index,resolved)
                    for frame in presented(container,stream):
                        expected = vt.entry(scanned)
                        actual_digest, domain = native_digest(frame)
                        actual = dict(pts=frame.pts,time_base=fraction(frame.time_base),key_frame=bool(frame.key_frame),width=frame.width,height=frame.height,pix_fmt=frame.format.name,native_sha256=actual_digest,digest_domain=domain)
                        if canonical(actual) != canonical({k:expected[k] for k in actual}):
                            raise ValueError("B scan differs from validated native traversal")
                        finished, raw = tracker.observe(frame,scanned)
                        signals.write(canonical(dict(type="frame",position=scanned,identity=expected["identity"],pts=expected["pts"],time_base=expected["time_base"],tiles=raw)))
                        scanned += 1
                        for row in finished:
                            candidate(row,cs)
                        cs.flush(); signals.flush(); db.commit(); check_spool()
                eof = True
                if scanned != trailer["presented_frames"]:
                    raise ValueError("B scanned count differs from validated traversal")
                for row in tracker.finish():
                    candidate(row,cs)
                cs.flush(); signals.flush(); db.commit(); check_spool()
                verify_source(vt,source)
                status = "complete" if trailer["status"] == "complete" else "partial"
                if status != "complete":
                    errors.append("Exact retained evidence unsupported by diagnostic/incomplete A traversal")
            except Exception as exc:
                errors.append(public_error(exc,source,pending,output))
                status = "partial" if scanned else "failed"
        if status == "complete":
            check_spool()
            assets = pending/"assets"
            assets.mkdir()
            with (pending/"evidence.jsonl").open("xb") as es:
                for (position,) in db.execute("SELECT position FROM evidence ORDER BY position"):
                    expected = vt.entry(position)
                    frame, proof = recover(source,vt,expected["identity"],config=resolved)
                    if proof["sha256"] != expected["native_sha256"] or proof["target_position"] != position:
                        raise ValueError("B evidence target differs from traversal")
                    native = b"".join(p.tobytes() for p in native_planes(frame)[0])
                    pgm = _pgm(frame)
                    png = _luma_png(frame)
                    if evidence_bytes+len(native)+len(pgm)+len(png) > config.max_evidence_bytes:
                        raise BudgetExceeded("B retained-evidence budget exhausted; explicit partial run")
                    items = []
                    for kind,extension,data in (("native_planes","yuv",native),("native_luma_preview","pgm",pgm),("native_luma_png","png",png)):
                        name = f"frame-{position:08d}.{extension}"
                        path = assets/name
                        with path.open("xb") as sink:
                            sink.write(data)
                        items.append(dict(path=f"assets/{name}",kind=kind,bytes=len(data),sha256=sha256(path)))
                    es.write(canonical(dict(position=position,identity=expected["identity"],native_sha256=expected["native_sha256"],digest_domain=expected["digest_domain"],verified=True,assets=items,recovery=proof)))
                    es.flush()
                    evidence_count += 1
                    evidence_bytes += len(native)+len(pgm)+len(png)
                    check_spool()
        else:
            (pending/"evidence.jsonl").touch()
        verify_source(vt,source)
    except Exception as exc:
        errors.append(public_error(exc,source,pending,output))
        status = "partial" if scanned else "failed"
    finally:
        if db is not None:
            db.close()
        if vt is not None:
            try:
                table_bytes = vt.table_bytes
            except ValueError:
                pass  # invalidated authority still must be disposed
            finally:
                vt.close()
    try:
        source_unchanged = sha256(source)==original
    except Exception as exc:
        source_unchanged = False
        errors.append(public_error(exc,source,pending,output))
    if not source_unchanged:
        status = "failed"
        errors.append("Source changed; no successful B output")
    result = dict(version=VERSION,status=status,errors=errors,configuration=asdict(config),configuration_sha256=config.sha256,
                  source_sha256=original,source_unchanged=source_unchanged,validation=validation,validation_traversals=1,
                  decoded_frames=validation["presented_frames"] if validation else 0,scanned_frames=scanned,scan_eof=eof,
                  candidate_count=candidates_count,evidence_count=evidence_count,evidence_bytes=evidence_bytes,
                  spool_bytes=spool_bytes,traversal_table_bytes=table_bytes,analysis_state_bytes_upper_estimate=tracker.max_state_bytes,
                  peak_combined_metadata_spool_bytes=peak_spool_bytes,peak_total_owned_bytes=peak_owned_bytes,
                  budget_accounting="max_spool includes B metadata and live VT; max_evidence is separate; checks per frame/128 candidate rows/evidence row; bounded staging quantum and diagnostic reserve explicitly reported",
                  max_live_tiles=len(tracker.occurrences),elapsed_seconds=time.perf_counter()-started,peak_rss=peak_rss(),
                  cleanup="VT removed before result publication; queue SQLite retained as bounded diagnostic spool; output owned by caller",
                  timing="native PTS/time-base; EOF end uncertainty retained; no nominal-FPS synthesis")
    try:
        for name in ("candidates.jsonl", "signals.jsonl", "evidence.jsonl"):
            if not (pending/name).exists():
                (pending/name).touch()
        # Final diagnostics are separate from the engine spool budget and never
        # turn exhaustion into complete success. Account their own bytes.
        final_spool = sum(p.stat().st_size for p in pending.iterdir() if p.is_file())
        if final_spool > config.max_spool_bytes and status == "complete":
            result["status"] = "partial"
            result["errors"].append("Final metadata spool exceeds budget")
        result["spool_bytes"] = final_spool
        result["diagnostic_bytes"] = len(canonical(result))
        while result["diagnostic_bytes"] != len(canonical(result)):
            result["diagnostic_bytes"] = len(canonical(result))
        if result["diagnostic_bytes"] > config.max_diagnostic_bytes:
            raise BudgetExceeded("Final B diagnostic reserve exhausted")
        with (pending/"result.json").open("xb") as sink:
            sink.write(canonical(result))
        # B diagnostics only: exclusive new directory, no READY/packet writer.
        output.mkdir()
        try:
            for path in sorted(pending.iterdir(),key=lambda p:p.name=="result.json"):
                os.rename(path,output/path.name)
        except BaseException:
            shutil.rmtree(output)
            raise
        pending.rmdir()
    except BaseException as exc:
        shutil.rmtree(pending,ignore_errors=True)
        if isinstance(exc,Exception):
            raise ValueError(public_error(exc,source,pending,output)) from None
        raise
    return result
