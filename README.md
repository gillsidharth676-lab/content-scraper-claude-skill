# content-scraper · Claude Code skills

Two **Claude Code skills** that find what's actually going viral in your niche this week — and tell you what to make. Plus a third skill that writes scripts in your voice (fork & retune).

- **`content-scraper`** — scrapes Instagram Reels + YouTube Shorts (last 7 days) for AI tools / Claude Code / automation content, transcribes locally with Whisper, returns a ranked CSV.
- **`content-validator`** — re-checks the scrape: strict niche filter, hook quality scoring, bot-view detection, transcript completeness. Outputs a validation report.
- **`my-voice-writer`** — writes short-form video scripts in a specific creator's voice using a fixed `[BEAT 1] → [BEAT 2] → [BEAT 3] → [CTA]` structure. Calibrated to one user out of the box — see the fork notice inside its `SKILL.md` to retune for your own voice.
- **`hook-agent`** — writes the 1-3 second opener that `my-voice-writer` deliberately skips. Always outputs 3 hook variants `[HOOK A/B/C]` across different archetypes (number-drop, confession, meta-acknowledgment, anti-claim, list-twist, quiet declarative), one of which is in dry-Hinglish.

Built end-to-end with Claude Code in a single session. Costs ~$1/week in Apify credits. Local Whisper is free.

## What you get

```
~/.claude/skills/content-scraper/      ← scrape + rank
~/.claude/skills/content-validator/    ← QA the scrape
~/.claude/skills/my-voice-writer/      ← voice-locked script writer (fork & retune)
~/.claude/skills/hook-agent/           ← writes the 1-3 sec opener, 3 variants
~/.local/bin/transcribe                ← local Whisper wrapper
```

Once installed, in a new Claude Code session you can say:

> *"run content-scraper, then validate the output, then give me a script topic for today's reel"*

…and get back a ranked topic list, a hook-quality report, and a creative direction grounded in real engagement data. Then say *"voice-write that as a reel"* and `my-voice-writer` outputs a `[BEAT 1] → [CTA]` script ready to shoot.

## Quick install (macOS, Apple Silicon)

See [`setup.md`](setup.md) for the full guide. Five-minute version:

```bash
# 1. Drop the skills into Claude Code's skills dir
cp -R content-scraper content-validator ~/.claude/skills/

# 2. Install Apify CLI + log in
npm install -g apify-cli
apify login   # or: export APIFY_TOKEN=apify_api_...

# 3. Install the local Whisper pipeline (yt-dlp + ffmpeg + whisper.cpp + base model)
bash setup.sh   # see setup.md if you want to do it manually
```

Then in any new Claude Code session: *"run content-scraper"*.

## Sample output

See [`examples/example-output.csv`](examples/example-output.csv) for a sanitized snapshot. Columns:

```
viral, platform, format, posted_at, author, views, likes, comments,
shares, er, er_basis, hook, caption, transcript, url
```

VIRAL flag fires on `views >= 100,000` OR `engagement_rate >= 5%`.

## Cost

| Component | Cost |
|---|---|
| Apify Instagram + YouTube scrapers | ~$0.50–$1.50 / run |
| Apify Twitter scraper | ⚠️ requires paid Apify tier ($49/mo) — repo skips X by default |
| Local Whisper (yt-dlp + whisper.cpp) | $0 (CPU/GPU local) |
| Claude Code | already paying for it |

Free Apify tier gives $5/mo in credits — enough for a few full weekly runs.

## What's in the box

| File | Purpose |
|---|---|
| `content-scraper/SKILL.md` | Skill instructions — describes the workflow Claude Code follows |
| `content-scraper/process.py` | Post-processing: filters, ER calc, VIRAL flag, ranked CSV |
| `content-validator/SKILL.md` | Validation skill instructions |
| `content-validator/validate.py` | Validation logic: strict niche, hook scores, bot detection, transcript completeness |
| `my-voice-writer/SKILL.md` | Voice-locked script writer — fixed beat structure, comment-trigger CTA, dry-Hinglish layer. **Fork & retune for your own voice.** |
| `hook-agent/SKILL.md` | 1-3 sec hook writer — 3 variants per call, archetype-tagged, mixed English/Hinglish. Pairs with `my-voice-writer`. |
| `bin/transcribe` | yt-dlp → 16kHz WAV → whisper.cpp wrapper |
| `setup.md` | Full install guide (macOS) |
| `setup-wsl.md` | Windows guide (via WSL2) |
| `DM_TEMPLATES.md` | Copy-paste DMs for the "Comment 'SKILL'" acquisition flow + Graph API payloads |
| `examples/example-output.csv` | Sanitized sample of a real weekly trend table |

## Niche

Targeted out of the box at **AI tools / Claude Code / automation**. Keyword list:

```
Claude Code, AI agents, N8N automation, AI coding, vibe coding,
Claude skills, OpenClaw, AI automation
```

To retarget to a different niche, edit the keyword list in:
- `content-scraper/SKILL.md` § "Target keywords"
- `content-scraper/process.py` → `NICHE_TERMS`
- `content-validator/validate.py` → `PRIMARY`, `SECONDARY`

## What it doesn't do

- ❌ TikTok (Apify has actors — swap in `clockworks/free-tiktok-scraper`; ~10 line change in the skill)
- ❌ Twitter/X on free tier (paid Apify tier only — `apidojo/twitter-scraper-lite` returns `{demo: true}` placeholders)
- ❌ Login-gated IG posts unless you configure yt-dlp browser cookies (see `setup.md` § Cookies)
- ❌ Sentiment analysis or LLM-based content classification — everything is heuristic/regex. Good enough for ranking, not for nuance.

## License

MIT. See [`LICENSE`](LICENSE).

## Credits

- [Apify](https://apify.com) — platform scrapers
- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) — local speech-to-text
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — universal video downloader
- Claude Code (Anthropic) — the host runtime
