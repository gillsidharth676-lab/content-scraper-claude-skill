---
name: content-validator
description: Validate the latest content-scraper output (YYYY-MM-DD_ai-niche-trends.json in ~/content-scraper/) along four dimensions — niche relevance, hook quality, engagement-rate sanity, and transcript completeness — and produce a report flagging false positives, weak hooks, suspicious bot signals, and missing transcripts. Use when the user says "validate this scrape", "check the content-scraper output", "are these posts actually relevant", "any bot/fake engagement", or asks for quality control on a trend table. Run AFTER content-scraper produces output.
---

# Content Validator — Quality Control for content-scraper

Audit the most recent content-scraper output and emit a structured report. Does NOT re-scrape; only re-analyzes what's on disk plus optionally re-runs local Whisper on rows with missing transcripts.

## Input

Latest file in `~/content-scraper/*_ai-niche-trends.json`. If multiple exist, use the newest by mtime.

## Four validation checks

### 1. Niche relevance

The scraper's filter is permissive (any niche keyword OR mention of an AI tool). Re-check each kept post with **stricter rules**:

A post passes strict niche only if **at least one** of:
- Mentions a primary keyword explicitly: `Claude Code`, `AI agent(s)`, `n8n`, `vibe coding`, `Claude skill(s)`, `OpenClaw`
- Mentions ≥2 secondary AI-tool names (Cursor, Windsurf, MCP, LangGraph, Replit Agent, Lovable, etc.)
- Has both an AI tool name AND a workflow-automation verb ("automate", "workflow", "agent that", "build a bot")

Flag everything else as `false_positive`. Common false positives in the AI niche:
- Generic ChatGPT screenshots / hype reels
- AI image-gen content (midjourney, dalle) miscategorized
- "AI made $X for me" with no actual tool detail
- Russian/foreign content where translation misfired the filter

### 2. Hook quality

Score the `hook` field 0–5 on these heuristics:
- +1 if it contains a number, $ amount, or specific tool name
- +1 if it's a question or makes a claim ("Just Solved", "Nobody Uses", "Will CHANGE")
- +1 if it has an explicit CTA in the first line ("Comment X", "Save this", "Try")
- +1 if length is 25-75 chars (sweet spot for IG/Shorts)
- +1 if it uses an emotional/curiosity trigger (RIP, $400K, "secret", "actually", surprise)

Surface:
- Top 10 hooks (score ≥4)
- Bottom 10 hooks (score ≤1) — patterns to avoid

### 3. Engagement-rate sanity

Flag suspicious posts:
- `views > 50_000` AND `likes < 10` → `suspicious_bot_views`
- `views > 100_000` AND `(likes + comments) / views < 0.001` → `extreme_engagement_suppression`
- `viral` flag set but `er_basis != "views"` → `viral_no_view_data` (viral flag was based on follower count, less reliable)
- `er > 0.3` with `views < 5_000` → `low_volume_high_er` (small-sample artifact)

Downgrade any flagged post's VIRAL status unless the user opts to keep it.

### 4. Transcript completeness

For every VIRAL row, check the `transcript` field:
- Empty string → `missing`
- Only `[Music]`, `[Applause]`, or similar bracket markers → `non_speech`
- < 20 characters → `too_short`

If the user has the local `transcribe` wrapper (`~/.local/bin/transcribe`), offer to fill the gaps via:

```bash
transcribe "$POST_URL" -l auto
```

For YouTube auto-translated music-only output, retry with `-m small` (better model often catches faint speech).

## Workflow

1. Locate latest trends file (`ls -t ~/content-scraper/*_ai-niche-trends.json | head -1`).
2. Load and run all four checks via the bundled `validate.py` (in this skill's directory).
3. Print a markdown report with sections per check.
4. Save full validation results to `~/content-scraper/YYYY-MM-DD_validation.json`.
5. After showing findings, **ask** before running expensive operations (filling Whisper transcripts).

## Output format

Markdown report with these sections:

```
## Validation summary
- Total posts: N
- False positives: N (M%)
- Weak hooks: N
- Suspicious engagement: N
- Missing transcripts (VIRAL only): N

## False positives
| # | platform | author | hook | reason |
...

## Top hooks (score ≥4)
| hook | score | views | platform |
...

## Suspicious engagement
| platform | author | views | likes | flag |
...

## Missing transcripts
| platform | url | status |
...
```

End with concrete actions:
- "Run `python ~/.claude/skills/content-validator/validate.py --fill-transcripts` to fill the N gaps via local Whisper (est. M minutes)"
- "X posts were re-flagged as non-viral due to suspicious engagement"
