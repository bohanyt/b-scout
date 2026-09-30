"""Bounded Checkpoint-A public CLI."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
from . import __version__
from .common import canonical, write_json


def parser():
    p = argparse.ArgumentParser(description="B-Scout Checkpoint A temporal oracle (synthetic proof)")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="command", required=True)
    f = sub.add_parser("fixtures")
    fs = f.add_subparsers(dest="action", required=True)
    g = fs.add_parser("generate")
    g.add_argument("--corpus", default="corpus-v1")
    g.add_argument("--out", type=Path, required=True)
    g.add_argument("--split", choices=("all", "dev", "held_out"), default="all")
    l = sub.add_parser("ledger")
    l.add_argument("source", type=Path)
    l.add_argument("--out", type=Path, required=True)
    l.add_argument("--stream-index", type=int)
    o = sub.add_parser("oracle")
    os = o.add_subparsers(dest="action", required=True)
    v = os.add_parser("verify")
    v.add_argument("--corpus", default="corpus-v1")
    v.add_argument("--media", type=Path, required=True)
    v.add_argument("--out", type=Path, required=True)
    v.add_argument("--split", choices=("all", "dev", "held_out"), default="all")
    r = sub.add_parser("recover")
    r.add_argument("source", type=Path)
    r.add_argument("--ledger", type=Path, required=True)
    r.add_argument("--pts", type=int, required=True)
    r.add_argument("--same-pts-ordinal", type=int, default=0)
    r.add_argument("--stream-index", type=int)
    r.add_argument("--out", type=Path, required=True, help="Padding-free native plane bytes")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    pending = None
    try:
        if args.command == "fixtures":
            from .corpus import generate
            result = generate(args.out, args.corpus, args.split)
        elif args.command == "ledger":
            from .ledger import ledger
            result = ledger(args.source, args.out, args.stream_index)
        elif args.command == "oracle":
            from .oracle import verify
            result = verify(args.media, args.out, args.corpus, args.split)
            write_json(args.out / "oracle.json", result)
        else:
            from .ledger import DecodeConfig, recover, validate_traversal, verify_source
            from .frames import native_planes
            from .common import safe_output
            safe_output(args.source, args.out)
            if args.ledger.resolve() == args.out.resolve():
                raise ValueError("Recovery output aliases ledger")
            published = False
            try:
                with validate_traversal(args.source, DecodeConfig(stream_index=args.stream_index)) as vt:
                    frame, result = recover(args.source, vt, vt.identity(args.pts, args.same_pts_ordinal),
                                            ledger_path=args.ledger)
                    args.out.parent.mkdir(parents=True, exist_ok=True)
                    with tempfile.NamedTemporaryFile(dir=args.out.parent, prefix=".bscout-recovery-",
                                                     delete=False) as sink:
                        pending = Path(sink.name)
                        for plane in native_planes(frame)[0]:
                            sink.write(plane.tobytes())
                    verify_source(vt, args.source)
                # Finish traversal cleanup before exclusive final publication.
                os.link(pending, args.out)
                published = True
            finally:
                if pending is not None:
                    try:
                        pending.unlink(missing_ok=True)
                    except Exception:
                        if published:
                            args.out.unlink()  # only the destination just created by us
                        raise
        print(canonical(result).decode(), end="")
        if args.command == "ledger":
            return 0 if result["status"] == "complete" else 2
        if args.command == "oracle":
            return 0 if all(f["status"] == "pass" for f in result["fixtures"]) else 2
        return 0
    except Exception as exc:
        message = str(exc)
        paths = [getattr(args, key, None) for key in ("source", "ledger", "out", "media")]
        paths.append(pending)
        for path in paths:
            if path is not None:
                for private in (str(path), str(path.resolve())):
                    message = message.replace(repr(private), "'[local-file]'").replace(private, "[local-file]")
        print(json.dumps({"status": "failed", "error": f"{type(exc).__name__}: {message}"}), file=sys.stderr)
        return 2
