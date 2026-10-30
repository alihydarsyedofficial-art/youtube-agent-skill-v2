#!/usr/bin/env python3
"""main.py - daily runner for the Tiny Wonders channel.

What one run does:
  1. Takes the oldest finished video from the upload queue (videos/queue/).
  2. Builds its metadata: from an optional sidecar JSON next to the video, or
     from the next unused sub-topic in skills/yt-script/niche_database.json.
  3. Uploads it with upload.py (OAuth refresh-token auth, channel check).
  4. Records the topic in upload_history.json (same format anti_duplicate.py
     reads) and moves the video to videos/uploaded/.

This script does NOT produce video. A finished video file must already be in
the queue folder. Optional sidecar: same name with .json, for example
    bedtime_story_01.mp4
    bedtime_story_01.json
        {"title": "...", "description": "...", "tags": ["..."],
         "topic": "Bedtime moral stories for toddlers", "thumbnail": "thumb.jpg"}

Environment variables (secrets are read by upload.py):
    NICHE_KEY         default: kids_cartoons
    UPLOAD_PRIVACY    private (default) | unlisted | public
    AI_DISCLOSURE     true (default) | false | omit
    MADE_FOR_KIDS     true | false   (default: true for kids_cartoons, else false)
    VIDEO_QUEUE_DIR   default: videos/queue
    VIDEO_DONE_DIR    default: videos/uploaded
    DRY_RUN           1 = show what would happen, upload nothing

Exit codes: 0 = uploaded or nothing to do, 1 = error that needs attention.
"""

import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from upload import (
    UploadError,
    get_service,
    parse_ai_disclosure,
    require_env,
    upload_video,
    verify_channel,
)

ROOT = Path(__file__).resolve().parent
NICHE_DB = ROOT / "skills" / "yt-script" / "niche_database.json"
HISTORY_FILE = ROOT / "upload_history.json"
QUEUE_DIR = ROOT / os.getenv("VIDEO_QUEUE_DIR", "videos/queue")
DONE_DIR = ROOT / os.getenv("VIDEO_DONE_DIR", "videos/uploaded")
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm"}

HASHTAGS = {
    "kids_cartoons": ["#KidsLearning", "#ToddlerVideos", "#BedtimeStories"],
    "personal_finance": ["#PersonalFinance", "#Budgeting", "#MoneyTips"],
    "crypto_web3": ["#Web3", "#Crypto", "#DeFi"],
    "ai_technology": ["#AI", "#Automation", "#Productivity"],
    "luxury_real_estate": ["#LuxuryHomes", "#Architecture", "#RealEstate"],
}


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        print(f"Warning: {path.name} is not valid JSON; ignoring it.")
        return default


def pick_next_video():
    if not QUEUE_DIR.is_dir():
        return None
    videos = sorted(
        (p for p in QUEUE_DIR.iterdir() if p.suffix.lower() in VIDEO_EXTS and p.is_file()),
        key=lambda p: (p.stat().st_mtime, p.name),
    )
    return videos[0] if videos else None


def next_unused_topic(niche_key: str, niche_info: dict, history: list):
    used = {h.get("topic") for h in history if h.get("niche") == niche_key}
    for topic in niche_info.get("sub_topics", []):
        if topic not in used:
            return topic
    return None


def default_metadata(topic: str, niche_key: str, niche_info: dict) -> dict:
    hashtags = HASHTAGS.get(niche_key, [])
    audience = niche_info.get("target_audience", "")
    description = (
        f"{topic}.\n\n"
        f"Made for: {audience}.\n\n"
        + " ".join(hashtags)
    ).strip()
    words = [w.strip(",.:;").lower() for w in topic.split() if len(w) > 3]
    tags = list(dict.fromkeys(words + [h.lstrip("#") for h in hashtags]))
    return {"title": topic, "description": description, "tags": tags, "topic": topic}


def record_history(entry: dict) -> None:
    history = load_json(HISTORY_FILE, [])
    history.append(entry)
    HISTORY_FILE.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")


def archive(video: Path, sidecar: Path) -> None:
    DONE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    shutil.move(str(video), str(DONE_DIR / f"{stamp}_{video.name}"))
    if sidecar.exists():
        shutil.move(str(sidecar), str(DONE_DIR / f"{stamp}_{sidecar.name}"))


def write_summary(text: str) -> None:
    path = os.getenv("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(text + "\n")


def run() -> int:
    niche_key = os.getenv("NICHE_KEY", "kids_cartoons")
    dry_run = os.getenv("DRY_RUN", "").strip().lower() in {"1", "true", "yes"}

    niches = load_json(NICHE_DB, {}).get("niches", {})
    niche_info = niches.get(niche_key)
    if not niche_info:
        print(f"ERROR: niche '{niche_key}' not found in {NICHE_DB.name}", file=sys.stderr)
        return 1

    video = pick_next_video()
    if video is None:
        print(f"No video in {QUEUE_DIR.relative_to(ROOT)}/ - nothing to upload today.")
        write_summary("No video in the queue; nothing uploaded.")
        return 0

    sidecar = video.with_suffix(".json")
    meta = load_json(sidecar, {}) if sidecar.exists() else {}

    if not meta.get("title"):
        history = load_json(HISTORY_FILE, [])
        topic = next_unused_topic(niche_key, niche_info, history)
        if topic is None:
            print(
                f"ERROR: every sub-topic for '{niche_key}' has been used and "
                f"{video.name} has no sidecar JSON with a title. Add new sub-topics to "
                "niche_database.json or supply a title in the sidecar file.",
                file=sys.stderr,
            )
            return 1
        meta = {**default_metadata(topic, niche_key, niche_info), **meta}

    made_for_kids_raw = os.getenv("MADE_FOR_KIDS", "").strip().lower()
    made_for_kids = (
        made_for_kids_raw in {"1", "true", "yes"}
        if made_for_kids_raw
        else niche_key == "kids_cartoons"
    )
    privacy = os.getenv("UPLOAD_PRIVACY", "private")
    thumb = meta.get("thumbnail")
    thumb_path = (video.parent / thumb) if thumb else None

    print(f"Video:   {video.name}")
    print(f"Title:   {meta['title']}")
    print(f"Privacy: {privacy} | Made for kids: {made_for_kids}")

    if dry_run:
        print("DRY_RUN set - nothing uploaded.")
        return 0

    try:
        youtube = get_service()
        verify_channel(youtube, require_env("YOUTUBE_CHANNEL_ID"))
        video_id = upload_video(
            youtube,
            video,
            meta["title"],
            meta.get("description", ""),
            tags=meta.get("tags", []),
            category_id=meta.get("category_id", "27"),
            privacy=privacy,
            made_for_kids=made_for_kids,
            ai_disclosure=parse_ai_disclosure(os.getenv("AI_DISCLOSURE")),
            thumbnail_path=thumb_path,
        )
    except UploadError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        write_summary(f"Upload failed: {exc}")
        return 1

    record_history(
        {
            "niche": niche_key,
            "topic": meta.get("topic", meta["title"]),
            "video_id": video_id,
            "file": video.name,
            "uploaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    )
    archive(video, sidecar)
    write_summary(f"Uploaded https://www.youtube.com/watch?v={video_id} ({privacy})")
    return 0


if __name__ == "__main__":
    sys.exit(run())
