---
name: yt-plan
version: 2.0.0
description: Content ideation, outlier multiplier validation, and binge-loop series planning.
---

# Strategic Content Ideation & Roadmap Engine (`yt-plan`)

## Purpose
Prevent wasted production hours by validating video concepts *before* scripting using Outlier Multiplier math and Viewer Avatar Buckets.

## Execution Protocol
1. **Outlier Validation Rule (`>= 3.0x`):**
   - Never greenlight a topic unless an adjacent video achieved at least **3x the channel's median views** within the last 90 days.
2. **Packaging-First Mandate:**
   - Before approving any topic, generate **3 distinct Title + Thumbnail pairs** and verify they score `>= 80` in `skills/yt-package/title.py`. If you cannot package it, discard the idea.
3. **The 3 Bucket Distribution (30-Day Calendar):**
   - **60% Broad TAM (Growth):** High-curiosity concepts understandable by a cold viewer on the Home Feed.
   - **25% Core Niche (Authority):** Tactical depth that builds trust and high session watch time.
   - **15% High-Intent Conversion (Search/Evergreen):** Problem-solving queries captured via `yt-seo`.
4. **Binge-Chain Architecture:**
   - Every video plan must specify its **Target Next Video** so the script's ending naturally opens a loop solved by the next upload.