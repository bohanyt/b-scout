"""Bounded Checkpoint-A public CLI."""
import argparse
import json
from pathlib import Path
import sys
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
    r.add_argument("--out", type=Path, required=True, help="Padding-free native plane bytes")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
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
            from .ledger import recover, rows
            from .frames import native_planes
            from .common import safe_output
            safe_output(args.source, args.out)
            if args.ledger.resolve() == args.out.resolve():
                raise ValueError("Recovery output aliases ledger")
            header, target, keys = None, None, []
            for row in rows(args.ledger):
                if row["type"] == "header":
                    header = row
                elif row["type"] == "frame":
                    if row["key_frame"] and row["pts"] is not None:
                        keys.append(row["pts"])
                    if row["pts"] == args.pts and row["same_pts_ordinal"] == args.same_pts_ordinal:
                        target = row
            if header is None or target is None:
                raise ValueError("Known target not found in ledger")
            frame, result = recover(args.source, target, header, keys, ledger_path=args.ledger)
            args.out.parent.mkdir(parents=True, exist_ok=True)
            with args.out.open("xb") as sink:
                for plane in native_planes(frame)[0]:
                    sink.write(plane.tobytes())
        print(canonical(result).decode(), end="")
        if args.command == "ledger":
            return 0 if result["status"] == "complete" else 2
        if args.command == "oracle":
            return 0 if all(f["status"] == "pass" for f in result["fixtures"]) else 2
        return 0
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        return 2
