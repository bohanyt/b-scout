"""Software presentation decode, bounded streamed ledger, exact random access."""
from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path
import sqlite3
import tempfile
import time

from .common import canonical, fingerprint, fraction, peak_rss, safe_output, sha256
from .frames import native_digest

VERSION = "bscout-ledger-v1"


class Timing:
    """Disk-backed counters keep duplicate identity stable even across regressions."""
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory(prefix="bscout-pts-")
        self.db = sqlite3.connect(str(Path(self.temp.name) / "counts.sqlite"))
        self.db.execute("PRAGMA cache_size=-256")
        self.db.execute("CREATE TABLE counts (pts INTEGER PRIMARY KEY, n INTEGER)")
        self.previous = None
        self.first = None
        self.counts = {"missing": 0, "duplicate": 0, "non_monotonic": 0}

    def observe(self, pts):
        flags = []
        if pts is None:
            self.counts["missing"] += 1
            return None, ["missing_pts"]
        if self.first is None:
            self.first = pts
        prior = self.db.execute("SELECT n FROM counts WHERE pts=?", (pts,)).fetchone()
        ordinal = 0 if prior is None else prior[0]
        self.db.execute("INSERT INTO counts VALUES (?,?) ON CONFLICT(pts) DO UPDATE SET n=excluded.n",
                        (pts, ordinal + 1))
        if ordinal:
            self.counts["duplicate"] += 1
            flags.append("duplicate_pts")
        if self.previous is not None and pts < self.previous:
            self.counts["non_monotonic"] += 1
            flags.append("non_monotonic_pts")
        self.previous = pts
        return ordinal, flags

    def close(self):
        self.db.close()
        self.temp.cleanup()


def select_video(container, index=None):
    videos = list(container.streams.video)
    if index is None:
        if not videos:
            raise ValueError("No video stream")
        stream = videos[0]
    else:
        stream = next((s for s in videos if s.index == index), None)
        if stream is None:
            raise ValueError("Selected stream is not video")
    stream.codec_context.thread_count = 1
    stream.codec_context.thread_type = "SLICE"
    stream.codec_context.options = {"err_detect": "explode"}
    return stream


def presented(container, stream):
    for packet in container.demux(stream):
        if packet.is_corrupt:
            raise ValueError("Demuxer flagged corrupt packet")
        for frame in packet.decode():
            if frame.is_corrupt:
                raise ValueError("Decoder flagged corrupt frame (concealed errors are not success)")
            yield frame


def frame_row(frame, ordinal, timing, source_hash, stream_index):
    same, flags = timing.observe(frame.pts)
    value, domain = native_digest(frame)
    return {"type": "frame", "ordinal": ordinal, "pts": frame.pts,
            "pts_unknown_reason": "decoder emitted no PTS" if frame.pts is None else None,
            "same_pts_ordinal": same, "time_base": fraction(frame.time_base),
            "identity": None if frame.pts is None else [source_hash, stream_index, frame.pts, same],
            "best_effort_timestamp": None,
            "best_effort_source": "not exposed separately by PyAV; not fabricated from FPS",
            "key_frame": bool(frame.key_frame), "pict_type": frame.pict_type.name
            if hasattr(frame.pict_type, "name") else str(frame.pict_type),
            "width": frame.width, "height": frame.height, "pix_fmt": frame.format.name,
            "native_sha256": value, "digest_domain": domain, "timing_flags": flags,
            "duration": getattr(frame, "duration", None)}


def ledger(source: Path, output: Path, stream_index=None):
    import av
    source, output = Path(source), Path(output)
    safe_output(source, output)
    before = sha256(source)
    start = time.perf_counter()
    timing = Timing()
    count, errors, last_duration = 0, [], None
    output.parent.mkdir(parents=True, exist_ok=True)
    status = "failed"
    try:
        with output.open("xb") as sink:
            def emit(value):
                sink.write(canonical(value))
            try:
                with av.open(str(source), options={"ignore_editlist": "0"}) as container:
                    stream = select_video(container, stream_index)
                    iterator = iter(presented(container, stream))
                    first = next(iterator, None)
                    if first is None:
                        raise ValueError("No presented video frames")
                    codec = stream.codec_context
                    emit({"type": "header", "version": VERSION,
                          "source_sha256": before, "source_bytes": source.stat().st_size,
                          "container": container.format.name, "selected_stream_index": stream.index,
                          "stream_count": len(container.streams), "time_base": fraction(stream.time_base),
                          "codec": codec.name, "pix_fmt": first.format.name,
                          "color": {k: getattr(codec, k, None) for k in
                                    ("color_range", "color_primaries", "color_trc", "colorspace")},
                          "container_start": container.start_time, "container_start_time_base": [1, 1000000],
                          "stream_start": stream.start_time, "stream_start_time_base": fraction(stream.time_base),
                          "first_presented_pts": first.pts, "origin_pts": first.pts,
                          "origin_convention": "first decoded presented-frame PTS; unknown stays unknown",
                          "first_presented_time_base": fraction(first.time_base),
                          "claimed_container_duration": container.duration,
                          "claimed_stream_duration": stream.duration,
                          "claimed_stream_frames": stream.frames,
                          "edit_lists": "FFmpeg demuxer default enabled; ignore_editlist=0 requested",
                          "toolchain": fingerprint()})
                    frame = first
                    while frame is not None:
                        emit(frame_row(frame, count, timing, before, stream.index))
                        count += 1
                        last_duration = getattr(frame, "duration", None)
                        frame = next(iterator, None)
                    # A short decode against a container claim is incomplete, not success.
                    if stream.frames and count != stream.frames:
                        errors.append("Presented-frame count differs from container claimed count")
                    status = "complete" if not errors and not any(timing.counts.values()) else "diagnostic"
            except Exception as exc:
                # Diagnostic artifacts must not expose a private input path.
                message = str(exc)
                # Native errors often embed repr(path), with doubled Windows
                # backslashes. Handle both repr and literal/resolved spellings.
                for private in (str(source), str(source.resolve())):
                    message = message.replace(repr(private), "'[source]'")
                    message = message.replace(private, "[source]")
                errors.append(f"{type(exc).__name__}: {message}")
                status = "partial" if count else "failed"
            unchanged = sha256(source) == before
            if not unchanged:
                status = "failed"
                errors.append("Source SHA changed during read")
            trailer = {"type": "trailer", "version": VERSION, "status": status,
                       "presented_frames": count, "timing": timing.counts, "errors": errors,
                       "discontinuities": "per-frame timing_flags; no fixed-FPS gap inference",
                       "last_frame_duration": last_duration if last_duration and last_duration > 0 else None,
                       "last_frame_duration_status": "decoder_reported" if last_duration and last_duration > 0 else "unknown",
                       "elapsed_seconds": time.perf_counter()-start, "peak_rss": peak_rss(),
                       "source_unchanged": unchanged, "output_bytes_before_trailer": sink.tell()}
            trailer["exact_recovery"] = {
                "status": "supported" if status == "complete" else "unsupported",
                "rule": "complete ledger with known, unique, strictly increasing PTS only"}
            # Fixed point allows the trailer to report total UTF-8 bytes, including itself.
            trailer["output_bytes"] = sink.tell()
            while True:
                total = sink.tell() + len(canonical(trailer))
                if total == trailer["output_bytes"]:
                    break
                trailer["output_bytes"] = total
            emit(trailer)
        return trailer
    finally:
        timing.close()


def rows(path):
    with Path(path).open(encoding="utf-8") as source:
        for line in source:
            yield json.loads(line)


def recovery_keys(ledger_path, header):
    """Validate the entire ledger; never trust a header/local counter as safety proof.

    v1 ledgers remain readable. The durable trailer state is advisory: raw rows,
    completion, and identities are checked again, including later anomalies.
    """
    if ledger_path is None:
        raise ValueError("Exact recovery requires a complete validated ledger")
    count, previous, found_header, trailer = 0, None, False, None
    keys = []
    for row in rows(ledger_path):
        kind = row.get("type")
        if trailer is not None:
            raise ValueError("Recovery ledger has records after trailer")
        if kind == "header" and not found_header and count == 0:
            if row != header or row.get("version") != VERSION:
                raise ValueError("Recovery ledger header mismatch")
            found_header = True
        elif kind == "frame" and found_header:
            pts = row.get("pts")
            if pts is None or (previous is not None and pts <= previous):
                raise ValueError("Exact recovery unsupported: missing/duplicate/non-monotonic PTS")
            if (row.get("ordinal") != count or row.get("same_pts_ordinal") != 0
                    or row.get("timing_flags") != []
                    or row.get("identity") != [header["source_sha256"],
                        header["selected_stream_index"], pts, 0]
                    or row.get("time_base") != header["first_presented_time_base"]
                    or (count == 0 and pts != header["first_presented_pts"])):
                raise ValueError("Recovery ledger frame identity/timing mismatch")
            if row["key_frame"]:
                keys.append(pts)
            previous, count = pts, count + 1
        elif kind == "trailer" and found_header:
            trailer = row
        else:
            raise ValueError("Invalid recovery ledger record order")
    if (not count or trailer is None or trailer.get("version") != VERSION
            or trailer.get("status") != "complete"
            or trailer.get("presented_frames") != count
            or trailer.get("timing") != {"missing": 0, "duplicate": 0, "non_monotonic": 0}
            or trailer.get("errors") != [] or trailer.get("source_unchanged") is not True):
        raise ValueError("Exact recovery unsupported: incomplete or unsafe ledger")
    return keys


def recover(source: Path, target: dict, header: dict, keys: list[int], *, ledger_path=None):
    """Actual backward keyframe seek, then presentation decode to exact identity."""
    import av
    source = Path(source)
    if sha256(source) != header["source_sha256"]:
        raise ValueError("Source digest differs from ledger")
    identity = target.get("identity")
    if identity is None or target["pts"] is None:
        raise ValueError("Exact recovery unavailable for unknown timing")
    if identity != [header["source_sha256"], header["selected_stream_index"],
                    target["pts"], target["same_pts_ordinal"]]:
        raise ValueError("Canonical target identity mismatch")
    validated_keys = recovery_keys(ledger_path, header)
    if keys != validated_keys:
        raise ValueError("Recovery keyframes differ from validated ledger")
    if target["same_pts_ordinal"] != 0:
        raise ValueError("Exact recovery unsupported: duplicate occurrence")
    # Seek strictly earlier than target and earlier than its preceding keyframe,
    # avoiding DTS-index/B-frame leading presentation traps and duplicate cuts.
    earlier = [p for p in keys if p < target["pts"]]
    anchor = max(earlier) if earlier else header["first_presented_pts"]
    with av.open(str(source), options={"ignore_editlist": "0"}) as container:
        stream = select_video(container, header["selected_stream_index"])
        target_tb = Fraction(*target["time_base"])
        offset = (Fraction(anchor-1) * target_tb) / stream.time_base
        seek_pts = offset.numerator // offset.denominator
        container.seek(seek_pts, stream=stream, backward=True, any_frame=False)
        decoded, previous = 0, None
        first_emitted = None
        for frame in presented(container, stream):
            decoded += 1
            if first_emitted is None:
                first_emitted = frame.pts
            if frame.time_base != target_tb:
                raise ValueError("Recovery time base differs from ledger")
            if frame.pts is None or (previous is not None and frame.pts <= previous):
                raise ValueError("Exact recovery unsupported: unsafe seek-path timing")
            previous = frame.pts
            if frame.pts == target["pts"]:
                actual, _ = native_digest(frame)
                if actual != target["native_sha256"]:
                    raise ValueError("Seek-path native digest mismatch")
                return frame, {"identity": identity, "sha256": actual,
                               "seek_offset": seek_pts, "first_emitted_pts": first_emitted,
                               "decoded_forward": decoded, "backward": True, "any_frame": False}
        raise ValueError("Exact known target identity never emitted after seek")
