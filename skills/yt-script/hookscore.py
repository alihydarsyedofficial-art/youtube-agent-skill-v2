#!/usr/bin/env python3
"""
hookscore.py - Deterministic 6-Axis YouTube Hook Scoring & Drop-Off Predictor
Evaluates:
  1. First-5-Second Velocity (No throat-clearing, immediate stakes)
  2. Psychological Trigger Density (Curiosity, Contrarian, Stakes, Proof)
  3. Open-Loop Architecture (Unresolved questions & forward momentum)
  4. Cognitive Ease (Syllable-per-word & sentence length variability)
  5. Multimodal Synchronization ([VISUAL], [SFX], [B-ROLL] density)
  6. Friction Penalty Deduction (Channel intros, begging for subs early)
"""

import argparse
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List


def load_hooks_config() -> Dict[str, Any]:
    config_path = Path(__file__).parent / "hooks.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "archetypes": {},
        "visual_markers": ["[VISUAL:", "[B-ROLL:", "[SFX:", "[TEXT:"],
        "friction_penalties": ["hey guys", "welcome back", "like and subscribe"],
    }


def count_syllables(word: str) -> int:
    word = re.sub(r"[^a-z]", "", word.lower())
    if not word:
        return 0
    if len(word) <= 3:
        return 1
    word = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", word)
    word = re.sub(r"^y", "", word)
    vowels = re.findall(r"[aeiouy]{1,2}", word)
    return max(1, len(vowels))


def score_hook(text: str, target_wpm: int = 155) -> Dict[str, Any]:
    config = load_hooks_config()
    raw_lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    clean_spoken = re.sub(r"\[.*?\]", "", text).strip()
    words = re.findall(r"\b[\w']+\b", clean_spoken)
    word_count = len(words)

    if word_count == 0:
        return {"error": "Empty spoken hook text provided.", "composite_score": 0}

    duration_sec = round((word_count / target_wpm) * 60, 1)
    lower_spoken = clean_spoken.lower()
    first_15_words = " ".join(words[:15]).lower()

    # 1. Friction Penalty Check (First 15 words are critical)
    friction_hits: List[str] = []
    for phrase in config.get("friction_penalties", []):
        if phrase in lower_spoken:
            friction_hits.append(phrase)

    # 2. Psychological Trigger Matching
    matched_triggers: List[Dict[str, Any]] = []
    trigger_raw_points = 0.0
    for archetype, data in config.get("archetypes", {}).items():
        weight = data.get("weight", 1.0)
        for pattern in data.get("patterns", []):
            if pattern in lower_spoken:
                in_first_5_sec = pattern in first_15_words
                bonus = 1.35 if in_first_5_sec else 1.0
                pts = round(12.0 * weight * bonus, 2)
                trigger_raw_points += pts
                matched_triggers.append({
                    "archetype": archetype,
                    "pattern": pattern,
                    "in_first_5s": in_first_5_sec,
                    "points": pts,
                })
    trigger_score = min(30.0, trigger_raw_points)

    # 3. Open-Loop & Curiosity Mechanics (Questions, Contrast Pivot Words)
    question_count = clean_spoken.count("?")
    contrast_pivots = len(
        re.findall(
            r"\b(but|however|except|until|turns out|plot twist|instead|yet)\b",
            lower_spoken,
        )
    )
    open_loop_score = min(20.0, (question_count * 7.5) + (contrast_pivots * 4.5))

    # 4. Cognitive Ease & Rhythm (Target: <1.45 syllables/word, 8-14 words/sentence)
    sentences = [s.strip() for s in re.split(r"[.!?]+", clean_spoken) if s.strip()]
    avg_sentence_len = word_count / max(1, len(sentences))
    avg_syllables = sum(count_syllables(w) for w in words) / word_count

    rhythm_score = 20.0
    if avg_sentence_len > 18:
        rhythm_score -= min(10.0, (avg_sentence_len - 18) * 1.2)
    elif avg_sentence_len < 5:
        rhythm_score -= 3.0
    if avg_syllables > 1.55:
        rhythm_score -= min(8.0, (avg_syllables - 1.55) * 20.0)
    rhythm_score = max(0.0, round(rhythm_score, 2))

    # 5. Multimodal Visual/Audio Cue Density (Target: 1 cue every 4-6 seconds)
    visual_cues = re.findall(r"\[(?:VISUAL|B-ROLL|SFX|TEXT|CUT|ZOOM)[^\]]*\]", text, re.I)
    expected_cues = max(1.0, duration_sec / 5.0)
    cue_ratio = len(visual_cues) / expected_cues
    multimodal_score = min(15.0, round(cue_ratio * 15.0, 2))

    # 6. First-5-Second Velocity Score (Immediate stakes / numbers / active verbs)
    has_number_early = bool(re.search(r"\b\d+\b", first_15_words))
    has_you_early = bool(re.search(r"\b(you|your)\b", first_15_words))
    velocity_score = 7.0
    if has_number_early:
        velocity_score += 4.0
    if has_you_early:
        velocity_score += 4.0
    if friction_hits and any(f in first_15_words for f in friction_hits):
        velocity_score = 0.0
    velocity_score = min(15.0, velocity_score)

    # Deduct Friction Penalties
    penalty_deduction = len(friction_hits) * 12.0
    raw_total = (
        trigger_score
        + open_loop_score
        + rhythm_score
        + multimodal_score
        + velocity_score
        - penalty_deduction
    )
    composite_score = round(max(0.0, min(100.0, raw_total)), 1)

    # Predict 30-second retention percentage based on composite score
    predicted_30s_retention = round(42.0 + (composite_score * 0.43), 1)

    directives: List[str] = []
    if friction_hits:
        directives.append(
            f"CRITICAL: Delete throat-clearing phrases immediately: {friction_hits}."
        )
    if not has_you_early:
        directives.append(
            "Inject viewer-centric framing ('you' or 'your') within the first 12 words."
        )
    if len(visual_cues) < math.floor(expected_cues):
        directives.append(
            f"Add {math.ceil(expected_cues - len(visual_cues))} more [VISUAL:] or [SFX:] cues to prevent visual static in the first {duration_sec}s."
        )
    if open_loop_score < 10:
        directives.append(
            "Plant an explicit unresolved question or 'But here is the catch...' pivot before second 20."
        )
    if avg_sentence_len > 16:
        directives.append(
            f"Shorten sentence length (currently {round(avg_sentence_len, 1)} words/sentence; target 9-13 for punchy cadence)."
        )

    return {
        "composite_score": composite_score,
        "grade": (
            "S-Tier (Viral Ready)"
            if composite_score >= 88
            else "A-Tier (Strong)"
            if composite_score >= 76
            else "B-Tier (Needs Polish)"
            if composite_score >= 62
            else "C-Tier (High Drop-Off Risk)"
        ),
        "predicted_30s_retention_pct": predicted_30s_retention,
        "metrics": {
            "spoken_word_count": word_count,
            "estimated_duration_sec": duration_sec,
            "avg_sentence_length": round(avg_sentence_len, 2),
            "avg_syllables_per_word": round(avg_syllables, 2),
            "visual_audio_cues_detected": len(visual_cues),
        },
        "dimension_breakdown": {
            "psychological_triggers_max30": round(trigger_score, 2),
            "open_loop_tension_max20": round(open_loop_score, 2),
            "cognitive_rhythm_max20": rhythm_score,
            "multimodal_sync_max15": multimodal_score,
            "first_5s_velocity_max15": velocity_score,
            "friction_penalty_deduction": -penalty_deduction,
        },
        "matched_triggers": matched_triggers,
        "friction_violations": friction_hits,
        "rewrite_directives": directives,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="6-Axis YouTube Hook Scorer")
    parser.add_argument("--text", type=str, help="Direct hook script text")
    parser.add_argument("--file", type=str, help="Path to file containing hook text")
    parser.add_argument("--wpm", type=int, default=155, help="Speaking rate WPM")
    parser.add_argument("--json-stdin", action="store_true", help="Read JSON payload from stdin")
    args = parser.parse_args()

    if args.json_stdin:
        payload = json.loads(sys.stdin.read())
        text = payload.get("text", "")
        wpm = int(payload.get("wpm", 155))
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

    result = score_hook(text, target_wpm=wpm)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()