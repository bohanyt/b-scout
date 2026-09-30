"""Versioned padding-free native plane digest and checked frame IDs."""
from __future__ import annotations

import hashlib
import zlib
import numpy as np
from .common import canonical

DOMAIN = "bscout-native-planes-v1"


def native_planes(frame):
    fmt = frame.format.name
    # Explicit supported storage domains; reject unknown layouts, don't guess.
    planar8 = {"yuv420p", "yuv422p", "yuv444p", "yuvj420p", "yuvj422p", "yuvj444p",
               "gbrp", "gray"}
    planar16 = {"yuv420p10le", "yuv422p10le", "yuv444p10le", "yuv420p12le",
                "yuv444p16le", "gray16le", "gbrp10le"}
    packed = {"rgb24": 3, "bgr24": 3, "rgba": 4, "bgra": 4, "argb": 4, "abgr": 4}
    if fmt not in planar8 | planar16 | set(packed) | {"nv12", "nv21"}:
        raise ValueError(f"Unsupported native digest pixel format: {fmt}")
    arrays, layout = [], []
    for i, p in enumerate(frame.planes):
        unit = (2 if fmt in planar16 else packed.get(fmt, 1))
        if fmt in {"nv12", "nv21"} and i == 1:
            unit = 2
        row_bytes = p.width * unit
        if p.line_size < row_bytes:
            raise ValueError("Negative/short native plane stride unsupported")
        a = np.frombuffer(p, dtype=np.uint8).reshape(p.height, p.line_size)[:, :row_bytes]
        arrays.append(a)
        layout.append({"plane": i, "width": p.width, "height": p.height,
                       "row_bytes": row_bytes, "sample_storage_bytes": unit})
    return arrays, layout


def native_digest(frame):
    arrays, layout = native_planes(frame)
    header = {"domain": DOMAIN, "width": frame.width, "height": frame.height,
              "pix_fmt": frame.format.name, "planes": layout}
    h = hashlib.sha256(canonical(header))
    for a in arrays:
        h.update(a.tobytes(order="C"))
    return h.hexdigest(), header


def id_bits(index: int):
    if not 0 <= index < 65536:
        raise ValueError("Frame-ID v1 range exceeded")
    check = zlib.crc32(index.to_bytes(2, "little")) & 255
    value = index | (check << 16)
    return [(value >> i) & 1 for i in range(24)]


def read_id(frame, harness):
    y = native_planes(frame)[0][0]
    if frame.format.name != "yuv420p":
        raise ValueError("Oracle frame-ID requires declared yuv420p representation")
    x, top, _, _ = harness["region_xywh"]
    cell = harness["cell_px"]
    means = [float(y[top + 4:top + cell - 4, x + j * cell + 4:x + (j + 1) * cell - 4].mean())
             for j in range(24)]
    if any(80 <= v <= 175 for v in means):
        raise ValueError("Frame-ID cell ambiguous/degraded")
    bits = [int(v > 127) for v in means]
    index = sum(b << i for i, b in enumerate(bits[:16]))
    if bits != id_bits(index):
        raise ValueError("Frame-ID check bits mismatch")
    return index
