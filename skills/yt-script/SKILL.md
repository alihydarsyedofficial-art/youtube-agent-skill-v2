---
name: yt-script
version: 2.0.0
description: High-retention multimodal scriptwriting with automated 6-axis hook scoring.
executable: skills/yt-script/hookscore.py
---

# Multimodal Scriptwriting & Hook Engineering (yt-script)

## Mandatory Workflow
1. Load creator linguistic rules from templates/voice.md.
2. Draft the First 35 Seconds (The Hook) using the 4-Beat Hook Formula:
   - Beat 1 (0-5s): Immediately validate the thumbnail/title premise. Zero greetings.
   - Beat 2 (5-15s): Challenge default assumptions with stakes or contrarian framing.
   - Beat 3 (15-25s): Show proof or benchmark velocity upfront.
   - Beat 4 (25-35s): Plant an unresolved open loop leading into Act 1.
3. Run Deterministic Verification:
   `python skills/yt-script/hookscore.py --text "<HOOK_TEXT>"`
   Do not proceed until composite_score >= 80.0 and friction_violations is empty.
4. Embed Multimodal Cues: Insert [VISUAL: ...], [B-ROLL: ...], [SFX: ...], or [TEXT: ...] markers every 4-6 seconds throughout the entire script.
5. The Native Bridge Ending: Never say "In conclusion" or "Thanks for watching." Transition directly from the final point into the problem solved by the linked end-screen video.
