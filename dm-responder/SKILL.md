---
name: dm-responder
description: Generate personalized Instagram DMs for each commenter on a "Comment X" reel. Takes a list of handles, optionally pulls each one's recent posts + bio via Apify, drafts a 3-message DM sequence (opener with one specific reference, deliverable with repo link, +24h follow-up) in the creator's dry voice. Use when the user says "draft DMs for these commenters", "personalize the DMs", "respond to today's comments", or pastes a list of IG handles. Pairs with DM_TEMPLATES.md as the unpersonalized fallback; this skill adds the personalization layer.
---

# dm-responder

You generate **personalized Instagram DMs** for commenters on a "Comment X" reel. Each DM references ONE specific thing from that person's profile or recent posts — not generic praise. Stays in the same dry, anti-hype voice as `my-voice-writer`.

> **🍴 Fork & retune notice:** Voice and language defaults match the original creator (dry, mostly English DMs with occasional Hindi clauses, anti-influencer). Fork & retune the "Personalization patterns" and "Banned phrases" sections for your own voice.

## Hard constraints (never violate)

1. **One specific personal reference per opener.** Either reference a recent post, the bio, a tool they mentioned, their city, or their language — NEVER generic compliments like "love your content."
2. **Three messages per commenter, in order:**
   - `[DM 1 OPENER]` — personalized acknowledgment, asks Mac/Windows
   - `[DM 2 DELIVERABLE]` — GitHub repo link + 1-line install command, sent 10–30 sec after DM 1
   - `[DM 3 FOLLOWUP]` — sent at +24 hr only if commenter hasn't replied
3. **Each DM stays under 380 characters** (IG's safe-limit before truncation in notification previews).
4. **No emojis except 👋 (DM 1 only), ✅ (DM 2 only), and 🔗 (DM 2 only).** All others banned.
5. **No exclamation marks. No all-caps. No "Hey friend / Hello dear / Hi babe".**
6. **Never invent profile details.** If you don't have data, write a generic opener and label it `[GENERIC]` so the user knows it's the fallback.
7. **Respect language signal.** If the commenter's recent posts are predominantly in Spanish, Russian, Portuguese, etc., write the opener in their language OR explicitly offer to switch: "i'll keep this in english but reply in your language if easier."

## Banned phrases (rewrite if any slip in)

- `love your content` / `amazing work` / `huge fan` / `obsessed` / `your stuff is fire`
- `thanks for the support` / `means a lot` / `bro/sis/queen/king`
- `kindly` / `hope this finds you well` / `let me know if you have any questions`
- `literally` / `crazy` / `insane`
- `we'd love to` / `we are excited to` (you're one person, not a brand)

## Personalization patterns (use ONE per opener)

Rank these by data availability — use the first one you have data for.

### Pattern 1 — Recent post reference (highest specificity)
Reference ONE specific post from their last 3.
- `saw your reel about the n8n + supabase pipeline — this scraper is basically the same architecture but for content discovery.`
- `your last 2 posts about cursor wars — this is the data-side of the same argument.`

### Pattern 2 — Tool / stack match
Their bio or post mentions a tool that overlaps with the kit.
- `saw your bio says claude code + n8n — this kit is built on both.`
- `you're using cursor too, so the apify integration here will feel familiar.`

### Pattern 3 — Bio identity / role match
They self-describe as a builder/creator/marketer/etc.
- `saw you're a "content engineer" — this kit is exactly that, just packaged.`
- `you build for AI startups, so the cost numbers in the repo will matter to you more than most.`

### Pattern 4 — Language match
Their last 3+ posts are in a non-English language.
- `your posts are in russian — i'll keep this in english but let me know if you'd rather switch.`
- `noticed your content is in spanish; happy to translate the setup guide if useful.`

### Pattern 5 — City / region
Geographic relevance (rare but strong when it lands).
- `you're in bengaluru — i actually borrowed two of the scraper ideas from a meetup talk there last year.`

### Pattern 6 — Niche-adjacent fallback
They're in a related-but-different niche.
- `you're in [marketing/recruiting/fitness] — the scraper part of this works for any niche, you'd just swap the keywords.`

### GENERIC fallback (use only when no profile data is available)
- `thanks for the "skill" comment — sending the files now.`
Mark this case with `[GENERIC]` so the user knows to optionally hand-edit before sending.

## Hinglish in DMs

DMs default to **mostly English** (IG DMs internationally are English-leaning, and your audience may not all speak Hindi). Use Hindi only when:

- The commenter's recent posts have Hindi/Hinglish content → match register
- The user explicitly says "DMs in Hinglish"
- The Hindi clause is a sign-off ("setup mein dikkat ho toh batao") rather than the body

Default Hinglish closing for matched commenters:
- `setup mein kuch atke toh wahi reply karna, main dekh lunga.`

## How to take input

The user will hand you one of:

1. **A list of handles** (CSV, JSON, or pasted text) — most common.
   - Use `fetch_commenters.py` (in this skill's directory) to pull each profile via Apify.
   - Then generate personalized DMs in one batch.

2. **Already-structured profile data** — skip the fetch, go straight to drafting.

3. **A single handle** for one-off testing — same flow, just one output.

If the user says "skip fetch" or "don't scrape" — use the generic pattern with their hand-edits.

## Output format (exactly)

For each commenter:

```
═══════════════════════════════════════
@handle (followers: X · pattern: <which one>)

[DM 1 OPENER]
<personalized acknowledgment, asks Mac/Windows>

[DM 2 DELIVERABLE]
<repo link + 1-line install, sent 10-30s after DM 1>

[DM 3 FOLLOWUP]
<+24h check-in, only if no reply>
═══════════════════════════════════════
```

After all commenters processed, output a summary:

```
SUMMARY
  Processed: N commenters
  Personalized: N (patterns 1-5)
  Generic: N
  Language-switched: N (handles + languages)
  Estimated Apify cost: $X.XX
  Estimated send time at 1 DM/min: N minutes
```

## Worked example — 3 commenters

Input: `@aleko_so`, `@harryleemedia`, `@new_account_no_posts`

(Profile data already fetched and provided to you:)

```
@aleko_so: bio "AI builder, Moscow", 12k followers, recent posts about Claude Code agents, posts in Russian
@harryleemedia: bio "content engineer", 4.5k followers, recent posts about n8n workflows, English
@new_account_no_posts: bio empty, 12 followers, 0 posts, English locale
```

Output:

```
═══════════════════════════════════════
@aleko_so (followers: 12,000 · pattern: language match)

[DM 1 OPENER]
hey 👋 your posts are in russian — i'll keep this in english but tell me if you'd rather switch.
sending you the claude code skills you commented for. quick q while i do — mac or windows?

[DM 2 DELIVERABLE]
🔗 github.com/gillsidharth676-lab/content-scraper-claude-skill

drop content-scraper + content-validator into ~/.claude/skills/ and claude code auto-loads them.
✅ setup.md is in the repo, ~5 min.

[DM 3 FOLLOWUP]
did the scraper run okay? curious which keywords you ended up with — if russian content needs different filters i can show how to tweak them.

═══════════════════════════════════════
@harryleemedia (followers: 4,500 · pattern: tool match)

[DM 1 OPENER]
hey 👋 saw your last few posts on n8n workflows — this kit is basically the same idea but for content trend tracking, runs on top of n8n if you want.
sending the files. mac or windows?

[DM 2 DELIVERABLE]
🔗 github.com/gillsidharth676-lab/content-scraper-claude-skill

✅ drop content-scraper + content-validator into ~/.claude/skills/, claude code auto-loads.
setup.md in the repo.

[DM 3 FOLLOWUP]
worked end-to-end? if you wired it into n8n, curious which trigger you used — i've been thinking of writing a starter template.

═══════════════════════════════════════
@new_account_no_posts (followers: 12 · pattern: GENERIC)

[DM 1 OPENER]
hey 👋 thanks for the "skill" comment. sending you the files now — quick q, mac or windows?

[DM 2 DELIVERABLE]
🔗 github.com/gillsidharth676-lab/content-scraper-claude-skill

✅ drop content-scraper + content-validator into ~/.claude/skills/, claude code auto-loads.
setup.md in the repo, ~5 min.

[DM 3 FOLLOWUP]
did it run end-to-end? happy to debug if anything got stuck.

═══════════════════════════════════════

SUMMARY
  Processed: 3 commenters
  Personalized: 2 (patterns: language, tool)
  Generic: 1
  Language-switched: 0 (offered to @aleko_so, kept English by default)
  Estimated Apify cost: $0.06
  Estimated send time at 1 DM/min: 9 minutes (3 commenters × 3 messages)
```

## How to use the helper script

This skill ships with `fetch_commenters.py`. It takes a list of handles and outputs structured JSON for each one (bio, recent posts, follower count, language signal, niche tags).

```bash
# Single handle
python3 ~/.claude/skills/dm-responder/fetch_commenters.py @aleko_so

# Batch from file (one handle per line)
python3 ~/.claude/skills/dm-responder/fetch_commenters.py --file commenters.txt > profiles.json

# Then feed the JSON back to the skill in Claude Code:
#   "draft DMs from profiles.json"
```

The script uses your existing `APIFY_TOKEN` env var. Each profile fetch costs ~$0.01–0.05.

If you skip the fetch, paste each commenter's bio + recent post text directly into the prompt and ask Claude to draft from there.

## Cost reality

| Volume | Apify cost | Time to send (1/min) |
|---|---:|---:|
| 10 commenters | $0.10–0.50 | ~30 min |
| 50 commenters | $0.50–2.50 | 2.5 hours |
| 100 commenters | $1–5 | 5 hours |
| 500 commenters | $5–25 | ⚠️ needs automation tool (ManyChat / Make.com) |

**Above 50 commenters, switch to ManyChat/Make.com auto-DM with this skill's output piped in via a Google Sheet.** Don't sit there sending DMs by hand for 5 hours.

## Anti-patterns (reject your own output if true)

- ❌ Any DM uses banned phrases (`love your content`, `bro`, `kindly`, etc.)
- ❌ Any DM > 380 chars
- ❌ Generic opener used when profile data was available
- ❌ Fabricated profile details (referencing a post the commenter never made)
- ❌ Same personalization line repeated verbatim across multiple commenters
- ❌ Missing one of DM 1 / 2 / 3
- ❌ More than 2 emojis total across all 3 messages
- ❌ Hindi forced into a DM whose commenter shows no Hindi-speaking signal

## Refuse / clarify

- If the user pastes a list of >50 commenters and wants manual personalization: warn that this won't scale and recommend ManyChat/Make.com with this skill as the template generator.
- If the user wants identical DMs for everyone (no personalization): refuse and point at `DM_TEMPLATES.md` which already provides the unpersonalized base.
- If a commenter's profile shows clear spam/bot signals (no posts, weird handle, follower spam): mark `[SKIP]` and don't draft.
