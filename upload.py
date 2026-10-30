#!/usr/bin/env python3
"""upload.py - YouTube Data API v3 uploader for the Tiny Wonders channel.

Authentication uses an OAuth refresh token supplied through environment
variables (GitHub Actions secrets). Nothing secret is ever written to disk
or printed.

Required environment variables:
    YOUTUBE_CLIENT_ID
    YOUTUBE_CLIENT_SECRET
    YOUTUBE_REFRESH_TOKEN
    YOUTUBE_CHANNEL_ID      (the upload is aborted if the token belongs to a
                             different channel)

Optional environment variables:
    UPLOAD_PRIVACY    private (default) | unlisted | public
    AI_DISCLOSURE     true (default) | false | omit
                      Sets status.containsSyntheticMedia. Answer "true" if the
                      video contains realistic AI-generated or altered content.

Standalone use:
    python upload.py --file video.mp4 --title "My title" --description "..."
"""

import argparse
import json
import os
import random
import re
import sys
import time
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

TOKEN_URI = "https://oauth2.googleapis.com/token"
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]
RETRIABLE_STATUS = {500, 502, 503, 504}
MAX_RETRIES = 8
CHUNK_SIZE = 8 * 1024 * 1024  # 8 MB
VALID_PRIVACY = {"private", "unlisted", "public"}


class UploadError(RuntimeError):
    """Raised for any failure that should stop the run."""


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise UploadError(f"Missing required environment variable: {name}")
    return value


def get_credentials() -> Credentials:
    """Exchange the refresh token for a short-lived access token."""
    creds = Credentials(
        token=None,
        refresh_token=require_env("YOUTUBE_REFRESH_TOKEN"),
        token_uri=TOKEN_URI,
        client_id=require_env("YOUTUBE_CLIENT_ID"),
        client_secret=require_env("YOUTUBE_CLIENT_SECRET"),
        scopes=SCOPES,
    )
    try:
        creds.refresh(Request())
    except Exception as exc:  # noqa: BLE001 - never echo token details
        raise UploadError(
            "Could not refresh the OAuth token. Check that the refresh token is "
            "valid, the OAuth app is published to 'In production' (Testing-mode "
            f"tokens expire after ~7 days), and the client ID/secret match. ({type(exc).__name__})"
        ) from None
    return creds


def get_service():
    return build("youtube", "v3", credentials=get_credentials(), cache_discovery=False)


def verify_channel(youtube, expected_channel_id: str) -> None:
    """Abort if the authorised account is not the expected channel."""
    try:
        resp = youtube.channels().list(part="id,snippet", mine=True).execute()
    except HttpError as exc:
        raise UploadError(f"Channel lookup failed: HTTP {exc.resp.status}") from None
    channels = {item["id"]: item["snippet"]["title"] for item in resp.get("items", [])}
    if expected_channel_id not in channels:
        found = ", ".join(channels) or "none"
        raise UploadError(
            f"Authorised channel(s) [{found}] do not include {expected_channel_id}. "
            "Re-run the OAuth flow while signed in to the correct channel."
        )
    print(f"Channel verified: {channels[expected_channel_id]} ({expected_channel_id})")


def _clean(text: str) -> str:
    # YouTube rejects < and > in titles and descriptions.
    return re.sub(r"[<>]", "", text or "").strip()


def _fit_tags(tags, limit: int = 450):
    """Keep the tag list under YouTube's 500-character total limit."""
    kept, total = [], 0
    for tag in tags or []:
        tag = _clean(str(tag))
        if not tag:
            continue
        cost = len(tag) + (2 if " " in tag else 0) + 1
        if total + cost > limit:
            break
        kept.append(tag)
        total += cost
    return kept


def build_body(title, description, tags, category_id, privacy, made_for_kids, ai_disclosure):
    if privacy not in VALID_PRIVACY:
        raise UploadError(f"privacy must be one of {sorted(VALID_PRIVACY)}")
    title = _clean(title)[:100]
    if not title:
        raise UploadError("A non-empty title is required.")
    description = _clean(description)
    description = description.encode("utf-8")[:4900].decode("utf-8", "ignore")

    status = {
        "privacyStatus": privacy,
        "selfDeclaredMadeForKids": bool(made_for_kids),
        "embeddable": True,
    }
    if ai_disclosure is not None:
        status["containsSyntheticMedia"] = bool(ai_disclosure)

    return {
        "snippet": {
            "title": title,
            "description": description,
            "tags": _fit_tags(tags),
            "categoryId": str(category_id),
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en",
        },
        "status": status,
    }


def _resumable_upload(request) -> dict:
    response, retry = None, 0
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                print(f"  uploaded {int(status.progress() * 100)}%")
        except HttpError as exc:
            if exc.resp.status in RETRIABLE_STATUS and retry < MAX_RETRIES:
                retry += 1
            else:
                raise UploadError(f"Upload failed: HTTP {exc.resp.status}") from None
        except (ConnectionError, TimeoutError, OSError):
            if retry >= MAX_RETRIES:
                raise UploadError("Upload failed: repeated network errors") from None
            retry += 1
        else:
            continue
        wait = min(60, random.random() * (2 ** retry))
        print(f"  transient error, retry {retry}/{MAX_RETRIES} in {wait:.1f}s")
        time.sleep(wait)
    if "id" not in response:
        raise UploadError(f"Unexpected upload response: {json.dumps(response)[:300]}")
    return response


def upload_video(
    youtube,
    video_path,
    title,
    description,
    tags=None,
    category_id="27",  # 27 = Education, 24 = Entertainment, 1 = Film & Animation
    privacy="private",
    made_for_kids=True,
    ai_disclosure=True,
    thumbnail_path=None,
) -> str:
    video_path = Path(video_path)
    if not video_path.is_file() or video_path.stat().st_size == 0:
        raise UploadError(f"Video file missing or empty: {video_path}")

    body = build_body(title, description, tags, category_id, privacy, made_for_kids, ai_disclosure)
    media = MediaFileUpload(str(video_path), chunksize=CHUNK_SIZE, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    print(f"Uploading '{body['snippet']['title']}' as {privacy} ...")
    video_id = _resumable_upload(request)["id"]
    print(f"Upload complete: https://www.youtube.com/watch?v={video_id}")

    if thumbnail_path and Path(thumbnail_path).is_file():
        try:
            youtube.thumbnails().set(
                videoId=video_id, media_body=MediaFileUpload(str(thumbnail_path))
            ).execute()
            print("Thumbnail set.")
        except HttpError as exc:
            # Custom thumbnails need a verified channel; the video itself is already live.
            print(f"Warning: thumbnail not set (HTTP {exc.resp.status}).")
    return video_id


def parse_ai_disclosure(raw):
    raw = (raw or "true").strip().lower()
    if raw == "omit":
        return None
    return raw in {"1", "true", "yes"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload one video to YouTube.")
    parser.add_argument("--file", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--tags", default="", help="comma-separated")
    parser.add_argument("--thumbnail")
    parser.add_argument("--category", default="27")
    parser.add_argument("--privacy", default=os.getenv("UPLOAD_PRIVACY", "private"))
    parser.add_argument("--not-for-kids", action="store_true")
    args = parser.parse_args()

    try:
        youtube = get_service()
        verify_channel(youtube, require_env("YOUTUBE_CHANNEL_ID"))
        upload_video(
            youtube,
            args.file,
            args.title,
            args.description,
            tags=[t.strip() for t in args.tags.split(",") if t.strip()],
            category_id=args.category,
            privacy=args.privacy,
            made_for_kids=not args.not_for_kids,
            ai_disclosure=parse_ai_disclosure(os.getenv("AI_DISCLOSURE")),
            thumbnail_path=args.thumbnail,
        )
    except UploadError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
