#!/usr/bin/env python3
"""
retention.py - Full-Timeline Retention Curve Simulator & Pattern Interrupt Engine
Models attention decay across 15-second windows using exponential decay with
dopamine re-engagement impulses from visual changes, open loops, and story pivots.
"""

import argparse
import json
import math
import re
import sys
from typing import Any, Dict, List


INTERRUPT_MARKERS = re.compile(
    r"\[(?:VISUAL|B-ROLL|SFX|CUT|GRAPHIC|DEMO|SCREEN|TEXT)[^\]]*\]", re.I
)
DOPAMINE_PIVOTS = re.compile(
    r"\b(but wait|here's why|the crazy part|mistake|secret|step \d+|number \d+|for example|watch what happens)\b",
    re.I,
)


def simulate_retention(script_text: str, wpm: int = 150) -> Dict[str, Any]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", script_text.strip()) if p.strip()]
    if not paragraphs:
        return {"error": "Empty script provided.", "overall_retention_score": 0}

    words_per_sec = wpm / 60.0
    timeline_windows: List[Dict[str, Any]] = []
    flatline_alerts: List[Dict[str, Any]] = []

    current_sec = 0.0
    current_retention = 100.0
    consecutive_static_sec = 0.0

    for idx, block in enumerate(paragraphs):
        visual_cues = INTERRUPT_MARKERS.findall(block)
        pivots = DOPAMINE_PIVOTS.findall(block)
        questions = block.count("?")

        spoken_clean = INTERRUPT_MARKERS.sub("", block)
        words = re.findall(r"\b[\w']+\b", spoken_clean)
        word_count = len(words)
        if word_count == 0:
            continue

        block_duration = round(word_count / words_per_sec, 1)
        start_sec = round(current_sec, 1)
        end_sec = round(current_sec + block_duration, 1)

        # Calculate natural decay vs re-engagement impulse
        is_hook_zone = start_sec < 30.0
        base_decay_rate = 0.42 if is_hook_zone else 0.14  # % per second without stimuli

        stimulus_score = (len(visual_cues) * 1.8) + (len(pivots) * 1.5) + (questions * 1.2)
        expected_stimuli = max(1.0, block_duration / 8.0)
        stimulus_density = round(stimulus_score / expected_stimuli, 2)

        effective_decay = max(0.02, base_decay_rate / max(0.5, stimulus_density))
        drop_pct = round(min(18.0, effective_decay * block_duration), 2)
        current_retention = round(max(12.0, current_retention - drop_pct), 1)

        if len(visual_cues) == 0 and len(pivots) == 0:
            consecutive_static_sec += block_duration
        else:
            consecutive_static_sec = 0.0

        risk_level = "LOW"
        if consecutive_static_sec >= 22.0 or stimulus_density < 0.45:
            risk_level = "CRITICAL_FLATLINE"
            flatline_alerts.append({
                "block_index": idx + 1,
                "timestamp_range": f"{format_ts(start_sec)} - {format_ts(end_sec)}",
                "static_duration_sec": round(consecutive_static_sec, 1),
                "prescription": (
                    "Insert a [B-ROLL:] state change, on-screen graphic, or a mid-roll open loop ('And this leads to the biggest trap...')."
                ),
                "excerpt": spoken_clean[:90] + ("..." if len(spoken_clean) > 90 else ""),
            })
        elif stimulus_density < 0.75:
            risk_level = "MODERATE_DRIFT"

        timeline_windows.append({
            "block": idx + 1,
            "time_range": f"{format_ts(start_sec)}-{format_ts(end_sec)}",
            "duration_sec": block_duration,
            "word_count": word_count,
            "visual_cues": len(visual_cues),
            "verbal_pivots": len(pivots) + questions,
            "stimulus_density": stimulus_density,
            "predicted_audience_remaining_pct": current_retention,
            "risk": risk_level,
        })

        current_sec = end_sec

    avg_view_duration_pct = (
        round(
            sum(w["predicted_audience_remaining_pct"] for w in timeline_windows)
            / len(timeline_windows),
            1,
        )
        if timeline_windows
        else 0.0
    )

    return {
        "total_duration_sec": round(current_sec, 1),
        "total_duration_formatted": format_ts(current_sec),
        "predicted_avd_pct": avg_view_duration_pct,
        "final_retention_pct": current_retention,
        "flatline_count": len(flatline_alerts),
        "pacing_verdict": (
            "ELITE RETENTION (>=55% AVD)"
            if avg_view_duration_pct >= 55
            else "COMPETITIVE (42-54% AVD)"
            if avg_view_duration_pct >= 42
            else "HIGH DROP-OFF RISK (<42% AVD)"
        ),
        "flatline_interventions": flatline_alerts,
        "timeline_simulation": timeline_windows,
    }


def format_ts(seconds: float) -> str:
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


def main() -> None:
    parser = argparse.ArgumentParser(description="YouTube Retention Curve Simulator")
    parser.add_argument("--file", type=str, help="Path to full script file")
    parser.add_argument("--text", type=str, help="Raw script text")
    parser.add_argument("--wpm", type=int, default=150, help="Words per minute")
    parser.add_argument("--json-stdin", action="store_true", help="Read JSON from stdin")
    args = parser.parse_args()

    if args.json_stdin:
        payload = json.loads(sys.stdin.read())
        text = payload.get("text", "")
        wpm = int(payload.get("wpm", 150))
    elif args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
        wpm = args.wpm
    elif args.text:
        text = args.text
        wpm = args.wpm
    else:
        parser.print_help()
        sys.exit(1)

    print(json.dumps(simulate_retention(text, wpm=wpm), indent=2))


if __name__ == "__main__":
    main()