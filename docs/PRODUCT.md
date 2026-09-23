# Product and UX

## Promise

B-Scout helps editors and AI agents understand what happened in raw footage and when, especially where speech is absent. It produces inspectable evidence, not an authoritative account of everything in a video.

The distinguishing evaluation case is readable UI/text displayed for only one, three, or five frames amid moving footage and persistent HUD. Broad footage support remains the product direction: screen recordings, gameplay, interviews, events, and field research. Profiles may specialize signals without hard-coding a particular game into the core.

## Human workflow (planned)

1. Open the desktop app; drag one or more local files into the queue, or use a file picker.
2. Confirm the source, selected audio track or separate microphone file, output location, and mode. Default: visual-only; Groq is an explicit toggle with an audio-upload notice.
3. Scan in place. Show decoded/scanned frames, video-time progress, stage progress, warnings, and actual processing speed. Cancel safely; resume checkpoints must validate source and configuration identity.
4. Review a filterable timeline. Each candidate opens its best frame, crop, surrounding context, OCR status, and optional speech. Distinguish candidate / confirmed / needs-review; do not call every frame change a tutorial.
5. Export a packet or choose an existing private sync folder. User chooses what leaves the machine. Downstream review returns editorial annotations linked by event ID.

The main window should stay usable while processing. Dropping a large file must pass its local path to the engine, not copy/upload the entire file just to accept it. Originals remain unchanged. The app must disclose temporary/cache disk requirements; in-place input does not mean zero output storage.

## One engine, multiple interfaces

Python core and CLI first; a Tauri shell is the selected desktop direction. GUI, CLI, and later MCP call the same job/packet logic. No second algorithm in the UI. Desktop packaging is a later milestone, not a replacement for the promised easy workflow.

Conceptual command (NOT IMPLEMENTED):

```text
bscout analyze <local-video> --output <folder> --profile high-recall
```

## Non-goals for v0.1

No video editing/rendering, mandatory cloud video upload, always-on screen recording, general object/boss recognition, automatic clip publishing, full CapCut integration, or claim that one summary replaces source footage. Human/AI editorial judgment is separate from measured indexing.
