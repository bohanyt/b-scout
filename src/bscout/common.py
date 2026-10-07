"""Canonical serialization, file safety and runtime provenance."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time


def canonical(value) -> bytes:
    """Sorted keys, compact JSON, UTF-8, no NaN, one terminal LF."""
    return (json.dumps(value, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def digest(value) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, value) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("xb") as output:
        output.write(canonical(value))


def fraction(value):
    return None if value is None else [value.numerator, value.denominator]


def safe_output(source: Path, output: Path) -> None:
    """Check aliases before any mkdir/open; never overwrite any output."""
    source, output = Path(source), Path(output)
    if source.resolve() == output.resolve():
        raise ValueError("Output resolves to source")
    if output.exists():
        if os.path.samefile(source, output):
            raise ValueError("Output aliases source")
        raise FileExistsError("Output already exists")
    if output.is_symlink():
        raise ValueError("Output is a dangling symlink")


def peak_rss() -> dict:
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
                (name, ctypes.c_size_t) for name in (
                    "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                    "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
                    "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]

        c = Counters()
        c.cb = ctypes.sizeof(c)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        api = ctypes.WinDLL("psapi", use_last_error=True).GetProcessMemoryInfo
        api.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        if not api(kernel.GetCurrentProcess(), ctypes.byref(c), c.cb):
            raise OSError(ctypes.get_last_error(), "GetProcessMemoryInfo")
        return {"bytes": c.PeakWorkingSetSize,
                "method": "Windows GetProcessMemoryInfo PeakWorkingSetSize; process lifetime incl native allocations"}
    import resource
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {"bytes": int(value * (1 if sys.platform == "darwin" else 1024)),
            "method": "getrusage(RUSAGE_SELF).ru_maxrss; process lifetime incl native allocations"}


def fingerprint() -> dict:
    import av
    import numpy
    return {"python": platform.python_version(), "implementation": platform.python_implementation(),
            "os": platform.system(), "os_release": platform.release(), "arch": platform.machine(),
            "av": av.__version__, "numpy": numpy.__version__,
            "libraries": {k: list(v) for k, v in av.library_versions.items()},
            "library_meta": av._core.library_meta, "decode": {"hardware": False, "thread_count": 1,
            "thread_type": "SLICE", "err_detect": "explode"},
            "encoder": "libx264 fixture-only; FFV1 lossless; software, one thread"}
