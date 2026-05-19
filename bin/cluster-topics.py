#!/usr/bin/env python3
"""Cluster the latest scraped trends file by topic and rank by total views.

Reads the newest ~/content-scraper/*_ai-niche-trends.json. Outputs a
markdown table. Used by the Makefile as the topic-picker handoff to
hook-generator + my-voice-writer.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path.home() / "content-scraper"

TOPICS = [
    ("Claude Code skills/plugins",
     r"\b(claude\s*skill|claude\s*plugin|claude\s*code\s+(skill|plugin|extension)|mcp\s+server|openclaw)\b"),
    ("AI agent income / monetization",
     r"\b(\$[\d,]+|make\s+money|side\s*hustle|sell(ing)?\s+ai|earn(ed)?|revenue|client[s]?)\b"),
    ("Boris Cherny / Anthropic insider",
     r"\b(boris|cherny|anthropic|claude\s+team)\b"),
    ("Comment-for-DM lead magnet",
     r"\b(comment\s+[\"“‘]?\w+|comenta\s+|coment\s+|留言|пиши|напиши|dm\s+me)"),
    ("N8N workflow automation",
     r"\b(n8n|workflow|automation\s+pipeline|nodes|integrate|webhook)\b"),
    ("Vibe coding / build-in-public",
     r"\b(vibe\s*coding|build.*in.*public|let'?s\s+build|build.*with.*me)\b"),
    ("Prompting frameworks/tips",
     r"\b(prompt\w*|framework|10x|top\s+\d+\s+(tips|tricks)|hack\b)\b"),
    ("Multi-agent / parallel agents",
     r"\b(50\s+agents|multi.?agent|parallel|swarm|fleet)\b"),
    ("Claude vs ChatGPT / Google",
     r"\b(claude\s+vs|chatgpt|gemini|google\s+ai|grok)\b"),
]


def topic_of(post: dict) -> str:
    text = " ".join([
        post.get("hook", "") or "",
        post.get("caption", "") or "",
        post.get("transcript", "") or "",
    ]).lower()
    for label, pat in TOPICS:
        if re.search(pat, text, re.IGNORECASE):
            return label
    return "Other AI/automation"


def main() -> None:
    files = sorted(ROOT.glob("*_ai-niche-trends.json"),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        print(f"error: no *_ai-niche-trends.json in {ROOT}", file=sys.stderr)
        sys.exit(1)

    latest = files[0]
    trends = json.load(open(latest))

    clusters = defaultdict(lambda: {"posts": [], "total_views": 0, "viral": 0})
    for r in trends:
        t = topic_of(r)
        clusters[t]["posts"].append(r)
        clusters[t]["total_views"] += r.get("views", 0)
        if r.get("viral"):
            clusters[t]["viral"] += 1

    ranked = sorted(clusters.items(), key=lambda kv: kv[1]["total_views"], reverse=True)

    print(f"# Topic clusters — {latest.name}\n")
    print(f"Total posts: **{len(trends)}**\n")
    print("| # | Topic | Posts | VIRAL | Total views | Top reel |")
    print("|---|---|---:|---:|---:|---|")

    for i, (label, c) in enumerate(ranked, 1):
        top = max(c["posts"], key=lambda p: p.get("views", 0)) if c["posts"] else {}
        hook = (top.get("hook", "") or "")[:50].replace("|", "\\|")
        author = top.get("author", "")
        views = top.get("views", 0)
        print(f"| {i} | {label} | {len(c['posts'])} | {c['viral']} | {c['total_views']:,} | {author} ({views:,}) — {hook} |")

    # Print the top topic as a single line at the end — easy for Makefile to grab
    if ranked:
        top_label = ranked[0][0]
        print(f"\n_Top topic: **{top_label}**_")


if __name__ == "__main__":
    main()
