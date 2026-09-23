# Ordered roadmap

| ID | Slice | Exit evidence |
|---|---|---|
| M0 | Design/contracts and agent continuity | Bootstrap checks; no runtime claim |
| BS-001 | Offline native-frame baseline | Synthetic truth set, PTS-preserving decode, regional change candidates, evidence packet, misses/performance report |
| BS-002 | Text/UI novelty and OCR adapter | Candidate-only recognition, same-box content changes, HUD/repeat handling, held-out recall/error measurements |
| BS-003 | Optional Groq speech | Explicit audio consent/selection, chunk-offset mapping, silence/no-audio/failure behavior, merged timeline |
| BS-004 | Drag-and-drop local desktop | Thin Tauri shell over same engine, in-place large-file input, review/seek/cancel workflow on Windows |
| BS-005 | Portable delivery and review | Validated packet, private Drive sync/delivery map, actual image retrieval, separate editorial annotations |
| BS-006 | Optional AI/MCP interface | Read/search/event/frame tools over existing packets; bounded on-demand context |

Only BS-001 is ready for implementation dispatch. Later entries are planned slices, not active assignments. Split a slice if its bounded proof becomes too large; do not silently add all later features to the first PR.

Source work should establish the hard temporal-evidence problem before investing in a polished shell. The GUI remains the user-facing destination, while CLI is the testable core interface.
