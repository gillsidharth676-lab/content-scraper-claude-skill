---
name: content-scraper
description: Scrape the last 7 days of Instagram Reels, YouTube Shorts, and X/Twitter posts in the AI tools / Claude Code / automation niche, transcribe video with Whisper, and return a sortable table of hooks, captions, engagement metrics, and a VIRAL flag. Use when the user asks for "AI niche content scrape", "viral Claude Code posts", "competitor reel/short tracking", "trend table", "what's working in AI content this week", or similar. Targets a fixed keyword + niche-account discovery flow, not arbitrary topics — for general scraping use apify-ultimate-scraper directly.
---

# Content Scraper — AI / Claude Code / Automation Niche

Build a weekly cross-platform trend table for the AI-tools / Claude Code / automation niche. Pulls Instagram Reels, YouTube Shorts, and X/Twitter posts from the **last 7 days**, transcribes video content, and ranks by views with a VIRAL flag.

## Niche scope (hard filter)

Only return posts about: **AI tools, Claude Code, AI coding assistants, AI agents, no-code/low-code automation.** Discard everything else (lifestyle, gaming, generic tech reviews, etc.) when post-processing.

## Target keywords (search these on every run)

```
Claude Code, AI agents, N8N automation, AI coding, vibe coding,
Claude skills, OpenClaw, AI automation
```

Plus hashtag variants: `#claudecode #aiagents #n8n #aicoding #vibecoding #claudeskills #openclaw #aiautomation`

## Competitor accounts

**Auto-discover each run** — do not hardcode handles. Discovery procedure:

1. Run each keyword search (below) on each platform.
2. Tally posting accounts across the top 100 results per platform.
3. Treat the top 5 most-frequent accounts per platform as that run's "competitors" — include all their last-7-day posts in the dataset even if a specific post didn't hit the keyword filter (still apply the niche filter).
4. Print the discovered competitor list at the top of the final output so the user can pin handles later if they want.

## Prerequisites

This skill depends on **apify-ultimate-scraper** for scraping and a **local Whisper pipeline** for video transcription (Apify's Whisper actors don't work reliably on the free tier — they get blocked by IG/YT). Before starting:

- Confirm Apify CLI: `apify --version` (install with `npm install -g apify-cli` if missing)
- Confirm Apify auth: `apify info 2>/dev/null` — if it fails, run `apify login` or set `APIFY_TOKEN`
- Confirm local transcribe pipeline: `which transcribe yt-dlp ffmpeg whisper-cli` — all should resolve
  - If missing, see the **Local Whisper setup** section below
- Read `~/.agents/skills/apify-ultimate-scraper/references/gotchas.md` before the first run

All `apify` commands must include `--user-agent apify-agent-skills/apify-ultimate-scraper --json 2>/dev/null`.

**REST API fallback:** the Apify CLI's `actors start` / `runs info` commands sometimes hang. If a CLI command hasn't returned in ~30s, switch to direct REST calls:
- Start run: `POST https://api.apify.com/v2/acts/{user}~{name}/runs?token=$APIFY_TOKEN` with JSON body
- Poll status: `GET https://api.apify.com/v2/actor-runs/{runId}?token=$APIFY_TOKEN` → `.data.status`
- Fetch dataset: `GET https://api.apify.com/v2/datasets/{datasetId}/items?token=$APIFY_TOKEN&format=json`

## Local Whisper setup

If `transcribe` isn't on PATH, install once with:

```bash
# yt-dlp + ffmpeg (single-binary downloads, ~/.local/bin)
curl -fsSL -o ~/.local/bin/yt-dlp https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_macos
chmod +x ~/.local/bin/yt-dlp
# ffmpeg static binary for macOS
curl -fsSL -o /tmp/ff.zip https://evermeet.cx/ffmpeg/getrelease/zip
unzip -o /tmp/ff.zip -d ~/.local/bin/ && chmod +x ~/.local/bin/ffmpeg

# cmake (needed to build whisper.cpp)
python3 -m pip install --user cmake
ln -sf ~/Library/Python/3.9/bin/cmake ~/.local/bin/cmake

# whisper.cpp with Metal GPU
git clone --depth 1 https://github.com/ggerganov/whisper.cpp.git ~/.local/whisper.cpp
cd ~/.local/whisper.cpp && make -j$(sysctl -n hw.ncpu)
bash ./models/download-ggml-model.sh base   # 141 MB multilingual
ln -sf ~/.local/whisper.cpp/build/bin/whisper-cli ~/.local/bin/whisper-cli
```

The `transcribe` wrapper itself lives at `~/.local/bin/transcribe`. Usage:

```bash
transcribe <url> [-m base|small|medium|large-v3] [-l auto|en|ru|es|...]
```

It downloads via yt-dlp, extracts mono 16kHz WAV, runs whisper-cli, prints text on stdout. Works for any yt-dlp-supported platform (YouTube, Instagram, TikTok, X/Twitter, etc.).

## Workflow

### Step 1 — Compute the date window

`since = today - 7 days` (UTC). Apply this as a hard cutoff after fetching, since most Apify actors take a result-count limit, not a date filter.

### Step 2 — Scrape per platform

Run these three scrapes in **parallel** (separate `apify actors call` invocations). For each, fetch enough results to cover 7 days — start with `resultsLimit: 200` per keyword and expand if the oldest result is still inside the window.

#### Instagram Reels — `apify/instagram-hashtag-scraper` (not `instagram-reel-scraper`)

The reel-scraper requires usernames/profile URLs and can't do keyword discovery. Use `apify/instagram-hashtag-scraper` with `resultsType: "reels"` for hashtag-driven discovery.

Input shape:
```json
{
  "hashtags": ["claudecode", "aiagents", "n8n", "aicoding", "vibecoding", "claudeskills", "openclaw", "aiautomation"],
  "resultsType": "reels",
  "resultsLimit": 30
}
```

The hashtag scraper does **not** return transcripts. For transcripts, use the **local Whisper** wrapper on each reel's post URL (`https://www.instagram.com/p/{shortCode}/`):

```bash
transcribe "$REEL_URL" -l auto
```

Do NOT use Apify's `crawlerbros/instagram-transcript-scraper` — it returns "Could not extract video data" on free tier due to Instagram blocking Apify proxies.

#### YouTube Shorts — `streamers/youtube-scraper` (not `youtube-shorts-scraper`)

The shorts-specific scraper requires `channels[]` and isn't usable for keyword discovery. Use the main `streamers/youtube-scraper` with `searchQueries`, `maxResultsShorts: 25`, `maxResults: 0`, `maxResultStreams: 0`, `dateFilter: "week"`, `downloadSubtitles: true`, `preferAutoGeneratedSubtitles: true`, `subtitlesFormat: "plaintext"`, `sortVideosBy: "POPULAR"`. Returns view/like/comment counts plus auto-captions in `subtitles[0].plaintext` for ~85% of shorts.

For shorts that come back with `subtitles: null`, fall back to **local Whisper**: `transcribe <video-url>` (see Local Whisper setup above). Do NOT use Apify's `marielise.dev/video-transcriber-ultimate` — it gets IP-blocked by YouTube on free tier and fails with `DownloadError`.

#### X/Twitter — `apidojo/twitter-scraper-lite` ⚠️ paid-tier only

This actor returns `[{demo: true}]` placeholders on Apify FREE tier — costs ~$0.40 per call for nothing. Skip X entirely on free tier, OR upgrade to Apify Starter ($49/mo), OR try `kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest` as an alternative.

When X data IS available: for video tweets, extract the video URL and transcribe via the local `transcribe` wrapper (Twitter URLs work with yt-dlp).

Input shape (example):
```json
{
  "searchTerms": ["Claude Code", "AI agents", "N8N automation", "AI coding", "vibe coding", "Claude skills", "OpenClaw", "AI automation"],
  "maxItems": 200,
  "sort": "Latest",
  "tweetLanguage": "en"
}
```

### Step 3 — Niche filter

For every collected post, decide if it's on-niche using caption + transcript + hashtags. Keep it only if **any** of these are true:

- Mentions one of the target keywords (case-insensitive, allow plural/possessive)
- Mentions a clearly-AI tool name: Claude, ChatGPT, GPT-4/5, Cursor, Windsurf, Replit Agent, Lovable, Bolt, v0, n8n, Make.com, Zapier (when paired with "AI"), LangChain, LangGraph, MCP, Agent SDK
- Topic is unambiguously AI coding, AI agents, automation workflows, vibe coding, or AI dev tooling

Drop posts that are:
- Generic AI hype without specific tools
- Unrelated tech (web design, hardware reviews, crypto, gaming)
- Spam / clickbait without substance

### Step 4 — Compute engagement rate

```
ER = (likes + comments + shares/reposts) / max(views, follower_count, 1)
```

If view count is available (Reels, Shorts, X video views), use it. For text-only tweets, use `views` (impressions). If neither is available, use the author's follower count as the denominator and **note this in a `er_basis` column**.

### Step 5 — VIRAL flag

Tag a post `VIRAL` if **either**:
- `views >= 100_000`, OR
- `er >= 0.05` (5%)

### Step 6 — Build the output table

Sort by `views` descending. Columns:

| Column | Notes |
|---|---|
| `viral` | `VIRAL` if flagged, else empty |
| `platform` | `instagram` / `youtube` / `x` |
| `format` | `reel` / `short` / `tweet` / `video_tweet` |
| `posted_at` | ISO 8601 UTC |
| `author` | handle/channel |
| `views` | int (blank if unavailable) |
| `likes` | int |
| `comments` | int |
| `shares` | int (reposts for X) |
| `er` | float, 4 decimals |
| `er_basis` | `views` or `followers` |
| `hook` | first sentence of caption or first 80 chars (whichever is shorter) |
| `caption` | full caption |
| `transcript` | full transcript (collapsed to one line for the table; keep raw in JSON) |
| `url` | direct post URL |

### Step 7 — Save and report

- Save as `~/content-scraper/YYYY-MM-DD_ai-niche-trends.csv` AND `.json` (same data, JSON keeps full transcript text un-collapsed).
- Render the top 20 rows as a markdown table in chat.
- Above the table, print:
  - Total posts scanned vs. kept after niche filter
  - Discovered competitor list (top 5 per platform)
  - Count of VIRAL posts per platform
  - Apify run/dataset URLs for traceability

## Cost & runtime warning

Before kicking off, tell the user this is roughly:
- 3 platform searches × 8 keywords = ~24 actor runs
- Plus 1 transcript run per video Short/tweet (potentially 50–200 runs)
- Expect ~$1–$5 in Apify credits and 10–25 minutes of wall time

Ask for confirmation before running unless the user said "go" / "just run it" in the same turn.

## Gotchas

- **Reel scraper transcripts** can be empty for very recent posts (Instagram hasn't generated captions yet). Fall back to Whisper actor for those.
- **YouTube Shorts** without auto-captions and non-English audio: Whisper handles multilingual but flag the language in output.
- **X impression counts** are only visible for tweets posted in the last ~30 days and only via authenticated scrapers — `apidojo/twitter-scraper-lite` returns them.
- **Date cutoff** — many actors return results past the date window; always filter client-side after fetching.
- **Rate limits** — if any actor returns `RATE_LIMITED`, switch to `apify actors start` (non-blocking) and poll with `apify runs info`.
