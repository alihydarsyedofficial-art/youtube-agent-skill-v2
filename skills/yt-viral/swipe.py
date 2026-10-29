#!/usr/bin/env python3
import argparse
import json
import re
import statistics
import sys
from typing import Any, Dict, List

def extract_title_skeleton(title: str) -> str:
    skeleton = re.sub(r"\$[\d,\.]+[KkMmBb]?", "[$_AMOUNT]", title)
    skeleton = re.sub(r"\b\d+\s*(days|hours|minutes|months|years|seconds|steps|tools|ways)\b", r"[NUMBER] \1", skeleton, flags=re.I)
    skeleton = re.sub(r"\b\d+\b", "[NUMBER]", skeleton)
    return skeleton

def deconstruct_viral_transcript(title: str, transcript: str) -> Dict[str, Any]:
    clean_text = re.sub(r"\[.*?\]", " ", transcript or "").strip()
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean_text) if s.strip()]
    if not sentences:
        return {"error": "Empty transcript provided."}
    total_sentences = len(sentences)
    words = re.findall(r"\b[\w']+\b", clean_text)
    total_words = len(words)
    sent_lengths = [len(re.findall(r"\b[\w']+\b", s)) for s in sentences]
    hook_end = max(1, int(round(total_sentences * 0.14)))
    setup_end = max(hook_end + 1, int(round(total_sentences * 0.32)))
    climax_start = max(setup_end + 1, int(round(total_sentences * 0.82)))
    acts = {
        "act_1_hook_0_14pct": " ".join(sentences[:hook_end]),
        "act_2_escalation_14_32pct": " ".join(sentences[hook_end:setup_end]),
        "act_3_core_execution_32_82pct": " ".join(sentences[setup_end:climax_start]),
        "act_4_payoff_and_bridge_82_100pct": " ".join(sentences[climax_start:]),
    }
    open_loops: List[str] = [
        s for s in sentences
        if "?" in s or re.search(r"\b(wait until|later|in a minute|secret|but first|here is the catch|turns out|plot twist)\b", s, re.I)
    ]
    skeleton = extract_title_skeleton(title)
    avg_len = round(total_words / max(1, total_sentences), 2)
    burstiness = round(statistics.pstdev(sent_lengths), 2) if len(sent_lengths) > 1 else 0.0
    return {
        "original_title": title,
        "reusable_title_skeleton": skeleton,
        "structural_metrics": {
            "total_word_count": total_words,
            "estimated_duration_min": round(total_words / 150.0, 2),
            "total_sentences": total_sentences,
            "avg_words_per_sentence": avg_len,
            "sentence_burstiness_std_dev": burstiness,
            "open_loops_detected": len(open_loops),
        },
        "four_act_dna": {
            k: {"word_count": len(re.findall(r"\b[\w']+\b", v)), "opening_anchor": v[:140] + ("..." if len(v) > 140 else "")}
            for k, v in acts.items()
        },
        "extracted_open_loops": open_loops[:8],
        "niche_transfer_blueprint": [
            f"1. Title Formula: Adapt '{skeleton}' to your target topic and verify score >= 82 in title.py.",
            f"2. Cadence Target: Maintain ~{avg_len} words/sentence with a burstiness std-dev near {burstiness}.",
            f"3. Tension Pacing: Plant at least {max(3, len(open_loops))} explicit open loops across the script.",
            "4. Handoff Ending: Cut directly from Act 4 payoff into the next-video bridge without verbal sign-offs.",
        ],
    }

def main() -> None:
    parser = argparse.ArgumentParser(description="Viral Outlier Structural DNA Extractor")
    parser.add_argument("--title", type=str, default="Untitled Outlier", help="Viral video title")
    parser.add_argument("--file", type=str, help="Path to viral transcript file")
    parser.add_argument("--text", type=str, help="Raw transcript text")
    parser.add_argument("--json-stdin", action="store_true", help="Read JSON from stdin")
    args = parser.parse_args()
    if args.json_stdin:
        payload = json.loads(sys.stdin.read() or "{}")
        title = str(payload.get("title", "Untitled Outlier"))
        text = str(payload.get("text", ""))
    elif args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
        title = args.title
    elif args.text:
        text = args.text
        title = args.title
    else:
        parser.print_help()
        sys.exit(1)
    print(json.dumps(deconstruct_viral_transcript(title, text), indent=2))

if __name__ == "__main__":
    main()
