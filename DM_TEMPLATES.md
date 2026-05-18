# DM templates

Copy-paste DM scripts for the "Comment 'SKILL' and I'll send the repo" flow on Instagram. Designed for a 2-message sequence (high reply rate), with a 24-hour follow-up for non-responders.

The repo URL is hard-coded as `github.com/gillsidharth676-lab/content-scraper-claude-skill` — replace it if you fork this and change the owner.

---

## Message 1 — Opener (send immediately)

```
Hey {{first_name}} 👋 just saw your "SKILL" comment — thanks!

Sending you the two Claude Code skills I built (content-scraper + content-validator) plus the setup guide. One sec, dropping the link in the next message.

Quick Q while I do — are you on Mac or Windows? Setup's slightly different. (Mac users can copy-paste in 5 min, Windows needs WSL.)
```

**Why this works:**
- Acknowledges them by name → not bot energy
- Splits delivery across 2 messages → IG algorithm rewards multi-message DM threads
- Asks a low-friction question → conversation continues → DM thread quality score rises

---

## Message 2a — Deliverables for Mac (send 10–30 sec later)

```
Here's everything 👇

🔗 github.com/gillsidharth676-lab/content-scraper-claude-skill

✅ content-scraper/SKILL.md — the main scraper
✅ content-validator/SKILL.md + validate.py — QA layer
✅ setup.md — yt-dlp + whisper.cpp install (5 min, free)
✅ examples/example-output.csv — sanitized sample of a weekly run

Clone the repo, then:
  cp -R content-scraper content-validator ~/.claude/skills/

Claude Code auto-loads them. Then say "run content-scraper" in any new session.

Stuck? Just reply here — happy to debug.
```

---

## Message 2b — Deliverables for Windows (send 10–30 sec later)

```
Here's everything 👇

🔗 github.com/gillsidharth676-lab/content-scraper-claude-skill

Windows note: you'll need WSL2 for the local Whisper part — the repo has setup-wsl.md with the exact commands. Apify scraping itself works in plain PowerShell.

✅ content-scraper/SKILL.md
✅ content-validator/SKILL.md + validate.py
✅ setup-wsl.md — Windows-specific guide
✅ examples/example-output.csv

After cloning, drop both skill folders into %USERPROFILE%\.claude\skills\ and Claude Code auto-loads them.

Stuck? Just reply.
```

---

## Message 3 — Follow-up at +24 hr (send only if no reply)

```
Hey — did you get a chance to try it? Curious what your niche is and if the keyword filter caught your competitors.

No pressure if you didn't — just want to make sure it actually worked end-to-end for you. The local Whisper part trips some people up.
```

The people who reply to this become DM thread regulars (gold for IG algo).

---

## Auto-reply variant (under 280 chars, for ManyChat / Chatfuel)

```
Hey! Here's the Claude Code skill I built 👉 github.com/gillsidharth676-lab/content-scraper-claude-skill

Drop both folders in ~/.claude/skills/ and Claude Code auto-loads them. Setup guide inside the repo. Hit reply if you get stuck 🛠️
```

---

## Edge-case responses

| If they say... | Reply with... |
|---|---|
| *"is this free?"* | Yep — the skills are open source. You'll pay ~$1–5 in Apify credits/week for the scraping part. Local Whisper is free. |
| *"i don't code"* | No coding needed — Claude Code does the work, you just install the skill files (drag & drop) and ask it to run. 5 min setup. |
| *"can it do TikTok?"* | Not yet — Apify has TikTok actors though, so swapping one in is a 10-line edit. Want me to send the modified version? |
| *non-English comment* | Reply in their language. The two big segments this week are Russian and Spanish — high signal those audiences engage. Use translate. |
| *"already have this"* | Oh nice! What's your stack — Apify too, or different? Always trading notes 🤝 |

---

## Raw Instagram Graph API payloads

If you're wiring this through Make.com or a custom backend instead of ManyChat, here are the request bodies for the IG Send Message endpoint.

### Endpoint

```
POST https://graph.instagram.com/v21.0/me/messages?access_token={{IG_ACCESS_TOKEN}}
Content-Type: application/json
```

### Opener with quick-reply buttons

```json
{
  "recipient": { "id": "{{IG_USER_ID}}" },
  "message": {
    "text": "Hey 👋 just saw your \"SKILL\" comment — thanks!\n\nSending you the two Claude Code skills I built. One sec.\n\nQuick Q while I do — Mac or Windows?",
    "quick_replies": [
      { "content_type": "text", "title": "🍎 Mac",     "payload": "OS_MAC" },
      { "content_type": "text", "title": "🪟 Windows", "payload": "OS_WINDOWS" },
      { "content_type": "text", "title": "🐧 Linux",   "payload": "OS_LINUX" }
    ]
  }
}
```

### Deliverables (Mac branch)

```json
{
  "recipient": { "id": "{{IG_USER_ID}}" },
  "message": {
    "text": "Here's everything 👇\n\n🔗 github.com/gillsidharth676-lab/content-scraper-claude-skill\n\n✅ content-scraper/SKILL.md\n✅ content-validator/SKILL.md + validate.py\n✅ setup.md\n✅ examples/example-output.csv\n\nClone the repo, then:\n  cp -R content-scraper content-validator ~/.claude/skills/\n\nClaude Code auto-loads them. Then say \"run content-scraper\".\n\nStuck? Just reply here."
  }
}
```

### Follow-up (sent at +24h via scheduler)

```json
{
  "recipient": { "id": "{{IG_USER_ID}}" },
  "message": {
    "text": "Hey — did you get a chance to try it? Curious what your niche is.\n\nNo pressure if you didn't — just want to make sure it worked end-to-end. The Whisper part trips some people up."
  }
}
```

---

## Reel caption (for the launch reel itself)

```
🔺Comment "SKILL" and I'll DM you the Claude Code skills I built🔻

I got tired of studying viral content that was actually 2 months old.

So I built two Claude Code skills:

1️⃣ content-scraper — pulls IG Reels + YouTube Shorts from the last 7 days, transcribes them locally with Whisper (free), scores engagement, flags VIRAL posts.

2️⃣ content-validator — checks for bot views, scores hook quality, clusters by topic, tells me which angles are actually working *this week* in the AI/Claude Code/automation niche.

This week's verdict: "Comment-for-DM" content beat every other format by 3x. So here I am, doing the thing.

Comment "SKILL" and I'll DM you:
✅ Both skill files (SKILL.md + Python helpers)
✅ The setup guide (yt-dlp + whisper.cpp + Apify)
✅ My actual top-20 ranked list from this week

🔗 Repo: github.com/gillsidharth676-lab/content-scraper-claude-skill

Built entirely with Claude Code. Cost me about $1 in API credits.

🔺

#claudecode #aiagents #aiautomation #vibecoding #claudeskills #n8n #anthropic #aitools #buildinpublic #automation
```

---

## Production checklist before posting the reel

- [ ] GitHub repo is public and the URL above resolves
- [ ] At least one screenshot or demo in the repo README
- [ ] Saved Reply in IG → Settings → Tools → "SKILL" trigger, so manual replies are 1-tap
- [ ] Manychat (or equivalent) wired up if expecting >50 comments
- [ ] Token hygiene: revoke leaked tokens from chat transcripts, set Apify + GitHub PAT rotation reminders
