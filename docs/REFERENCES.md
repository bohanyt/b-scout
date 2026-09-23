# Architectural references and reuse policy

Checked during bootstrap on 2026-09-24. These are design references, not installed dependencies or a claim to have audited entire codebases. No upstream code/model/asset is copied in M0. Pin a commit/version, inspect LICENSE and dependency/model terms, and preserve notices before actual reuse.

| Ref | Primary source | What B-Scout takes / limitation |
|---|---|---|
| R1 | [WebDevBar/watch-video README](https://github.com/WebDevBar/watch-video/blob/master/README.md) | Agent-readable summary + frame/OCR/transcript timeline and one core/thin wrappers. README describes MIT, periodic/scene sampling and a max-frame cap. Those sampling/cap defaults are not B-Scout's brief-event gate. Exact code/license audit required before copying. |
| R2 | [PyAV time documentation](https://pyav.org/docs/stable/api/time.html) | Integer PTS and rational time-base; use source presentation timestamps. Documentation is timing reference, not a chosen package version. |
| R3 | [PaddleOCR text detection](https://www.paddleocr.ai/main/en/version3.x/module_usage/text_detection.html) | Separate text-region inference from recognition. Benchmark exact model/runtime on real UI before selection; no automatic weights bundled. |
| R4 | [PySceneDetect detector API](https://www.scenedetect.com/docs/latest/api/detectors.html) | Optional shot segmentation/rolling change scores. Minimum scene lengths are unsuitable as the only short-popup retention gate. |
| R5 | [Groq speech-to-text](https://console.groq.com/docs/speech-to-text) | Optional transcription, verbose timestamps, explicit audio track extraction, chunk-offset bookkeeping. Check current request limits when implementing; avoid fixed pricing/quota assumptions. |
| R6 | [Tauri external binaries](https://v2.tauri.app/develop/sidecar/) | Python engine can be packaged as a sidecar; per-platform packaging still needs proof. |
| R7 | [Tauri drag/drop API](https://v2.tauri.app/reference/javascript/api/namespacewebviewwindow/) | Native file-drop paths for in-place processing; constrain sidecar/path permissions. |
| R8 | [screenpipe official site](https://screenpipe.com/) | Local visual/audio history as searchable agent context. Conceptual reference, not a recording service to import or copy. |
| R9 | [FFmpeg documentation](https://ffmpeg.org/ffmpeg.html) | Media probing/extraction/stream selection and offline processing building blocks. Decoder/build/distribution choices remain explicit dependencies. |

## Earlier research leads, not approved dependencies

`coah80/youtube-mcp`, `guimatheus92/mcp-video-analyzer`, Auto-Editor, and FrameScout were mentioned during ideation. No implementation/maintenance/license claim for them is adopted by this bootstrap; inspect the actual upstream and commit before reuse. The earlier screenpipe fork URL is not treated as the canonical upstream. No private knowledge of vidIQ internals is claimed.

## Reuse record required for future PRs

For each incorporated component: canonical repository URL, exact commit/package/model version, copied or invoked paths, license file and notices, transitive/native binary/model-weight obligations, and evidence that its behavior fits our test corpus. Inspiration alone is not a license to relicense upstream code. B-Scout's MIT license covers only original repository material.

Do not implement new scene detection/decoder/OCR frameworks where a suitable maintained component passes the requirements; compose adapters. Do not import a large project just because it advertises video understanding. The custom core is temporal candidate preservation, occurrence-aware dedupe, and inspectable evidence packaging.
