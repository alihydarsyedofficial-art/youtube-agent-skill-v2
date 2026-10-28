---
name: yt-edit
version: 2.0.0
description: Post-production jump-cut automation, dead-air removal, and visual rhythm cues.
executable: skills/yt-edit/deadair.py
---

# Post-Production Cut Logic & Dead-Air Elimination (yt-edit)

## Execution Protocol
1. Run `python skills/yt-edit/deadair.py --file raw_captions.srt --max-gap 0.40`
2. Cut pauses > 0.25s in the first 60 seconds and strip all flagged filler words.
3. Execute the generated ffmpeg_auto_cut_command to remove dead air automatically.
