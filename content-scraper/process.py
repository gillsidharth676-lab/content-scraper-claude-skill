#!/usr/bin/env python3
"""Post-process Apify scrape results into a unified ranked table.

Reads three JSON files (ig.json, yt.json, x.json) of dataset items, applies
date + niche filters, computes engagement rate, flags VIRAL, and writes
trends.csv + trends.json. Also prints a markdown table of the top rows.
"""
import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path.home() / "content-scraper"
SINCE = datetime.now(timezone.utc) - timedelta(days=7)

NICHE_TERMS = [
    "claude code", "claude-code", "claudecode",
    "ai agent", "ai-agent", "aiagent",
    "n8n", "n-eight-n",
    "ai coding", "vibe coding", "vibecoding",
    "claude skill", "claudeskill", "openclaw",
    "ai automation", "aiautomation",
    "cursor", "windsurf", "replit agent", "lovable", "bolt.new", "v0.dev",
    "langchain", "langgraph", "mcp", "agent sdk", "anthropic",
    "chatgpt agent", "gpt agent", "autogpt", "crewai",
    "make.com", "zapier ai", "n8n automation",
]

NON_NICHE_DROPS = [
    "gaming", "csgo", "fortnite", "crypto pump", "nft mint",
    "weight loss", "diet plan", "skincare", "makeup",
]


def is_niche(text: str) -> bool:
    t = (text or "").lower()
    if any(d in t for d in NON_NICHE_DROPS):
        # only drop if also no positive signal
        if not any(term in t for term in NICHE_TERMS):
            return False
    return any(term in t for term in NICHE_TERMS)


def first_hook(caption: str) -> str:
    if not caption:
        return ""
    line = re.split(r"[\.\!\?\n]", caption.strip(), maxsplit=1)[0]
    return line.strip()[:80]


def safe_int(v, default=0):
    try:
        return int(v) if v is not None else default
    except (TypeError, ValueError):
        return default


def parse_dt(s):
    if not s:
        return None
    try:
        if isinstance(s, (int, float)):
            return datetime.fromtimestamp(s, tz=timezone.utc)
        s = str(s).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def normalize_ig(item):
    """Instagram hashtag scraper item -> normalized row."""
    if item.get("type") not in (None, "Video", "Sidecar", "Image"):
        pass
    caption = item.get("caption") or ""
    posted = parse_dt(item.get("timestamp"))
    views = safe_int(item.get("videoViewCount") or item.get("videoPlayCount"))
    likes = safe_int(item.get("likesCount"))
    comments = safe_int(item.get("commentsCount"))
    url = item.get("url") or ""
    author = item.get("ownerUsername") or ""
    fmt = "reel" if item.get("productType") == "clips" or item.get("type") == "Video" else (item.get("type") or "post").lower()
    transcript = item.get("transcript") or ""
    return {
        "platform": "instagram",
        "format": fmt,
        "posted_at": posted.isoformat() if posted else "",
        "_posted_at_dt": posted,
        "author": author,
        "views": views,
        "likes": likes,
        "comments": comments,
        "shares": 0,
        "hook": first_hook(caption),
        "caption": caption,
        "transcript": transcript,
        "url": url,
    }


def normalize_yt(item):
    """YouTube scraper item -> normalized row."""
    caption = item.get("title") or ""
    desc = item.get("text") or ""
    posted = parse_dt(item.get("date") or item.get("uploadDate"))
    views = safe_int(item.get("viewCount"))
    likes = safe_int(item.get("likes"))
    comments = safe_int(item.get("commentsCount"))
    url = item.get("url") or ""
    author = item.get("channelName") or item.get("channelUsername") or ""
    # detect short via URL or duration
    is_short = "/shorts/" in url or (item.get("duration") and ":" in str(item.get("duration")) and int(str(item.get("duration")).split(":")[0]) == 0)
    fmt = "short" if is_short else "video"
    # transcript from subtitles ([{plaintext: '...'}] from streamers/youtube-scraper)
    subs = item.get("subtitles") or []
    transcript = ""
    if isinstance(subs, list) and subs:
        for s in subs:
            if isinstance(s, dict) and s.get("plaintext"):
                transcript = s["plaintext"]
                break
    elif isinstance(subs, str):
        transcript = subs
    combined_text = caption + " " + desc
    return {
        "platform": "youtube",
        "format": fmt,
        "posted_at": posted.isoformat() if posted else "",
        "_posted_at_dt": posted,
        "author": author,
        "views": views,
        "likes": likes,
        "comments": comments,
        "shares": 0,
        "hook": first_hook(caption),
        "caption": (caption + "\n\n" + desc).strip(),
        "transcript": transcript,
        "url": url,
    }


def normalize_x(item):
    """Twitter Lite scraper item -> normalized row."""
    text = item.get("text") or ""
    posted = parse_dt(item.get("createdAt"))
    views = safe_int(item.get("viewCount") or item.get("views"))
    likes = safe_int(item.get("likeCount"))
    comments = safe_int(item.get("replyCount"))
    shares = safe_int(item.get("retweetCount"))
    url = item.get("url") or ""
    author = (item.get("author") or {}).get("userName") or item.get("authorUsername") or ""
    has_video = bool(item.get("video")) or any("video" in (m.get("type", "") or "").lower() for m in (item.get("extendedEntities") or {}).get("media", []) if isinstance(m, dict))
    fmt = "video_tweet" if has_video else "tweet"
    return {
        "platform": "x",
        "format": fmt,
        "posted_at": posted.isoformat() if posted else "",
        "_posted_at_dt": posted,
        "author": author,
        "views": views,
        "likes": likes,
        "comments": comments,
        "shares": shares,
        "hook": first_hook(text),
        "caption": text,
        "transcript": "",  # not transcribed in this pass
        "url": url,
    }


def compute_er(row):
    engagement = row["likes"] + row["comments"] + row["shares"]
    if row["views"] > 0:
        return engagement / row["views"], "views"
    return 0.0, "no_views"


def viral_flag(row, er):
    if row["views"] >= 100_000:
        return "VIRAL"
    if er >= 0.05:
        return "VIRAL"
    return ""


def load_dataset(path):
    if not Path(path).exists():
        print(f"WARN: {path} missing", file=sys.stderr)
        return []
    with open(path) as f:
        return json.load(f)


def main():
    ig_items = load_dataset(ROOT / "ig.json")
    yt_items = load_dataset(ROOT / "yt.json")
    x_items = load_dataset(ROOT / "x.json")

    print(f"raw counts: ig={len(ig_items)} yt={len(yt_items)} x={len(x_items)}", file=sys.stderr)

    rows = []
    for it in ig_items:
        try:
            rows.append(normalize_ig(it))
        except Exception as e:
            print(f"ig parse err: {e}", file=sys.stderr)
    for it in yt_items:
        try:
            rows.append(normalize_yt(it))
        except Exception as e:
            print(f"yt parse err: {e}", file=sys.stderr)
    for it in x_items:
        try:
            rows.append(normalize_x(it))
        except Exception as e:
            print(f"x parse err: {e}", file=sys.stderr)

    # Date filter
    rows = [r for r in rows if r["_posted_at_dt"] and r["_posted_at_dt"] >= SINCE]
    print(f"after 7d filter: {len(rows)}", file=sys.stderr)

    # Niche filter
    kept = []
    dropped = 0
    for r in rows:
        text = (r["caption"] or "") + " " + (r["transcript"] or "") + " " + (r["hook"] or "")
        if is_niche(text):
            kept.append(r)
        else:
            dropped += 1
    print(f"after niche filter: kept={len(kept)} dropped={dropped}", file=sys.stderr)

    # Engagement + VIRAL
    for r in kept:
        er, basis = compute_er(r)
        r["er"] = round(er, 4)
        r["er_basis"] = basis
        r["viral"] = viral_flag(r, er)

    # Sort by views desc
    kept.sort(key=lambda r: r["views"], reverse=True)

    # Discover competitors (top 5 authors per platform by post count)
    competitors = {}
    for plat in ("instagram", "youtube", "x"):
        c = Counter(r["author"] for r in kept if r["platform"] == plat and r["author"])
        competitors[plat] = c.most_common(5)

    # VIRAL counts
    viral_counts = Counter(r["platform"] for r in kept if r["viral"])

    # Write CSV
    csv_path = ROOT / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}_ai-niche-trends.csv"
    json_path = csv_path.with_suffix(".json")
    cols = ["viral", "platform", "format", "posted_at", "author", "views", "likes",
            "comments", "shares", "er", "er_basis", "hook", "caption", "transcript", "url"]
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in kept:
            row = {k: r.get(k, "") for k in cols}
            # collapse transcript newlines for CSV readability
            row["transcript"] = (row["transcript"] or "").replace("\n", " ")[:500]
            row["caption"] = (row["caption"] or "").replace("\n", " ")[:500]
            w.writerow(row)

    with open(json_path, "w") as f:
        json.dump([{k: r.get(k, "") for k in cols} for r in kept], f, indent=2, default=str)

    # Print markdown table of top 20
    print("\n## Summary\n")
    print(f"- Total scraped: ig={len(ig_items)}, yt={len(yt_items)}, x={len(x_items)}")
    print(f"- After 7-day filter: {len(rows)}")
    print(f"- After niche filter: **{len(kept)} posts**")
    print(f"- VIRAL: {dict(viral_counts) or '(none)'}")
    print(f"- Output: `{csv_path}` and `{json_path}`")
    print("\n## Auto-discovered competitors (top 5 by post count)\n")
    for plat, items in competitors.items():
        if items:
            print(f"- **{plat}**: " + ", ".join(f"{a} ({n})" for a, n in items))
        else:
            print(f"- **{plat}**: (none)")
    print("\n## Top 20 by views\n")
    print("| # | viral | plat | fmt | author | views | er | hook | url |")
    print("|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(kept[:20], 1):
        hook = (r["hook"] or "").replace("|", "\\|").replace("\n", " ")[:60]
        url = r["url"] or ""
        print(f"| {i} | {r['viral']} | {r['platform']} | {r['format']} | {r['author']} | {r['views']:,} | {r['er']:.3f} | {hook} | {url} |")


if __name__ == "__main__":
    main()
