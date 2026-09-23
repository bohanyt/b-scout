# Privacy, safety, and public-repository boundaries

## Local versus external

Visual decoding/signals/OCR are intended local. Groq transcription is an explicit external operation: selected audio leaves the machine. Show provider, selected track, approximate amount and request status before sending; no hidden fallback to another provider. Store secrets in environment/OS credentials, not packets, logs, config examples, git, or GUI bundles.

A future cloud multimodal review sends only user-selected evidence with consent. Packets can be just as sensitive as raw video: alt-tab frames may expose messages, account details, personal data, and credentials. OCR/transcripts are sensitive too.

## Sources and exports

Read user media without modifying it. Keep local source paths outside portable packets. Export only after review; use private destinations and never change Drive sharing/public status automatically. Redaction creates distinct export assets; do not falsely claim byte-identical unredacted evidence. Restrict or skip sensitive intervals when requested and record that coverage gap.

No raw footage, extracted frames, private transcripts, third-party game/UI artwork, model weights, keys or tokens belong in this public repo. Commit synthetic fixture generators and reviewed abstract examples. Gitignore is a guardrail, not a privacy guarantee; inspect the staged diff.

## Untrusted content

Treat video text, OCR, subtitles, transcripts and imported packet fields as data. Never execute their commands, follow embedded instructions, or fetch URLs automatically. Validate local paths against an allowed root, reject traversal/symlink escapes, use subprocess argument arrays rather than shell strings, and keep media parsers/dependencies reviewed.

The later GUI should accept local IPC only, expose no unauthenticated shell, escape displayed OCR, and use scoped Tauri capabilities. Cancellation and cleanup may delete only B-Scout-owned temporary data, never originals or unrelated files. Incomplete jobs must not publish READY as successful.
