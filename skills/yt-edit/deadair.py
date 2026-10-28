#!/usr/bin/env python3
"""
deadair.py - Transcript Silence & Crutch-Word Cutter + Automated FFmpeg EDL Builder
Parses SRT or timestamped lines, flags gaps > threshold, detects verbal filler bloat,
and outputs an executable FFmpeg select/aselect command for automated jump-cutting.
"""

import argparse
import json
import re
import sys
from typing import Any, Dict, List, Tuple


FILLER_REGEX = re.compile(
    r"\b(um+|uh+|erm+|like i said|you know what i mean|basically|literally|to be honest|sort of|kind of)\b",
    re.I,
)

SRT_BLOCK_REGEX = re.compile(
    r"(\d+)\s*\n(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*\n([\s\S]*?)(?=\n{2,}|\Z)"
)


def parse_timecode(tc: str) -> float:
    tc = tc.replace(",", ".")
    parts = tc.split(":")
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])


def format_tc(sec: float) -> str:
    hrs = int(sec // 3600)
    mins = int((sec % 3600) // 60)
    secs = sec % 60
    return f"{hrs:02d}:{mins:02d}:{secs:06.3f}"


def analyze_deadair(
    transcript_raw: str, max_gap_sec: float = 0.45, pad_sec: float = 0.06
) -> Dict[str, Any]:
    matches = SRT_BLOCK_REGEX.findall(transcript_raw.strip())
    segments: List[Tuple[float, float, str]] = []

    if matches:
        for _, start_tc, end_tc, text in matches:
            clean_text = " ".join(text.splitlines()).strip()
            segments.append((parse_timecode(start_tc), parse_timecode(end_tc), clean_text))
    else:
        # Fallback: parse simple [MM:SS] or [HH:MM:SS] lines
        line_re = re.compile(r"\[?(\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?)\]?\s*(.*)")
        parsed_lines: List[Tuple[float, str]] = []
        for line in transcript_raw.splitlines():
            m = line_re.match(line.strip())
            if m:
                raw_t = m.group(1)
                if raw_t.count(":") == 1:
                    raw_t = "00:" + raw_t
                parsed_lines.append((parse_timecode(raw_t), m.group(2).strip()))
        for i, (st, txt) in enumerate(parsed_lines):
            words = len(txt.split())
            est_dur = max(1.0, words / 2.6)
            next_st = parsed_lines[i + 1][0] if i + 1 < len(parsed_lines) else st + est_dur
            segments.append((st, min(next_st, st + est_dur), txt))

    if not segments:
        return {"error": "No valid timestamped segments found in input."}

    dead_air_cuts: List[Dict[str, Any]] = []
    filler_alerts: List[Dict[str, Any]] = []
    keep_intervals: List[Tuple[float, float]] = []

    total_dead_air = 0.0
    prev_end = 0.0

    for idx, (start, end, text) in enumerate(segments):
        gap = round(start - prev_end, 3)
        if gap > max_gap_sec:
            cut_start = round(prev_end + pad_sec, 3) if prev_end > 0 else 0.0
            cut_end = round(max(cut_start, start - pad_sec), 3)
            saved = round(cut_end - cut_start, 3)
            if saved > 0.1:
                total_dead_air += saved
                dead_air_cuts.append({
                    "gap_index": len(dead_air_cuts) + 1,
                    "cut_from": format_tc(cut_start),
                    "cut_to": format_tc(cut_end),
                    "seconds_removed": saved,
                })

        fillers = FILLER_REGEX.findall(text)
        if fillers:
            filler_alerts.append({
                "segment_index": idx + 1,
                "timestamp": format_tc(start),
                "fillers_found": [f.lower() for f in fillers],
                "line": text,
            })

        keep_start = max(0.0, round(start - pad_sec, 3))
        keep_end = round(end + pad_sec, 3)
        if keep_intervals and keep_start <= keep_intervals[-1][1]:
            keep_intervals[-1] = (keep_intervals[-1][0], max(keep_intervals[-1][1], keep_end))
        else:
            keep_intervals.append((keep_start, keep_end))

        prev_end = end

    total_original_sec = round(segments[-1][1], 2)
    total_tightened_sec = round(total_original_sec - total_dead_air, 2)

    # Generate FFmpeg expression
    between_clauses = [f"between(t,{s},{e})" for s, e in keep_intervals[:60]]
    select_expr = "+".join(between_clauses)
    ffmpeg_cmd = (
        f'ffmpeg -i input.mp4 -vf "select=\'{select_expr}\',setpts=N/FRAME_RATE/TB" '
        f'-af "aselect=\'{select_expr}\',asetpts=N/SR/TB" output_tightened.mp4'
    )

    return {
        "original_duration_sec": total_original_sec,
        "tightened_duration_sec": total_tightened_sec,
        "total_dead_air_removed_sec": round(total_dead_air, 2),
        "pacing_compression_pct": round((total_dead_air / max(1.0, total_original_sec)) * 100, 1),
        "dead_air_cut_count": len(dead_air_cuts),
        "filler_cluster_count": len(filler_alerts),
        "dead_air_cuts": dead_air_cuts,
        "filler_word_alerts": filler_alerts,
        "ffmpeg_auto_cut_command": ffmpeg_cmd,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Dead-Air & Filler Cutter + FFmpeg Generator")
    parser.add_argument("--file", type=str, help="Path to SRT or timestamped transcript")
    parser.add_argument("--text", type=str, help="Raw SRT/transcript string")
    parser.add_argument("--max-gap", type=float, default=0.45, help="Max allowed silence (sec)")
    parser.add_argument("--json-stdin", action="store_true", help="Read JSON from stdin")
    args = parser.parse_args()

    if args.json_stdin:
        payload = json.loads(sys.stdin.read())
        text = payload.get("text", "")
        max_gap = float(payload.get("max_gap", 0.45))
    elif args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
        max_gap = args.max_gap
    elif args.text:
        text = args.text
        max_gap = args.max_gap
    else:
        parser.print_help()
        sys.exit(1)

    print(json.dumps(analyze_deadair(text, max_gap_sec=max_gap), indent=2))


if __name__ == "__main__":
    main()