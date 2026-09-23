# Evidence packet contract — 0.1-draft

This is a draft interface for humans, local agents, and cloud review. The schemas cover the manifest/event envelope; full packet validation and providers are BS-001+ work. Illustrative records in `examples/` are not measured output and are deliberately incomplete.

## Portable layout

```text
<source>.<run-id>.bscout/
  manifest.json
  events/000001.jsonl       # bounded shards, stable event IDs
  transcript.jsonl         # optional; timestamped segments/words
  overview.jsonl           # sparse coverage outside text events
  frames/                  # full frame/crops; separate files
  contactsheets/           # navigation aids, not OCR originals
  clips/                   # optional contextual video
  checksums.json
  summary.md               # human/agent entry point
  READY.json               # written last after local validation
```

Local-only state/credentials/source-path maps stay outside the portable packet. Outputs use a new directory or validated resume identity; no overwrite of unrelated files. Cancellation/error leaves partial status, not a success marker. A failed optional stage may be skipped/failed explicitly; `complete` only covers the requested scope, not perfect understanding.

## Identity and timing

Manifest records schema and engine/config versions, run/source IDs, source hash when available, selected streams, dimensions, PTS origin, rational time-base, duration, stage status, scan coverage/gaps, and an artifact inventory. Use packet-relative POSIX paths with no `..`, absolute paths, drive letters, or URLs in local artifact paths. Readers must resolve and reject symlink escapes, not just test strings.

Events retain source ID, first observed frame/PTS, exclusive end frame/PTS, kind, region in original source pixels, raw signal scores, OCR state, best-frame asset reference, context range, shared content ID, occurrence number, and review/warning fields. One second is not a timestamp precision limit. Keep exact integer PTS; derive display time from `(pts - origin_pts) * time_base.num / time_base.den`.

An event's best frame must lie inside its interval. A source's frame indices start at zero and are presentation-order indices, not packet numbers. Last-frame duration uncertainty is explicit. Different source/edited clocks require an offset or piecewise map; never silently reuse timestamps across a rough cut.

## Observations versus interpretation

Initial kinds are conservative: `visual_change_candidate`, `text_candidate`, `ui_candidate`, `speech_segment`. Do not label a generic change `boss_reveal` without validated evidence. `score` is not a calibrated probability. OCR stores raw output, provider/model and status; unreadable/failed is not equivalent to no event.

Later `editorial.jsonl` is a separate artifact keyed by event/source IDs, with author/model, evidence IDs actually inspected, rationale, and KEEP/VO/FREEZE/MONTAGE/REVIEW verdicts. Do not overwrite observations with generated narration or fabricate ground truth.

## Asset integrity and publication

Each exported asset has an ID, relative path, MIME type, byte count and SHA-256. `checksums.json` inventories content artifacts including the manifest; it excludes itself and READY. READY includes the run ID and checksum-file digest and is written last via a temporary file plus rename. Consumers must verify all referenced files/digests; cloud sync may deliver READY before other files despite local write order. A marker alone does not prove upload completeness.

The bootstrap schema permits an incomplete/example manifest and missing evidence, but a finished production packet must have no unresolved materialized references. Shard large event files; include counts and time ranges so agents do not need a giant JSON document. Preserve all occurrence records; storage budgets must be surfaced instead of silently truncating evidence.

## Drive handoff

MVP: export locally and let the user place a packet in a private Drive sync folder. A later uploader can add a separate delivery map of asset IDs to Drive file IDs/version IDs after verifying upload. Do not add a second Google login to the core prematurely.

A JSON filename is not an image. A Drive connector must successfully retrieve the actual referenced image bytes before an agent can claim to inspect them. Read summary/manifest, relevant event shards, then selected full-resolution frames. Use contact sheets for navigation. Record `evidence_unavailable` rather than inventing descriptions when images cannot be accessed. Direct video playback support is not assumed; use selected frames or an explicitly supported clip-analysis tool.

Export packages must warn about private desktop content, OCR text, and speech. Keep unredacted evidence local; redacted export variants have separate IDs/hashes. No automatic public links or repo uploads.
