---
name: yt-retention
version: 2.0.0
description: Pacing optimization, flatline detection, and dopamine reset scheduling.
executable: skills/yt-retention/retention.py
---

# Retention Pacing & Dopamine Loop Engineering (yt-retention)

## Execution Protocol
1. Run `python skills/yt-retention/retention.py --file draft_script.txt`
2. Resolve every CRITICAL_FLATLINE alert where consecutive_static_sec >= 22.0 by inserting a visual state change, audio reset, or mid-roll open loop.
3. Re-run until flatline_count == 0 and predicted_avd_pct >= 52.0.
