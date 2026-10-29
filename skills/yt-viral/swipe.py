#!/usr/bin/env python3
import sys
import json
import re

def analyze_swipe():
    try:
        raw_input = sys.stdin.read()
        payload = json.loads(raw_input) if raw_input.strip() else {}
    except Exception:
        payload = {}

    title = payload.get("title", "Untitled Outlier Cartoon Video")
    text = payload.get("text", "Everyone thinks kids content is easy. They are wrong. Watch what happens in the first 5 seconds.")
    
    clean_text = re.sub(r'\[.*?\]', ' ', text).strip()
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_text) if s.strip()]
    
    if not sentences:
        sentences = [clean_text]

    words = clean_text.split()
    total_sentences = len(sentences)
    hook_end = max(1, round(total_sentences * 0.14))
    setup_end = max(hook_end + 1, round(total_sentences * 0.32))
    climax_start = max(setup_end + 1, round(total_sentences * 0.82))

    open_loops = [s for s in sentences if "?" in s or re.search(r'\b(wait until|secret|watch what happens|turns out|surprise)\b', s, re.I)]

    result = {
        "status": "success",
        "engine": "python-viral-swipe-deconstructor",
        "original_title": title,
        "reusable_title_skeleton": re.sub(r'\b\d+\b', '[NUMBER]', title),
        "structural_metrics": {
            "total_word_count": len(words),
            "estimated_duration_min": round(len(words) / 150.0, 2),
            "total_sentences": total_sentences,
            "open_loops_detected": len(open_loops)
        },
        "four_act_dna": {
            "act_1_hook_0_14pct": {"opening_anchor": " ".join(sentences[:hook_end])[:140]},
            "act_2_escalation_14_32pct": {"opening_anchor": " ".join(sentences[hook_end:setup_end])[:140]},
            "act_3_core_execution_32_82pct": {"opening_anchor": " ".join(sentences[setup_end:climax_start])[:140]},
            "act_4_payoff_82_100pct": {"opening_anchor": " ".join(sentences[climax_start:])[:140]}
        },
        "extracted_open_loops": open_loops[:5]
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    analyze_swipe()