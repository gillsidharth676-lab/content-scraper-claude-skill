# content-scraper · Claude Code skills

Two **Claude Code skills** that find what's actually going viral in your niche this week — and tell you what to make. Plus a third skill that writes scripts in your voice (fork & retune).

- **`content-scraper`** — scrapes Instagram Reels + YouTube Shorts (last 7 days) for AI tools / Claude Code / automation content, transcribes locally with Whisper, returns a ranked CSV.
- **`content-validator`** — re-checks the scrape: strict niche filter, hook quality scoring, bot-view detection, transcript completeness. Outputs a validation report.
- **`my-voice-writer`** — writes short-form video scripts in a specific creator's voice using a fixed `[BEAT 1] → [BEAT 2] → [BEAT 3] → [CTA]` structure. Calibrated to one user out of the box — see the fork notice inside its `SKILL.md` to retune for your own voice.
- **`hook-agent`** — writes the 1-3 second opener that `my-voice-writer` deliberately skips. Always outputs 3 hook variants `[HOOK A/B/C]` across different archetypes (number-drop, confession, meta-acknowledgment, anti-claim, list-twist, quiet declarative), one of which is in dry-Hinglish.
- **`ai-visuals-writer`** — converts a finished script + hook into a complete AI-generation shotlist (Sora 2 / Veo 3 / Runway Gen-4 / Pika / Kling), with voice-over + music guidance and budget estimate. Replaces raw recordings for B-roll while keeping UI screens as real recordings.
- **`hook-generator`** — more opinionated cousin of `hook-agent`: always 5 hooks, all Hinglish, fixed 5-pattern slate (aspirational, pain-point, exclusivity, time-or-money claim, curiosity-gap), with per-hook confidence scores 0-10 grounded in the latest scrape data.
- **`dm-responder`** — drafts personalized IG DMs for commenters who hit your "Comment X" reel. One specific reference per opener (recent post / tool / language / city), 3-message sequence, banned phrases enforced. Includes a Python helper that batch-fetches commenter profiles via Apify.

Built end-to-end with Claude Code in a single session. Costs ~$1/week in Apify credits. Local Whisper is free.

## What you get

```
~/.claude/skills/content-scraper/      ← scrape + rank
~/.claude/skills/content-validator/    ← QA the scrape
~/.claude/skills/my-voice-writer/      ← voice-locked script writer (fork & retune)
~/.claude/skills/hook-agent/           ← writes the 1-3 sec opener, 3 variants
~/.claude/skills/hook-generator/       ← 5 hooks across 5 fixed patterns, scored
~/.claude/skills/ai-visuals-writer/    ← AI-generation shotlist + VO + music + budget
~/.claude/skills/dm-responder/         ← personalized DMs for commenters (+ fetch helper)
~/.local/bin/transcribe                ← local Whisper wrapper
```

Once installed, in a new Claude Code session you can say:

> *"run content-scraper, then validate the output, then give me a script topic for today's reel"*

…and get back a ranked topic list, a hook-quality report, and a creative direction grounded in real engagement data. Then say *"voice-write that as a reel"* and `my-voice-writer` outputs a `[BEAT 1] → [CTA]` script ready to shoot.

## Quick install (macOS, Apple Silicon)

See [`setup.md`](setup.md) for the full guide. Five-minute version:

```bash
# 1. Drop the skills into Claude Code's skills dir
cp -R content-scraper content-validator my-voice-writer hook-agent hook-generator ai-visuals-writer dm-responder ~/.claude/skills/

# 2. Install Apify CLI + log in
npm install -g apify-cli
apify login   # or: export APIFY_TOKEN=apify_api_...

# 3. Install the local Whisper pipeline (yt-dlp + ffmpeg + whisper.cpp + base model)
bash setup.sh   # see setup.md if you want to do it manually
```

Then in any new Claude Code session: *"run content-scraper"*.

## One-command pipeline (`make`)

The repo ships a Makefile that chains all 7 skills end-to-end:

```bash
make help                                          # list targets
make doctor                                        # diagnose env
make reel                                          # full pre-shoot pipeline (skills 1-6)
make reel TOPIC="text-photo vs text-video memes"   # override topic
make dms HANDLES=commenters.txt                    # post-shoot DMs (skill 7)
```

`make reel` runs: **scrape → validate → cluster → hooks → script → shotlist**, and drops everything into `~/content-scraper/YYYY-MM-DD-reel-package/`. Wall time ~10 min, Apify cost ~$0.50/run.

For LLM-driven targets (`hook`, `script`, `shotlist`, `dms`) the Makefile auto-uses `claude -p` (Claude Code's headless mode) if `claude` is on PATH; otherwise it prints copy-paste instructions to run inside a Claude Code session.

## Graphical interface (`make gui`)

Prefer point-and-click? The repo ships a Streamlit app covering the whole 7-step pipeline:

```bash
python3 -m pip install --user -r gui/requirements.txt   # one-time
make gui                                                # opens http://localhost:8501
```

The GUI walks Setup → Scrape → Validate → Topics → Hooks → Script → Shotlist → DMs → Done. Every step has **Run / Regenerate / inline-Edit** controls, and a **Return to Edit** footer that jumps back to any earlier step without losing artifacts. State persists to the same `~/content-scraper/YYYY-MM-DD-reel-package/` directory the Makefile uses, so CLI and GUI are interchangeable mid-run.

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
| `hook-generator/SKILL.md` | 5-hook generator with fixed pattern slate (aspirational / pain / exclusivity / money / curiosity) + per-hook confidence scoring. All Hinglish. |
| `ai-visuals-writer/SKILL.md` | Script → AI-generation shotlist. Tool-agnostic prompts (Sora 2 / Veo 3 / Runway / Pika / Kling), voice-over guidance, music, budget. |
| `dm-responder/SKILL.md` | Personalized IG DM drafter for "Comment X" commenters. One specific reference per opener, 3-message sequence, banned-phrase enforcement. |
| `dm-responder/fetch_commenters.py` | Batch profile-fetch helper via Apify. Pulls bio, recent posts, followers, language signal, niche tags. Outputs JSON. |
| `Makefile` | One-command orchestrator. `make reel` chains skills 1–6; `make dms HANDLES=...` runs skill 7; `make gui` launches the GUI. |
| `gui/app.py` | Streamlit GUI for the full pipeline — 9 steps, Run/Edit/Regenerate per step, Return-to-Edit navigation. |
| `gui/requirements.txt` | GUI dependency (`streamlit`). |
| `bin/run-scrape.sh` | Apify IG + YT scrape orchestrator (parallel REST calls, polling, dataset fetch, process). Called by `make scrape`. |
| `bin/cluster-topics.py` | Topic clustering of latest trends.json by view performance. Called by `make cluster`. |
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
