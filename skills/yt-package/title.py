#!/usr/bin/env python3
"""
title.py - High-CTR Title & Thumbnail Synergy Scorer
Evaluates pixel truncation, curiosity triggers, specificity (numbers/timeframes),
and penalizes redundant words repeated across both Title and Thumbnail text.
"""

import argparse
import json
import re
import sys
from typing import Any, Dict, List

HIGH_CTR_TRIGGERS = {
    "negative_stakes": ["never", "stop", "mistake", "warning", "ruined", "worst", "lie", "trap", "dead"],
    "curiosity_mystery": ["secret", "hidden", "truth", "nobody", "actually", "why", "how", "inside", "exposed"],
    "velocity_authority": ["exact", "blueprint", "tested", "hours", "days", "minutes", "step-by-step", "ultimate", "free"],
}


def estimate_pixel_width(text: str) -> int:
    # Approximate Roboto Medium 16px character pixel widths on YouTube Home Feed
    wide_chars = sum(1 for c in text if c in "MWG@%QOHD")
    narrow_chars = sum(1 for c in text if c in "ijl1|!.,':; ")
    normal_chars = len(text) - wide_chars - narrow_chars
    return int(wide_chars * 12.5 + normal_chars * 8.5 + narrow_chars * 4.2)


def score_package(title: str, thumb_text: str = "") -> Dict[str, Any]:
    title_clean = title.strip()
    thumb_clean = thumb_text.strip()
    char_len = len(title_clean)
    pixel_width = estimate_pixel_width(title_clean)

    # 1. Length & Mobile Truncation Check (Ideal: 42-58 chars, < 480px)
    length_score = 25.0
    if char_len > 62 or pixel_width > 520:
        length_score -= min(18.0, (char_len - 58) * 1.5)
    elif char_len < 24:
        length_score -= 6.0

    # 2. Specificity & Concrete Numbers / Timeframes / Brackets
    has_number = bool(re.search(r"\b\d+\b", title_clean))
    has_brackets = bool(re.search(r"[\(\[\{].*?[\)\]\}]", title_clean))
    has_dollar_or_pct = bool(re.search(r"[\$%]|\b(x|10x|100x)\b", title_clean.lower()))
    specificity_score = min(
        25.0,
        (12.0 if has_number else 0.0)
        + (7.0 if has_brackets else 0.0)
        + (8.0 if has_dollar_or_pct else 0.0)
        + 5.0,
    )

    # 3. Emotional & Curiosity Polarity
    lower_title = title_clean.lower()
    matched_categories: Dict[str, List[str]] = {}
    trigger_pts = 0.0
    for cat, words in HIGH_CTR_TRIGGERS.items():
        hits = [w for w in words if re.search(rf"\b{re.escape(w)}\b", lower_title)]
        if hits:
            matched_categories[cat] = hits
            trigger_pts += len(hits) * 9.0
    curiosity_score = min(30.0, trigger_pts + (6.0 if "?" in title_clean else 0.0))

    # 4. Title + Thumbnail Synergy (Zero Redundancy, <= 4 words on thumbnail)
    synergy_score = 20.0
    thumb_words = re.findall(r"\b\w+\b", thumb_clean.lower())
    title_words = set(re.findall(r"\b\w{4,}\b", lower_title))
    overlapping_words = [w for w in thumb_words if w in title_words]

    if not thumb_clean:
        synergy_score = 12.0  # Neutral when thumbnail text is omitted
    else:
        if len(thumb_words) > 4:
            synergy_score -= (len(thumb_words) - 4) * 4.5
        if overlapping_words:
            synergy_score -= len(overlapping_words) * 6.0
    synergy_score = max(0.0, round(synergy_score, 1))

    total_ctr_score = round(
        max(0.0, min(100.0, length_score + specificity_score + curiosity_score + synergy_score)),
        1,
    )

    recommendations: List[str] = []
    if char_len > 60:
        recommendations.append(
            f"Trim {char_len - 55} characters so the payoff word isn't cut off by '...' on mobile."
        )
    if overlapping_words:
        recommendations.append(
            f"Thumbnail text repeats title words {overlapping_words}. Make the thumbnail text create a contrasting visual question instead."
        )
    if thumb_clean and len(thumb_words) > 4:
        recommendations.append(
            f"Reduce thumbnail overlay from {len(thumb_words)} words to 2-4 words max for sub-second eye-scanning."
        )
    if curiosity_score < 12:
        recommendations.append(
            "Inject a high-polarity contrast or stakes word (e.g., 'Why...', 'Stop...', 'The Truth About...')."
        )

    return {
        "title": title_clean,
        "thumbnail_overlay": thumb_clean,
        "ctr_synergy_score": total_ctr_score,
        "metrics": {
            "character_count": char_len,
            "estimated_pixel_width": pixel_width,
            "mobile_truncation_risk": "HIGH" if char_len > 60 or pixel_width > 510 else "SAFE",
            "thumbnail_word_count": len(thumb_words),
            "redundant_overlap_words": overlapping_words,
        },
        "breakdown": {
            "feed_visibility_max25": round(length_score, 1),
            "specificity_max25": round(specificity_score, 1),
            "curiosity_polarity_max30": round(curiosity_score, 1),
            "thumbnail_synergy_max20": synergy_score,
        },
        "matched_triggers": matched_categories,
        "optimization_directives": recommendations,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Title & Thumbnail CTR Synergy Scorer")
    parser.add_argument("--title", type=str, help="Candidate video title")
    parser.add_argument("--thumb", type=str, default="", help="Thumbnail text overlay")
    parser.add_argument("--json-stdin", action="store_true", help="Read JSON from stdin")
    args = parser.parse_args()

    if args.json_stdin:
        payload = json.loads(sys.stdin.read())
        candidates = payload.get("candidates")
        if isinstance(candidates, list):
            results = [
                score_package(c.get("title", ""), c.get("thumb", "")) for c in candidates
            ]
            results.sort(key=lambda x: x["ctr_synergy_score"], reverse=True)
            print(json.dumps({"ranked_packages": results}, indent=2))
            return
        title = payload.get("title", "")
        thumb = payload.get("thumb", "")
    elif args.title:
        title = args.title
        thumb = args.thumb
    else:
        parser.print_help()
        sys.exit(1)

    print(json.dumps(score_package(title, thumb), indent=2))


if __name__ == "__main__":
    main()