"""Frozen declarative truth and deterministic YUV fixture generation."""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import json
import numpy as np
from .common import digest, sha256, write_json
from .frames import id_bits

CORPUS = Path(__file__).parent / "corpora" / "corpus-v1"


def load_corpus(name="corpus-v1"):
    if name != "corpus-v1":
        raise ValueError("Unknown corpus version")
    spec = json.loads((CORPUS / "spec.json").read_text(encoding="utf-8"))
    truth = json.loads((CORPUS / "annotations.json").read_text(encoding="utf-8"))
    frozen = json.loads((CORPUS / "digests.json").read_text(encoding="utf-8"))
    if digest(spec) != frozen["spec"] or digest(truth) != frozen["annotations"]:
        raise ValueError("Frozen corpus-v1 truth digest changed")
    for fixture in truth["fixtures"]:
        if digest(fixture["pts"]) != frozen["schedules"][fixture["id"]]:
            raise ValueError("Frozen schedule changed")
    return spec, truth, frozen


def planes_for(spec, fixture, index, omit=None):
    """Generator truth: studio-range 8-bit YUV420, no RGB conversion."""
    width, height = fixture["width"], fixture["height"]
    seed = fixture["seed"]
    yy, xx = np.indices((height, width))
    y = (32 + ((xx // 12 + yy // 10 + index * 3 + seed) % 64)).astype(np.uint8)
    u = np.full((height // 2, width // 2), 128, np.uint8)
    v = u.copy()
    # Persistent HUD is an annotated foreground event and can be omitted for
    # an independent counterfactual survival comparison.
    for event in fixture["events"]:
        if event["id"] == omit or not event["start"] <= index < event["end_exclusive"]:
            continue
        x, top, w, h = event["region_xywh"]
        style = event["style"]
        roi = y[top:top+h, x:x+w]
        if style == "chroma":
            u[top//2:(top+h)//2, x//2:(x+w)//2] = 200
            v[top//2:(top+h)//2, x//2:(x+w)//2] = 60
        elif style == "low_contrast":
            roi[:] = np.minimum(roi.astype(np.uint16) + 6, 235).astype(np.uint8)
        elif style == "fade_scale":
            phase = index - event["start"] + 1
            inset = max(0, 10-phase)
            roi[inset:h-inset, inset:w-inset] = 100 + phase * 8
        else:
            value = event["luma"]
            roi[:] = value
            # Abstract glyph-like checker content; entirely synthetic.
            roi[4:h-4:4, 4:w-4:4] = 16 if value > 100 else 235
    # ID drawn last; challenge effects cannot overwrite the harness strip.
    x, top, _, _ = spec["harness"]["region_xywh"]
    cell = spec["harness"]["cell_px"]
    y[:32] = 16
    for j, bit in enumerate(id_bits(index)):
        y[top:top+cell, x+j*cell:x+(j+1)*cell] = 235 if bit else 16
    u[:16] = 128
    v[:16] = 128
    return [y, u, v]


def make_frame(planes):
    import av
    y, u, v = planes
    frame = av.VideoFrame(y.shape[1], y.shape[0], "yuv420p")
    for p, a in zip(frame.planes, planes):
        padded = np.zeros((p.height, p.line_size), np.uint8)
        padded[:, :a.shape[1]] = a
        p.update(padded)
    return frame


def encode(spec, fixture, path):
    import av
    settings = fixture["encoder"]
    options = {"fflags": "+bitexact"}
    if fixture["container"] == "mp4":
        options["movflags"] = "+faststart"
    with av.open(str(path), "w", format=fixture["container"], options=options) as output:
        audio = None
        if fixture["audio_before_video"]:
            audio = output.add_stream("pcm_s16le", rate=48000)
            audio.layout = "mono"
            audio.codec_context.thread_count = 1
        video = output.add_stream(settings["codec"], rate=Fraction(*fixture["rate"]))
        video.width, video.height, video.pix_fmt = fixture["width"], fixture["height"], "yuv420p"
        video.time_base = Fraction(1, 60000)
        video.codec_context.time_base = Fraction(1, 60000)
        video.codec_context.thread_count = 1
        if settings["codec"] == "libx264":
            video.options = {"preset": "medium", "crf": "18", "x264-params":
                             f"keyint={settings['gop']}:min-keyint={settings['gop']}:scenecut=0:bframes=2:b-adapt=0:threads=1"}
        else:
            video.options = {"level": "3", "coder": "1", "context": "1", "slicecrc": "1"}
        for i, pts in enumerate(fixture["pts"]):
            if audio is not None:
                af = av.AudioFrame.from_ndarray(np.zeros((1, 800), np.int16), format="s16", layout="mono")
                af.sample_rate, af.pts, af.time_base = 48000, i*800, Fraction(1, 48000)
                for packet in audio.encode(af):
                    output.mux(packet)
            frame = make_frame(planes_for(spec, fixture, i))
            frame.pts, frame.time_base = pts, Fraction(1, 60000)
            for packet in video.encode(frame):
                output.mux(packet)
        for packet in video.encode():
            output.mux(packet)
        if audio is not None:
            for packet in audio.encode():
                output.mux(packet)


def generate(out: Path, corpus="corpus-v1", split="all"):
    import av
    spec, truth, frozen = load_corpus(corpus)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise FileExistsError("Fixture output must be empty")
    selected = [f for f in truth["fixtures"] if split == "all" or f["split"] == split]
    records = []
    for fixture in selected:
        path = out / fixture["filename"]
        old_level = av.logging.get_level()
        av.logging.set_level(av.logging.INFO)
        try:
            with av.logging.Capture(local=True) as logs:
                encode(spec, fixture, path)
        finally:
            av.logging.set_level(old_level)
        records.append({"id": fixture["id"], "file": path.name, "sha256": sha256(path),
                        "bytes": path.stat().st_size, "status": "generated",
                        "encoder_logs": [message.strip() for _, component, message in logs
                                         if "x264" in component]})
    # Invalid inputs use the encoded main fixture, never user media.
    main = out / selected[0]["filename"]
    payload = main.read_bytes()
    (out / "truncated.mp4").write_bytes(payload[:len(payload)//2])
    damaged = bytearray(payload)
    # Corrupt a substantial central payload region, retain container header.
    start = len(payload)//2
    damaged[start:start+4096] = b"\xff" * min(4096, len(payload)-start)
    (out / "damaged.mp4").write_bytes(damaged)
    (out / "unsupported.mp4").write_bytes(b"synthetic non-media; never executable\n" * 32)
    report = {"corpus": corpus, "split": split, "T1": frozen, "fixtures": records,
              "invalid": [{"file": n, "sha256": sha256(out/n)} for n in
                          ("truncated.mp4", "damaged.mp4", "unsupported.mp4")]}
    write_json(out / "generation.json", report)
    return report
