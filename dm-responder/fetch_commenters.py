#!/usr/bin/env python3
"""Fetch IG profile data for a list of commenter handles via Apify.

Outputs JSON suitable to feed back into the dm-responder skill so it can
draft personalized DMs without hallucinating profile details.

Usage:
    # Single handle (prints JSON to stdout)
    python3 fetch_commenters.py @aleko_so

    # Batch from file (one handle per line, with or without @)
    python3 fetch_commenters.py --file commenters.txt > profiles.json

    # With cost estimate first (no fetch)
    python3 fetch_commenters.py --file commenters.txt --dry-run

Requires APIFY_TOKEN in env. Uses apify/instagram-profile-scraper actor.
Cost: ~$0.01-0.05 per profile fetched. Skipped/private profiles cost $0.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter

ACTOR_ID = "apify~instagram-profile-scraper"
API_BASE = "https://api.apify.com/v2"


def get_token() -> str:
    t = os.environ.get("APIFY_TOKEN")
    if not t:
        sys.exit("error: APIFY_TOKEN not set. export APIFY_TOKEN=apify_api_...")
    return t


def normalize_handle(h: str) -> str:
    h = h.strip()
    if h.startswith("@"):
        h = h[1:]
    if "instagram.com/" in h:
        h = h.split("instagram.com/", 1)[1].rstrip("/").split("?")[0]
    return h


def detect_language(text: str) -> str:
    """Rough language detection based on script + common stopwords. Good enough for routing."""
    if not text:
        return "unknown"
    # Devanagari (Hindi)
    if re.search(r"[ऀ-ॿ]", text):
        return "hi"
    # Cyrillic (Russian)
    if re.search(r"[Ѐ-ӿ]", text):
        return "ru"
    # Chinese / Japanese / Korean
    if re.search(r"[一-鿿぀-ゟ゠-ヿ가-힯]", text):
        return "cjk"
    # Arabic
    if re.search(r"[؀-ۿ]", text):
        return "ar"
    # Romanized Hindi heuristic
    hindi_words = ["hai", "kya", "main", "aap", "tumhe", "yaar", "nahi", "matlab", "bhai", "karo", "dekho"]
    text_lower = text.lower()
    if sum(1 for w in hindi_words if f" {w} " in f" {text_lower} ") >= 2:
        return "hi-en"
    # Spanish heuristic
    spanish_words = ["el", "la", "los", "que", "para", "con", "esto", "como", "más", "está"]
    if sum(1 for w in spanish_words if f" {w} " in f" {text_lower} ") >= 3:
        return "es"
    # Portuguese heuristic
    portuguese_words = ["você", "para", "com", "uma", "este", "como", "mais", "está"]
    if sum(1 for w in portuguese_words if f" {w} " in f" {text_lower} ") >= 3:
        return "pt"
    return "en"


def extract_niche_tags(text: str) -> list:
    """Pull out tool/niche signals from bio + captions for the dm-responder."""
    tags = []
    signals = {
        "claude_code": r"\bclaude\s*code\b",
        "n8n": r"\bn8n\b",
        "cursor": r"\bcursor\b",
        "windsurf": r"\bwindsurf\b",
        "mcp": r"\bmcp\b",
        "ai_agents": r"\bai\s*agents?\b",
        "automation": r"\bautomation\b",
        "apify": r"\bapify\b",
        "vibe_coding": r"\bvibe\s*coding\b",
        "content_creator": r"\bcontent\s*(creator|engineer)\b",
        "indie_hacker": r"\bindie\s*(hacker|maker)\b",
        "founder": r"\bfounder\b|\bbuilding\b",
        "marketer": r"\bmarketer\b|\bmarketing\b",
    }
    for tag, pattern in signals.items():
        if re.search(pattern, text, re.IGNORECASE):
            tags.append(tag)
    return tags


def fetch_profile(handle: str, token: str) -> dict:
    """Run apify/instagram-profile-scraper for one handle and return structured data."""
    input_payload = {"usernames": [handle], "resultsLimit": 3}
    url = f"{API_BASE}/acts/{ACTOR_ID}/run-sync-get-dataset-items?token={token}"
    req = urllib.request.Request(
        url,
        data=json.dumps(input_payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            items = json.loads(resp.read().decode())
    except Exception as e:
        return {"handle": handle, "error": f"fetch_failed: {e}"}

    if not items:
        return {"handle": handle, "error": "no_results"}

    p = items[0]
    bio = p.get("biography") or ""
    recent_posts = p.get("latestPosts", []) or p.get("posts", []) or []

    # Pull last 3 captions for niche + language detection
    captions = [post.get("caption", "") for post in recent_posts[:3] if isinstance(post, dict)]
    combined_text = bio + " " + " ".join(captions)

    return {
        "handle": handle,
        "url": p.get("url") or f"https://instagram.com/{handle}",
        "full_name": p.get("fullName") or "",
        "bio": bio,
        "followers": p.get("followersCount") or 0,
        "following": p.get("followsCount") or 0,
        "posts_count": p.get("postsCount") or 0,
        "is_private": p.get("private", False),
        "is_verified": p.get("verified", False),
        "language": detect_language(combined_text),
        "niche_tags": extract_niche_tags(combined_text),
        "recent_captions": captions,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("handle", nargs="?", help="Single @handle to fetch")
    ap.add_argument("--file", help="File with one handle per line")
    ap.add_argument("--dry-run", action="store_true", help="Estimate cost, don't fetch")
    ap.add_argument("--rate-limit", type=float, default=0.5, help="Seconds between fetches")
    args = ap.parse_args()

    # Collect handles
    handles = []
    if args.handle:
        handles.append(normalize_handle(args.handle))
    if args.file:
        with open(args.file) as f:
            handles.extend(normalize_handle(line) for line in f if line.strip())
    if not handles:
        ap.error("provide a handle or --file")

    # Dedupe
    seen = set()
    handles = [h for h in handles if not (h in seen or seen.add(h))]

    if args.dry_run:
        est_low = len(handles) * 0.01
        est_high = len(handles) * 0.05
        print(f"would fetch {len(handles)} profiles", file=sys.stderr)
        print(f"estimated cost: ${est_low:.2f} - ${est_high:.2f}", file=sys.stderr)
        print(json.dumps(handles, indent=2))
        return

    token = get_token()
    profiles = []
    for i, h in enumerate(handles, 1):
        print(f"[{i}/{len(handles)}] fetching {h}...", file=sys.stderr)
        p = fetch_profile(h, token)
        profiles.append(p)
        if "error" in p:
            print(f"  error: {p['error']}", file=sys.stderr)
        else:
            print(f"  ok · {p['followers']} followers · lang={p['language']} · tags={p['niche_tags']}", file=sys.stderr)
        if i < len(handles):
            time.sleep(args.rate_limit)

    # Summary to stderr
    success = sum(1 for p in profiles if "error" not in p)
    lang_dist = Counter(p.get("language", "unknown") for p in profiles if "error" not in p)
    print(f"\ndone · {success}/{len(profiles)} fetched · languages: {dict(lang_dist)}", file=sys.stderr)

    # Profiles to stdout (JSON, ready to feed back to Claude)
    json.dump(profiles, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()
