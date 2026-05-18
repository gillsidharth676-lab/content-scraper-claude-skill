# Setup guide — macOS (Apple Silicon)

Total time: ~10 min. Total cost: $0 for the local parts; $0–$5 for Apify free tier.

## 1. Drop the skills into Claude Code

```bash
git clone https://github.com/YOUR_HANDLE/content-scraper-claude-skill.git
cd content-scraper-claude-skill
mkdir -p ~/.claude/skills
cp -R content-scraper content-validator ~/.claude/skills/
```

Verify:

```bash
ls ~/.claude/skills/
# should list: content-scraper  content-validator  ...
```

## 2. Install Node + Apify CLI

If you don't have Node:

```bash
# Apple Silicon — download official binary, no Homebrew needed
curl -fsSL -o /tmp/node.tar.xz https://nodejs.org/dist/v24.15.0/node-v24.15.0-darwin-arm64.tar.xz
mkdir -p ~/.local
tar -xJf /tmp/node.tar.xz -C ~/.local
mv ~/.local/node-v24.15.0-darwin-arm64 ~/.local/node
echo 'export PATH="$HOME/.local/node/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

Then:

```bash
npm install -g apify-cli
apify --version   # should show 1.5+
```

## 3. Get an Apify token and log in

1. Sign up at https://console.apify.com/sign-up (free tier: $5/mo credits)
2. Generate a token at https://console.apify.com/settings/integrations
3. Log in:

```bash
apify login --token apify_api_xxxxxxxxxxxxx

# Or persist as env var:
echo 'export APIFY_TOKEN="apify_api_xxxxxxxxxxxxx"' >> ~/.zshrc
source ~/.zshrc
```

## 4. Install local Whisper pipeline

The skill uses **local Whisper** for video transcription — free, runs on your Mac, no Apify charges. You need:
- `yt-dlp` (video downloader)
- `ffmpeg` (audio extractor)
- `whisper.cpp` (transcription, Metal-accelerated on Apple Silicon)

```bash
mkdir -p ~/.local/bin
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc

# yt-dlp (single-binary)
curl -fsSL -o ~/.local/bin/yt-dlp \
  https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_macos
chmod +x ~/.local/bin/yt-dlp

# ffmpeg (static binary for macOS)
curl -fsSL -o /tmp/ff.zip https://evermeet.cx/ffmpeg/getrelease/zip
unzip -o /tmp/ff.zip -d ~/.local/bin/
chmod +x ~/.local/bin/ffmpeg

# cmake (needed to build whisper.cpp — installed via pip to avoid Homebrew)
python3 -m pip install --user cmake
ln -sf ~/Library/Python/3.9/bin/cmake ~/.local/bin/cmake

# whisper.cpp with Metal GPU
git clone --depth 1 https://github.com/ggerganov/whisper.cpp.git ~/.local/whisper.cpp
cd ~/.local/whisper.cpp
make -j$(sysctl -n hw.ncpu)
bash ./models/download-ggml-model.sh base   # 141 MB multilingual
ln -sf ~/.local/whisper.cpp/build/bin/whisper-cli ~/.local/bin/whisper-cli
```

Drop in the wrapper script:

```bash
cp bin/transcribe ~/.local/bin/transcribe
chmod +x ~/.local/bin/transcribe
```

Verify:

```bash
which yt-dlp ffmpeg whisper-cli transcribe
transcribe "https://www.youtube.com/shorts/Grc8n0suMGU"   # should print a transcript
```

## 5. Use the skill

In any new Claude Code session, say:

> *"run content-scraper"*

…or be specific:

> *"run content-scraper for the last 7 days, then validate it and recommend a script topic for today's reel"*

The skills auto-load from `~/.claude/skills/`.

## Optional: yt-dlp browser cookies (for logged-in IG posts)

Some Instagram reels are visible only to logged-in viewers. To transcribe those, configure yt-dlp to use your Chrome session cookies:

1. Make sure you're logged into Instagram in Chrome.
2. Run a one-time transcribe to trigger the macOS Keychain prompt for "Chrome Safe Storage" — click **"Always Allow"**.
3. From then on, `transcribe` auto-passes Chrome cookies for any `instagram.com` URL.

Test:

```bash
transcribe "https://www.instagram.com/p/SOMECODE/"
```

If it still fails with "Instagram sent an empty media response", check:
```bash
python3 -c "
import sqlite3
db = '/Users/$USER/Library/Application Support/Google/Chrome/Default/Cookies'
rows = sqlite3.connect(f'file:{db}?mode=ro', uri=True).execute(
    \"SELECT name FROM cookies WHERE host_key LIKE '%instagram%'\"
).fetchall()
print('sessionid present:', any(r[0]=='sessionid' for r in rows))
"
```

If `sessionid` is missing, log in to Instagram fresh in Chrome.

## Optional: bigger Whisper model

The `base` model (141 MB) is fast but rough. For better accuracy:

```bash
cd ~/.local/whisper.cpp
bash ./models/download-ggml-model.sh small        # 466 MB
# or
bash ./models/download-ggml-model.sh medium       # 1.4 GB
```

Then call with `-m small` or `-m medium`:

```bash
transcribe "<url>" -m small
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `apify login` hangs in browser | use `apify login --token YOUR_TOKEN` instead |
| `apify actors call` hangs >30s | switch to REST API; see `content-scraper/SKILL.md` § REST API fallback |
| `cmake: command not found` during whisper.cpp build | `python3 -m pip install --user cmake` then re-symlink |
| Whisper output is empty / just `[Music]` | try `-m small` (catches faint speech better) |
| All Apify Twitter results say `{demo: true}` | free Apify tier doesn't include X; skip or upgrade |
| IG hashtag scraper returns "Could not extract" | rare; rerun, or switch to `apify/instagram-search-scraper` |
