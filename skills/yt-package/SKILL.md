---
name: yt-package
version: 2.0.0
description: High-CTR Title and Thumbnail pairing with pixel-width truncation and synergy scoring.
executable: skills/yt-package/title.py
---

# High-CTR Title & Thumbnail Synergy Packaging (yt-package)

## Execution Protocol
1. Generate 10 candidate Title + Thumbnail pairs across Curiosity, Proof, and Loss-Aversion angles.
2. Enforce Zero Redundancy: Thumbnail text (max 4 words) must complement, never repeat, the video title.
3. Score candidates with `python skills/yt-package/title.py --title "Title" --thumb "Thumb Text"` and select pairs scoring >= 82.0.
