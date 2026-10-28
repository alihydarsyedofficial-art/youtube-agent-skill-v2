---
name: yt-audit
version: 2.0.0
description: Full-channel diagnostic audit identifying CTR, 30-second hook retention, AVD, and session-end conversion bottlenecks.
---

# YouTube Channel Diagnostic & Bottleneck Audit (`yt-audit`)

## Purpose
Diagnose why a channel or video is underperforming by isolating the exact stage of the viewer funnel where impressions or viewers leak.

## The 4-Stage Diagnostic Funnel
Evaluate every video or channel cohort against these deterministic thresholds:
1. **Packaging Efficiency (CTR & Impressions Velocity):**
   - **Benchmark:** `> 6.5%` Browse/Suggested CTR.
   - **Diagnosis if `< 4.5%`:** Topic TAM (Total Addressable Market) is too narrow, or Title + Thumbnail fails the sub-second curiosity check. Route immediately to `yt-package`.
2. **First-30-Second Hook Survival:**
   - **Benchmark:** `>= 70%` of viewers still watching at `0:30`.
   - **Diagnosis if `< 60%`:** Clickbait mismatch (first 5 seconds don't validate the thumbnail) or throat-clearing intro. Route to `yt-script` and run `hookscore.py`.
3. **Body Pacing & Average Percentage Viewed (APV):**
   - **Benchmark:** `>= 50%` APV on 8–15 minute videos.
   - **Diagnosis if `< 40%`:** Monotone mid-video plateaus (>25s without visual state changes) or premature payoff. Route to `yt-retention` (`retention.py`).
4. **End-Screen Binge Velocity:**
   - **Benchmark:** `>= 8%` end-screen click-through rate.
   - **Diagnosis if `< 3%`:** Verbal sign-off signals ("Thanks for watching, guys!") trigger mass exit before the bridge hook.

## Required Audit Output Schema
Always output:
- **Primary Bottleneck Stage** (Single highest-leverage constraint)
- **Outlier vs. Underperformer Delta Table**
- **3 Immediate Surgical Fixes** ranked by expected view-lift multiplier.