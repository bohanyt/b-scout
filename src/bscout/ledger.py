"""Software presentation decode, bounded streamed ledger, exact random access."""
from __future__ import annotations

from fractions import Fraction
from dataclasses import dataclass, replace
import copy
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import time
import weakref

from .common import canonical, digest, fingerprint, fraction, peak_rss, safe_output, sha256
from .frames import DOMAIN, native_digest

VERSION = "bscout-ledger-v2"
PROJECTION = "bscout-traversal-projection-v1"


@dataclass(frozen=True, slots=True)
class DecodeConfig:
    """Immutable software baseline shared by full validation and seek decode."""
    stream_index: int | None = None
    demux_options: tuple = (("ignore_editlist", "0"),)
    hardware: bool = False
    thread_count: int = 1
    thread_type: str = "SLICE"
    err_detect: str = "explode"
    ledger_version: str = VERSION
    projection_version: str = PROJECTION
    domain_version: str = DOMAIN

    def __post_init__(self):
        if self.stream_index is not None and (type(self.stream_index) is not int or self.stream_index < 0):
            raise ValueError("Invalid video stream selection")
        if (self.demux_options != (("ignore_editlist", "0"),) or type(self.demux_options) is not tuple
                or self.hardware is not False or type(self.thread_count) is not int or self.thread_count != 1
                or self.thread_type != "SLICE" or self.err_detect != "explode"
                or (self.ledger_version, self.projection_version, self.domain_version) != (VERSION, PROJECTION, DOMAIN)):
            raise ValueError("Unsupported decoder configuration for Checkpoint A")

    def binding(self, toolchain):
        return {"selected_stream_index": self.stream_index, "demux_options": dict(self.demux_options),
                "hardware": self.hardware, "thread_count": self.thread_count, "thread_type": self.thread_type,
                "err_detect": self.err_detect, "ledger_version": self.ledger_version,
                "projection_version": self.projection_version, "domain_version": self.domain_version,
                "toolchain": toolchain}


class _TraversalState:
    def __init__(self, source, config):
        self.source, self.config = source, config
        self.temp = tempfile.TemporaryDirectory(prefix="bscout-traversal-")
        self.db = None
        try:
            self.db = sqlite3.connect(str(Path(self.temp.name) / "traversal.sqlite"))
            self.db.execute("PRAGMA cache_size=-256")
            self.db.execute("CREATE TABLE frames (position INTEGER PRIMARY KEY, pts INTEGER, same INTEGER, key INTEGER, row TEXT)")
            self.db.execute("CREATE INDEX identity_idx ON frames(pts,same)")
            self.db.execute("CREATE INDEX anchor_idx ON frames(key,pts)")
        except BaseException:
            if self.db is not None:
                self.db.close()
            self.temp.cleanup()
            raise
        self.header, self.trailer = None, None
        self.invalid = False

    def dispose(self):
        try:
            if self.db is not None:
                self.db.close()
        finally:
            self.db = None
            self.temp.cleanup()


_LIVE = weakref.WeakKeyDictionary()


def _state(vt):
    if type(vt) is not ValidatedTraversal or vt not in _LIVE:
        raise ValueError("Expected live core-generated ValidatedTraversal; closed/unverified object")
    state = _LIVE[vt]
    if state.invalid or state.db is None:
        raise ValueError("ValidatedTraversal is invalidated or closed")
    return state


class ValidatedTraversal:
    """Opaque process-local capability. Only an actual core decode can mint it.

    Public metadata is copied; no caller-owned table or deserialized state is
    imported. This is a trusted-process boundary, not protection from hostile
    Python code already executing in this process.
    """
    __slots__ = ("__weakref__",)

    def __init__(self, *args, **kwargs):
        raise ValueError("Use validate_traversal; caller state cannot construct a VT")

    def __enter__(self):
        _state(self)
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        state = _LIVE.pop(self, None)
        if state is not None:
            state.dispose()

    @property
    def header(self):
        return copy.deepcopy(_state(self).header)

    @property
    def trailer(self):
        return copy.deepcopy(_state(self).trailer)

    @property
    def temporary_directory(self):
        """Local lifecycle inspection only; never part of portable metadata."""
        return Path(_state(self).temp.name)

    @property
    def table_bytes(self):
        s = _state(self)
        return (Path(s.temp.name) / "traversal.sqlite").stat().st_size

    def entry(self, position):
        if type(position) is not int:
            raise ValueError("Traversal position must be an integer")
        row = _state(self).db.execute("SELECT row FROM frames WHERE position=?", (position,)).fetchone()
        if row is None:
            raise ValueError("Target position absent in validated traversal")
        return json.loads(row[0])

    def identity(self, pts, same_pts_ordinal=0):
        s = _state(self)
        if s.header is None:
            raise ValueError("No validated source header for identity selection")
        return (s.header["source_sha256"], s.header["selected_stream_index"], pts, same_pts_ordinal)


def _mint(state):
    vt = object.__new__(ValidatedTraversal)
    _LIVE[vt] = state
    weakref.finalize(vt, state.dispose)
    return vt


def public_error(exc, *paths):
    message = str(exc)
    for path in paths:
        for private in (str(path), str(Path(path).resolve())):
            message = message.replace(repr(private), "'[source]'").replace(private, "[source]")
    return f"{type(exc).__name__}: {message}"


class Timing:
    """Disk-backed counters keep duplicate identity stable even across regressions."""
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory(prefix="bscout-pts-")
        self.db = None
        try:
            self.db = sqlite3.connect(str(Path(self.temp.name) / "counts.sqlite"))
            self.db.execute("PRAGMA cache_size=-256")
            self.db.execute("CREATE TABLE counts (pts INTEGER PRIMARY KEY, n INTEGER)")
        except BaseException:
            if self.db is not None:
                self.db.close()
            self.temp.cleanup()
            raise
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
        try:
            if self.db is not None:
                self.db.close()
        finally:
            self.db = None
            self.temp.cleanup()


def select_video(container, index=None, config=None):
    videos = list(container.streams.video)
    if index is None:
        if not videos:
            raise ValueError("No video stream")
        stream = videos[0]
    else:
        stream = next((s for s in videos if s.index == index), None)
        if stream is None:
            raise ValueError("Selected stream is not video")
    config = config or DecodeConfig()
    stream.codec_context.thread_count = config.thread_count
    stream.codec_context.thread_type = config.thread_type
    stream.codec_context.options = {"err_detect": config.err_detect}
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


def _header(source, before, size, container, stream, first, config, toolchain):
    codec = stream.codec_context
    return {"type": "header", "version": VERSION, "projection_version": PROJECTION,
            "domain_version": DOMAIN, "source_sha256": before, "source_bytes": size,
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
            "claimed_container_duration": container.duration, "claimed_stream_duration": stream.duration,
            "claimed_stream_frames": stream.frames,
            "edit_lists": "FFmpeg demuxer default enabled; ignore_editlist=0 requested",
            "toolchain": toolchain, "decode_binding": config.binding(toolchain)}


# Only these run-local fields are optional and excluded from semantic comparison.
# Unknown fields are rejected: extensions require a new explicit projection policy.
_TELEMETRY = {"elapsed_seconds", "peak_rss", "output_bytes_before_trailer", "output_bytes",
              "traversal_table_bytes"}


def _trailer_semantics(trailer):
    return {k: v for k, v in trailer.items() if k not in _TELEMETRY and k != "projection_sha256"}


def validate_traversal(source: Path, config=DecodeConfig(), ledger_out=None, *, max_storage_bytes=None):
    """One complete actual decode creates process-local traversal authority.

    Diagnostic/failed traversals can produce ledgers, but never recover frames.
    Sources must remain stable local files; hashes detect observed changes, not
    malicious modify-and-restore races. No persisted state is trusted on import.
    """
    import av
    if type(config) is not DecodeConfig:
        raise ValueError("Expected immutable DecodeConfig")
    if max_storage_bytes is not None and (type(max_storage_bytes) is not int or max_storage_bytes <= 0):
        raise ValueError("Invalid traversal storage budget")
    source = Path(source).resolve()
    output = None if ledger_out is None else Path(ledger_out)
    if output is not None:
        safe_output(source, output)
    try:
        before, size = sha256(source), source.stat().st_size
    except Exception as exc:
        raise ValueError(public_error(exc, source)) from None
    state = _TraversalState(source, config)
    timing, sink = None, None
    start = time.perf_counter()
    count, errors, last_duration, eof = 0, [], None, False
    status = "failed"
    projection = hashlib.sha256()
    try:
        timing = Timing()
        if output is not None:
            output.parent.mkdir(parents=True, exist_ok=True)
            sink = output.open("xb")
        def emit(row):
            data = canonical(row)
            projection.update(data)
            if sink is not None:
                sink.write(data)
        try:
            toolchain = fingerprint()
            with av.open(str(source), options=dict(config.demux_options)) as container:
                stream = select_video(container, config.stream_index, config)
                state.config = replace(config, stream_index=stream.index)
                iterator = iter(presented(container, stream))
                first = next(iterator, None)
                if first is None:
                    raise ValueError("No presented video frames")
                state.header = _header(source, before, size, container, stream, first, state.config, toolchain)
                emit(state.header)
                frame = first
                incompatible = False
                while frame is not None:
                    row = frame_row(frame, count, timing, before, stream.index)
                    tb = row["time_base"]
                    incompatible |= tb is None or tb[0] <= 0 or tb[1] <= 0 or tb != state.header["first_presented_time_base"]
                    state.db.execute("INSERT INTO frames VALUES (?,?,?,?,?)",
                                     (count, row["pts"], row["same_pts_ordinal"], int(row["key_frame"]),
                                      canonical(row).decode("utf-8")))
                    emit(row)
                    count += 1
                    if max_storage_bytes is not None:
                        # Include dirty SQLite pages, journals, PTS counters and
                        # streamed ledger. Stop explicitly; never mint complete
                        # authority from the retained prefix after exhaustion.
                        storage = sum(p.stat().st_size for directory in (Path(state.temp.name), Path(timing.temp.name))
                                      for p in directory.iterdir() if p.is_file())
                        storage += state.db.execute("PRAGMA page_count").fetchone()[0] * state.db.execute("PRAGMA page_size").fetchone()[0]
                        storage += sink.tell() if sink is not None else 0
                        if storage > max_storage_bytes:
                            raise ValueError("Traversal storage budget exhausted; incomplete validation")
                    last_duration = getattr(frame, "duration", None)
                    frame = next(iterator, None)
                # presented consumes demux EOF and its decoder flush packets.
                eof = True
                if stream.frames and count != stream.frames:
                    errors.append("Presented-frame count differs from container claimed count")
                if incompatible:
                    errors.append("Incompatible or unknown presentation time bases")
                status = "complete" if not errors and not any(timing.counts.values()) else "diagnostic"
        except Exception as exc:
            errors.append(public_error(exc, source))
            status = "partial" if count else "failed"
        try:
            unchanged = source.stat().st_size == size and sha256(source) == before
        except Exception as exc:
            errors.append(public_error(exc, source))
            unchanged = False
        if not unchanged:
            status = "failed"
            errors.append("Source SHA/size changed during validation")
        state.db.commit()
        table_bytes = (Path(state.temp.name) / "traversal.sqlite").stat().st_size
        trailer = {"type": "trailer", "version": VERSION, "status": status,
                   "presented_frames": count, "timing": dict(timing.counts), "errors": errors,
                   "decode_eof": eof, "validation_passes": 1,
                   "discontinuities": "per-frame timing_flags; no fixed-FPS gap inference",
                   "last_frame_duration": last_duration if last_duration and last_duration > 0 else None,
                   "last_frame_duration_status": "decoder_reported" if last_duration and last_duration > 0 else "unknown",
                   "elapsed_seconds": time.perf_counter()-start, "peak_rss": peak_rss(),
                   "source_unchanged": unchanged, "traversal_table_bytes": table_bytes,
                   "exact_recovery": {"status": "supported" if status == "complete" else "unsupported",
                       "rule": "core complete traversal with known, unique, strictly increasing PTS and compatible time bases"}}
        projection.update(canonical(_trailer_semantics(trailer)))
        trailer["projection_sha256"] = projection.hexdigest()
        if sink is not None:
            trailer["output_bytes_before_trailer"] = sink.tell()
            trailer["output_bytes"] = sink.tell()
            while True:
                total = sink.tell() + len(canonical(trailer))
                if total == trailer["output_bytes"]:
                    break
                trailer["output_bytes"] = total
            sink.write(canonical(trailer))
        state.trailer = trailer
        return _mint(state)
    except BaseException:
        state.dispose()
        raise
    finally:
        if timing is not None:
            timing.close()
        if sink is not None:
            sink.close()


def ledger(source: Path, output: Path, stream_index=None):
    """Diagnostic-readable v2 ledger from the same full core validation pass."""
    with validate_traversal(source, DecodeConfig(stream_index=stream_index), ledger_out=output) as vt:
        return vt.trailer


def rows(path):
    with Path(path).open(encoding="utf-8") as source:
        for line in source:
            yield json.loads(line)


def _check_source(state, source):
    try:
        source = Path(source).resolve()
        if (source != state.source or state.header is None
                or source.stat().st_size != state.header["source_bytes"]
                or sha256(source) != state.header["source_sha256"]):
            raise ValueError("Source differs from validated traversal")
    except Exception as exc:
        state.invalid = True
        raise ValueError(public_error(exc, source, state.source)) from None


def _check_config(state, config=None):
    if config is not None:
        if type(config) is not DecodeConfig:
            raise ValueError("Expected immutable DecodeConfig")
        normalized = replace(config, stream_index=state.config.stream_index) if config.stream_index is None else config
        if normalized != state.config:
            raise ValueError("Recovery configuration differs from validated traversal")
    if canonical(fingerprint()) != canonical(state.header["toolchain"]):
        state.invalid = True
        raise ValueError("Native toolchain differs from validated traversal")


def verify_source(vt, source):
    """Recheck the source binding before a caller publishes withheld output."""
    state = _state(vt)
    _check_source(state, source)
    _check_config(state)


def _same_projection(actual, expected, telemetry=frozenset()):
    if not isinstance(actual, dict) or set(actual)-set(expected)-set(telemetry):
        return False
    required = set(expected)-set(telemetry)
    if not required.issubset(actual):
        return False
    return canonical({k: actual[k] for k in required}) == canonical({k: expected[k] for k in required})


def compare_ledger(vt, ledger_path):
    """Strict semantic cross-check against actual core observations, never authority.

    v1 is diagnostic-readable only: it lacks the explicit v2 config binding.
    Header/frame fields and trailer observation facts are required. Only the
    documented trailer telemetry fields may vary or be omitted.
    """
    state = _state(vt)
    if state.header is None:
        raise ValueError("No validated source header for ledger comparison")
    _check_source(state, state.source)
    _check_config(state)
    records = iter(_imported_rows(ledger_path))
    if not _same_projection(next(records, None), state.header):
        raise ValueError("Imported ledger header/config/version differs from source traversal; legacy ledger unverified")
    for (stored,) in state.db.execute("SELECT row FROM frames ORDER BY position"):
        if not _same_projection(next(records, None), json.loads(stored)):
            raise ValueError("Imported ledger frame differs from complete source traversal")
    if not _same_projection(next(records, None), state.trailer, _TELEMETRY):
        raise ValueError("Imported ledger trailer/completion differs from source traversal")
    if next(records, None) is not None:
        raise ValueError("Imported ledger has extra records")
    _check_source(state, state.source)
    return {"status": "matched", "projection_version": PROJECTION,
            "projection_sha256": state.trailer["projection_sha256"]}


def _imported_rows(path):
    try:
        yield from rows(path)
    except Exception as exc:
        raise ValueError(public_error(exc, path)) from None


def recover(source: Path, vt, requested_identity, *, ledger_path=None, config=None):
    """Source-bound real backward seek with contiguous VT alignment through target."""
    import av
    state = _state(vt)
    if state.trailer["status"] != "complete" or not state.trailer["decode_eof"]:
        raise ValueError("Exact recovery unsupported: unsafe/incomplete source traversal")
    _check_source(state, source)
    _check_config(state, config)
    if ledger_path is not None:
        compare_ledger(vt, ledger_path)
    if not isinstance(requested_identity, (tuple, list)) or len(requested_identity) != 4:
        raise ValueError("Expected canonical identity request, not caller target metadata")
    source_hash, stream_index, pts, same = requested_identity
    if (source_hash != state.header["source_sha256"] or type(stream_index) is not int
            or stream_index != state.config.stream_index or type(pts) is not int or type(same) is not int):
        raise ValueError("Canonical target identity differs from validated source/stream or timing unknown")
    if same != 0:
        raise ValueError("Exact recovery unsupported: nonzero duplicate occurrence ordinal")
    stored = state.db.execute("SELECT row FROM frames WHERE pts=? AND same=0", (pts,)).fetchone()
    if stored is None:
        raise ValueError("Target identity absent in validated traversal (before seek)")
    target = json.loads(stored[0])
    anchor_row = state.db.execute("SELECT pts FROM frames WHERE key=1 AND pts<? ORDER BY pts DESC LIMIT 1", (pts,)).fetchone()
    anchor = anchor_row[0] if anchor_row else state.header["first_presented_pts"]
    target_tb = Fraction(*target["time_base"])
    decoded, previous_pts, position, first_emitted, result = 0, None, None, None, None
    try:
        with av.open(str(state.source), options=dict(state.config.demux_options)) as container:
            stream = select_video(container, state.config.stream_index, state.config)
            if fraction(stream.time_base) != state.header["time_base"]:
                raise ValueError("Seek stream time base differs from validated traversal")
            offset = (Fraction(anchor-1)*target_tb)/stream.time_base
            seek_pts = offset.numerator//offset.denominator
            container.seek(seek_pts, stream=stream, backward=True, any_frame=False)
            for frame in presented(container, stream):
                decoded += 1
                if frame.pts is None or (previous_pts is not None and frame.pts <= previous_pts):
                    raise ValueError("Unsafe seek-path timing")
                if frame.time_base != target_tb:
                    raise ValueError("Seek frame time base differs from validated traversal")
                if position is None:
                    found = state.db.execute("SELECT position FROM frames WHERE pts=? AND same=0", (frame.pts,)).fetchone()
                    if found is None or found[0] > target["ordinal"]:
                        raise ValueError("Seek first frame unaligned or overshoots target")
                    position, first_emitted = found[0], frame.pts
                else:
                    position += 1
                expected = vt.entry(position)
                actual_digest, domain = native_digest(frame)
                actual = {"pts": frame.pts, "time_base": fraction(frame.time_base),
                          "key_frame": bool(frame.key_frame), "width": frame.width, "height": frame.height,
                          "pix_fmt": frame.format.name, "native_sha256": actual_digest, "digest_domain": domain}
                if canonical(actual) != canonical({k: expected[k] for k in actual}):
                    raise ValueError("Seek frame alignment/representation/native digest mismatch")
                previous_pts = frame.pts
                if position == target["ordinal"]:
                    result = frame, {"identity": target["identity"], "sha256": target["native_sha256"],
                        "source_sha256": state.header["source_sha256"],
                        "decode_binding_sha256": digest(state.header["decode_binding"]),
                        "projection_version": PROJECTION, "projection_sha256": state.trailer["projection_sha256"],
                        "target_position": position, "seek_offset": seek_pts, "first_emitted_pts": first_emitted,
                        "decoded_forward": decoded, "backward": True, "any_frame": False}
                    break
            if result is None:
                raise ValueError("Target present in VT but never emitted after seek")
        # Withhold the frame/proof until the post-check succeeds, including close.
        _check_source(state, source)
        return result
    except Exception as exc:
        _check_source(state, source)
        raise ValueError(public_error(exc, source)) from None
