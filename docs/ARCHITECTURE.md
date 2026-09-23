# Architecture: offline, multi-rate, evidence-first

Status: proposed implementation architecture adopted for bootstrap. No pipeline performance has been measured.

## Dataflow

```text
probe local source + source identity
  -> sequential decode with presentation timestamps
  -> every-frame regional change/edge signals
  -> candidate queue + periodic independent inspection
  -> region tracking / text and UI novelty checks
  -> candidate OCR + best readable frame + context references
  -> chronological events + optional timestamped speech
  -> validated portable packet -> human/AI review
```

## Time and input correctness

Scan the original or a verified time-preserving analysis copy. A lower-FPS export can already have discarded a short popup; no downstream detector can recover missing frames. Likewise, an alt-tab that was never recorded, or frozen game-capture output, contains no recoverable UI evidence.

Use decoded-frame PTS and rational time-base, not `frame_index / nominal_fps`, for timestamps. Normalize against an explicitly recorded origin; retain original PTS. Intervals are half-open. Preserve presentation order, record decode errors/discontinuities and end-boundary uncertainty. Exact-frame re-extraction must seek to an earlier decodable point then decode forward, not assume a keyframe seek is exact. PyAV documents these timing primitives [R2].

Per-level files are independent sources. A rough-cut input has a new time axis: do not map its timestamps to raw media without an explicit edit/time map. Separate microphone audio needs an explicit offset/map; do not assume its zero matches game zero. Choose one visible gameplay/composite source for scanning; alpha VTuber-only material lacks the game UI.

## Rates are scheduling, not promises

| Layer | Intended schedule | Work / output |
|---|---|---|
| L0 | Every decoded presentation frame | Tile/region pixel and edge deltas; persistent-state statistics; PTS ledger |
| L1 | Event-triggered plus configurable periodic inspection | Text-region model and panel heuristics; region association and novelty |
| L2 | Approximately one-second aggregation windows | Group and index events, preserving original frame boundaries |
| L3 | Candidate event only | Full-resolution OCR when needed, representative frame(s), context |
| L4 | Selected evidence on demand | Human or multimodal interpretation and editorial annotations |

A possible L1 heartbeat is 5-10 inspections per second of video time, but it is not frozen and can miss a sub-100ms event by itself. L0 triggers promote their exact source frames regardless of heartbeat phase. No batch boundary may throw them away. Under overload, slow down, spill bounded metadata, or return a partial result; never silently skip frames.

The engine is **offline**: processing one second of footage may take more than one second. Every-frame scheduling does not establish 60 FPS inference throughput. Decode, conversion, storage, and OCR all count toward benchmarks.

## Change, text, and UI are different signals

L0 does not recognize UI. Start with regional classical CV. Whole-screen hashes/averages alone can miss small text changes; excessive downscaling can erase them. Preserve scale mapping to full-resolution crops, and compare short-term change with a longer stable reference so slow fades can accumulate.

Text detection locates candidate text regions; recognition reads them. PaddleOCR exposes a separate text-detection module [R3], but the actual model/runtime remains a benchmark decision. An independent panel heuristic is useful when OCR/text detection fails. There is no assumption that a ready-made universal UI model will work on stylized game menus.

PySceneDetect is an optional shot segmentation component, not the transient-event gate: its minimum-scene-length behavior can merge/suppress short boundaries [R4]. A text event can happen without a scene cut or a new box.

Persistent HUD is not a blanket exclusion. Unchanged text may be deprioritized; numeric changes may matter. Keep raw region-change evidence available and use profile-specific rules for lives/waves/counters later. A new panel that covers a HUD area must not be masked out. Screens full of moving sprites/effects are negative/challenge cases, not proof of a popup.

## Tracking and dedupe

Track region identity, bounds, appearance/disappearance, and content change. Replacing text inside an unchanged box opens a new content event. Closing and reopening identical text creates another occurrence. Share image/text storage via content IDs without deleting occurrence timestamps. Never use only a whole-frame perceptual hash or text embedding to decide two small text regions are identical.

Do not reject one-frame candidates or require a fixed minimum duration. A confidence threshold should retain an uncertain candidate with a review flag. One-second summaries reference event IDs; they do not round start/end times or merge distinct contents. No universal event-count cap.

## Evidence selection and context

Select within the observed interval, favoring readable text, panel completeness, low blur, and non-faded appearance. A globally sharp gameplay background is not a sufficient best-frame metric. OCR confidence is a score, not ground truth. Keep alternatives when uncertain, and retain evidence even when recognition is unavailable or wrong.

Record context ranges before/after each event, clipped to source bounds, plus a sparse whole-video overview so silent gameplay without text still has context. Generate context images/clips lazily from exact references. Offline input can be re-read: no need to keep seconds of raw 1440p60 RGB in RAM. Use a bounded low-resolution ring and source-frame references, or a bounded disk cache. Overlap and reuse shared context assets.

## Optional speech and providers

Visual analysis must run with no audio/network/key. The chosen first external speech provider is Groq Whisper; its API supports timestamped transcription and large-file chunking [R5]. Extract the selected audio track explicitly; chunk with offsets and overlap dedupe. Preserve the original language, source/channel metadata, quality warnings, and silence uncertainty. Do not claim speech timestamps are frame-exact.

Groq is opt-in and sends audio off-device. Provider failure produces a partial speech stage without invalidating completed visual evidence. Only provider-specific adapters handle credentials or retries; bounded retry/cost controls are required.

## Packaging and interfaces

Target layout when implementation starts: `src/bscout/{ingest,signals,tracking,evidence,providers,packet}`, CLI at `src/bscout/cli.py`, tests by layer. Do not add empty framework code just to mirror this diagram.

Tauri supports external sidecars and drag/drop paths [R6, R7]. Package one engine, exchange job/status messages through bounded IPC, allowlist paths, and avoid exposing an unauthenticated local command-execution server. Packaging of Python/FFmpeg/model assets is an explicit later proof, not solved by selecting Tauri.

See [REFERENCES.md](REFERENCES.md) for R1-R7 and [ACCEPTANCE.md](ACCEPTANCE.md) for gates.
