# Setup guide — Windows (via WSL2)

Native Windows works for the Apify scraping part but the local Whisper pipeline (`whisper.cpp` Metal acceleration, `yt-dlp` cookie integration with Chrome's Keychain-encrypted store) is much smoother in WSL2. This guide uses WSL2 Ubuntu.

## 1. Install WSL2 Ubuntu

In PowerShell as admin:

```powershell
wsl --install -d Ubuntu-22.04
```

Reboot, set up Linux username + password when prompted. From here, all commands are inside the WSL Ubuntu shell.

## 2. Install build dependencies

```bash
sudo apt update && sudo apt install -y \
  build-essential cmake git curl ffmpeg python3 python3-pip nodejs npm
```

Verify:
```bash
gcc --version && cmake --version && ffmpeg -version | head -1
```

## 3. Install Apify CLI

```bash
sudo npm install -g apify-cli
apify login --token apify_api_xxxxxxxxxxxxx
# or persist: echo 'export APIFY_TOKEN="..."' >> ~/.bashrc
```

## 4. Install yt-dlp

```bash
mkdir -p ~/.local/bin
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

curl -fsSL -o ~/.local/bin/yt-dlp \
  https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux
chmod +x ~/.local/bin/yt-dlp
```

## 5. Build whisper.cpp

```bash
git clone --depth 1 https://github.com/ggerganov/whisper.cpp.git ~/.local/whisper.cpp
cd ~/.local/whisper.cpp
make -j$(nproc)
bash ./models/download-ggml-model.sh base
ln -sf ~/.local/whisper.cpp/build/bin/whisper-cli ~/.local/bin/whisper-cli
```

Note: no Metal acceleration on WSL2. CUDA works if you have an NVIDIA GPU + the WSL CUDA toolkit:

```bash
# Optional NVIDIA acceleration
sudo apt install -y nvidia-cuda-toolkit
cd ~/.local/whisper.cpp
make clean
WHISPER_CUDA=1 make -j$(nproc)
```

## 6. Drop in transcribe wrapper

```bash
cp bin/transcribe ~/.local/bin/transcribe
chmod +x ~/.local/bin/transcribe
```

## 7. Install Claude Code skills

Claude Code on Windows respects WSL paths:

```bash
mkdir -p ~/.claude/skills
cp -R content-scraper content-validator ~/.claude/skills/
```

Run Claude Code from your WSL shell (or set its working dir to a WSL path) so the skills auto-load.

## Cookie integration in WSL

yt-dlp's `--cookies-from-browser chrome` won't reach Windows Chrome from WSL. Two options:

**Option A — export cookies once from Windows Chrome:**

1. In Windows Chrome, install the **"Get cookies.txt LOCALLY"** extension.
2. Visit instagram.com (logged in), click the extension → Export → save as `cookies.txt`.
3. Copy to WSL: `cp /mnt/c/Users/YOU/Downloads/cookies.txt ~/.config/yt-dlp-cookies.txt`
4. Edit the transcribe wrapper to use `--cookies ~/.config/yt-dlp-cookies.txt` instead of `--cookies-from-browser`.

**Option B — install Chrome inside WSL** (heavier):

```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb
google-chrome &   # log in once, cookies persist
```

Then the original `--cookies-from-browser chrome` works.

## Troubleshooting Windows-specific

| Symptom | Fix |
|---|---|
| `wsl --install` fails | enable Virtual Machine Platform + Windows Subsystem for Linux in "Turn Windows features on or off" |
| Claude Code can't find skills | run Claude Code from WSL shell, not Command Prompt |
| Whisper CPU-only slow | use `-m base` not `-m medium`; or install CUDA toolkit |
| File paths look like `/mnt/c/...` | normal — that's how WSL exposes Windows drives |
