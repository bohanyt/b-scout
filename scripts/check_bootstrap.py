"""Validate bootstrap docs and illustrative contracts; not a video/packet runtime."""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import unquote

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"Expected object: {path}")
    return value


def safe_relative_path(value: str) -> bool:
    parts = PurePosixPath(value).parts
    return bool(value and parts and not value.startswith("/")
                and "\\" not in value and ":" not in value
                and ".." not in parts and "?" not in value and "#" not in value)


def validate_pair(manifest: dict, event: dict) -> None:
    """Small cross-record checks for fixtures; full runtime validation is BS-001."""
    source = manifest["source"]
    if event["source_id"] != source["source_id"]:
        raise ValueError("Event/source identity mismatch")
    start, end = event["start"], event["end_exclusive"]
    if not (start["pts"] < end["pts"] and start["frame_index"] < end["frame_index"]):
        raise ValueError("Invalid half-open event interval")
    lower, upper = source["origin_pts"], source["origin_pts"] + source["duration_pts"]
    context = event["context"]
    if not (lower <= context["start_pts"] <= start["pts"] < end["pts"] <= context["end_pts"] <= upper):
        raise ValueError("Event/context outside source time range")
    bbox = event["region_xywh"]
    if bbox is not None:
        x, y, width, height = bbox
        if x + width > source["width"] or y + height > source["height"]:
            raise ValueError("Region outside source pixels")
    artifacts = manifest["artifacts"]
    ids = {item["id"] for item in artifacts}
    if len(ids) != len(artifacts):
        raise ValueError("Duplicate artifact ID")
    if any(not safe_relative_path(item["path"]) for item in artifacts):
        raise ValueError("Unsafe artifact path")
    references = list(context["asset_ids"])
    best = event["best_frame"]
    if best is not None:
        if not (start["pts"] <= best["pts"] < end["pts"]
                and start["frame_index"] <= best["frame_index"] < end["frame_index"]):
            raise ValueError("Best frame outside event interval")
        references.append(best["asset_id"])
    if any(ref not in ids for ref in references):
        raise ValueError("Unresolved evidence reference")
    coverage = manifest["coverage"]
    decoded, scanned = coverage["decoded_frames"], coverage["scanned_frames"]
    if decoded is not None and scanned is not None and scanned > decoded:
        raise ValueError("Scanned frame count exceeds decoded count")
    if manifest["status"] == "complete":
        if manifest["example"] or source["sha256"] is None:
            raise ValueError("Example/unidentified source cannot claim complete")
        if decoded is None or scanned != decoded or coverage["gaps"]:
            raise ValueError("Incomplete coverage cannot claim complete")
        if best is None and event["kind"] != "speech_segment":
            raise ValueError("Completed visual event lacks evidence")


def check_links(root: Path = ROOT) -> int:
    checked = 0
    for file in root.rglob("*.md"):
        for raw in re.findall(r"(?<!!)\[[^\]]+\]\(([^\s)]+)\)", file.read_text(encoding="utf-8")):
            if raw.startswith(("https://", "http://", "mailto:", "#")):
                continue
            target = (file.parent / unquote(raw.split("#", 1)[0])).resolve()
            if not target.is_relative_to(root.resolve()) or not target.is_file():
                raise ValueError(f"Broken/local-outside-repo link: {file.relative_to(root)} -> {raw}")
            checked += 1
    return checked


def main() -> int:
    try:
        for name in ("manifest", "event"):
            schema = load_json(ROOT / "schemas" / f"{name}.schema.json")
            Draft202012Validator.check_schema(schema)
            Draft202012Validator(schema).validate(load_json(ROOT / "examples" / f"{name}.example.json"))
        validate_pair(load_json(ROOT / "examples/manifest.example.json"),
                      load_json(ROOT / "examples/event.example.json"))
        count = check_links()
        sentinel = "END_OF_BSCOUT_CT_HANDOFF key=BSCOUT-CT-HANDOFF-20260924-V1 sections=9"
        handoff = (ROOT / "docs/handoffs/2026-09-24-bootstrap.md").read_text(encoding="utf-8")
        if not handoff.rstrip().endswith(sentinel):
            raise ValueError("Missing full handoff end marker")
        print(f"PASS: 2 draft schemas, 2 illustrative records, cross-record checks, {count} local links, handoff marker")
        print("Scope: bootstrap only. No video detection, runtime recall, GUI, or provider was tested.")
        return 0
    except Exception as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
