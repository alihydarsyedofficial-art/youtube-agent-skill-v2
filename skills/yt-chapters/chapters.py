#!/usr/bin/env python3
"""
chapters.py - Semantic Topic-Shift Chapter Generator & YouTube Compliance Validator
Detects topic transitions in timestamped transcripts, extracts high-intent SEO labels,
and enforces YouTube's strict chapter requirements.
"""

import argparse
import json
import re
import sys
from collections import Counter
from typing import Any, Dict, List, Tuple

STOPWORDS = {
    "the", "and", "to", "of", "in", "is", "it", "that", "for", "on", "you", "this",
    "with", "are", "as", "be", "at", "or", "from", "by", "an", "have", "but", "not",
    "what", "all", "were", "we", "when", "your", "can", "said", "there", "use", "each",
    "which", "she", "do", "how", "their", "if", "will", "up", "other", "about", "out",
    "many", "then", "them", "these", "so", "some", "her", "would", "make", "like",
    "into", "him", "has", "two", "more", "go", "no", "way", "could", "my", "than",
    "been", "call", "who", "its", "now", "find", "long", "down", "day", "did", "get",
    "come", "made", "may", "part", "going", "really", "actually", "basically", "just"
}

TRANSITION_CUES = re.compile(
    r"\b(next up|step \d+|number \d+|moving on|now let's|secondly|finally|the biggest|another key|part \d+)\b",
    re.I,
)


def parse_ts_to_sec(ts: str) -> int:
    parts = [int(float(p)) for p in ts.replace(",", ".").split(":")]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return parts[0] * 60 + parts[1]


def format_chapter_ts(sec: int) -> str:
    hrs = sec // 3600
    mins = (sec % 3600) // 60
    secs = sec % 60
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


def extract_seo_label(text: str) -> str:
    clean = re.sub(r"\[.*?\]", "", text)
    words = [
        w.capitalize()
        for w in re.findall(r"\b[a-zA-Z]{4,}\b", clean.lower())
        if w not in STOPWORDS
    ]
    if not words:
        return "Core Breakdown"
    top_terms = [term for term, _ in Counter(words).most_common(4)]
    return " ".join(top_terms[:3])


def generate_chapters(transcript: str, min_gap_sec: int = 45) -> Dict[str, Any]:
    line_pattern = re.compile(r"\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?\s*(.+)")
    entries: List[Tuple[int, str]] = []

    for line in transcript.strip().splitlines():
        m = line_pattern.match(line.strip())
        if m:
            entries.append((parse_ts_to_sec(m.group(1)), m.group(2).strip()))

    if not entries:
        return {"error": "Provide lines with [MM:SS] or [HH:MM:SS] timestamps."}

    chapters: List[Dict[str, Any]] = [
        {"timestamp_sec": 0, "timestamp": "00:00", "title": "Hook & Core Premise"}
    ]
    last_chapter_sec = 0
    accumulated_text: List[str] = []

    for sec, text in entries:
        accumulated_text.append(text)
        has_transition = bool(TRANSITION_CUES.search(text))
        elapsed = sec - last_chapter_sec

        if (has_transition and elapsed >= max(15, min_gap_sec // 2)) or elapsed >= min_gap_sec:
            label = extract_seo_label(" ".join(accumulated_text[-3:]))
            chapters.append({
                "timestamp_sec": sec,
                "timestamp": format_chapter_ts(sec),
                "title": label,
            })
            last_chapter_sec = sec
            accumulated_text = []

    # Validate YouTube Compliance Rules
    validation_errors: List[str] = []
    if chapters[0]["timestamp_sec"] != 0:
        validation_errors.append("First chapter must start at 00:00.")
    if len(chapters) < 3:
        validation_errors.append("YouTube requires a minimum of 3 chapters.")
    for i in range(1, len(chapters)):
        if chapters[i]["timestamp_sec"] - chapters[i - 1]["timestamp_sec"] < 10:
            validation_errors.append(
                f"Chapter '{chapters[i]['title']}' is less than 10 seconds after previous chapter."
            )

    formatted_block = "\n".join(f"{c['timestamp']} {c['title']}" for c in chapters)

    return {
        "youtube_compliant": len(validation_errors) == 0,
        "chapter_count": len(chapters),
        "validation_errors": validation_errors,
        "chapters": chapters,
        "copy_paste_description_block": formatted_block,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="YouTube SEO Chapter Generator & Validator")
    parser.add_argument("--file", type=str, help="Path to timestamped transcript")
    parser.add_argument("--text", type=str, help="Raw timestamped transcript")
    parser.add_argument("--min-gap", type=int, default=45, help="Target seconds between chapters")
    parser.add_argument("--json-stdin", action="store_true", help="Read JSON from stdin")
    args = parser.parse_args()

    if args.json_stdin:
        payload = json.loads(sys.stdin.read())
        text = payload.get("text", "")
        min_gap = int(payload.get("min_gap", 45))
    elif args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
        min_gap = args.min_gap
    elif args.text:
        text = args.text
        min_gap = args.min_gap
    else:
        parser.print_help()
        sys.exit(1)

    print(json.dumps(generate_chapters(text, min_gap_sec=min_gap), indent=2))


if __name__ == "__main__":
    main()