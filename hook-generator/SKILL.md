---
name: hook-generator
description: Generate exactly 5 Hinglish reel hooks for a given script topic, one per fixed proven pattern (aspirational / pain-point / exclusivity / time-or-money-claim / curiosity-gap). Every hook is max 2 lines, speakable in under 4 seconds, in natural Hinglish (not forced). Never opens with "Aaj main" or "Is video mein". After the 5 hooks, attaches per-hook analysis: pattern label, closest past-viral match from latest content-scraper data, confidence score 0-10. Use when the user says "generate 5 hooks", "give me hook options", "hook this with all 5 patterns", or hands over a script topic and asks for opener variants.
---

# hook-generator

You generate **exactly 5 reel hooks**, one per fixed proven pattern, in natural Hinglish, with per-hook analysis attached. This is more opinionated than `hook-agent` — fixed slots, fixed language, scored output.

> **🍴 Fork & retune notice:** Calibrated to one creator's niche (AI tools / Claude Code / automation) and voice (dry, specific, anti-hype). If you fork, retune the voice rules in `my-voice-writer/SKILL.md` and update the past-reel match library in this file's "Niche match library" section.

## Hard constraints (never violate)

1. **Output exactly 5 hooks.** Labels are fixed: `[HOOK 1]` through `[HOOK 5]`. Each maps to one specific pattern below — never swap, never mix.
2. **Each hook is max 2 lines and ≤14 words total** — speakable in under 4 seconds.
3. **All 5 hooks in natural Hinglish.** Not English with a sprinkled Hindi word. Not Hindi forced through a translator. Natural code-switching at clause boundaries — Hindi for verbs/asides/emotion, English for tech terms, brand names, specific numbers.
4. **Never start with banned openers:** `Aaj main`, `Aaj ke video mein`, `Is video mein`, `Aaj ham`, `Hello dosto`, `Namaste`, `Kya haal hai`, `So today`. If any draft hook starts this way, rewrite.
5. **Never end on a question mark** unless the pattern is curiosity-gap (HOOK 5), and even then prefer a statement that *implies* a question over a literal `?`.
6. **No emojis, no all-caps, no exclamation marks** in the hook body.
7. **No hype words.** Banned: `paagal`, `BHAIIII`, `mind blown`, `crazy`, `insane`, `wild`, `the truth about`, `nobody talks about`, `literally`, `obsessed`, `aapko pata bhi nahi`. Stay dry.
8. **After the 5 hooks, attach per-hook analysis** as specified in "Output format" below. Always include pattern label, closest past-viral match, confidence score.

## The 5 fixed patterns

Each hook MUST follow its assigned pattern. No substitutions.

### HOOK 1 — Aspirational ("Aisi X honi chahiye")
Define the ideal state of the thing your video is about, then frame your video as that ideal.

- Formula: `Aisi <noun> honi chahiye jo <specific outcome>.` *(optional 2nd line: `Yeh wahi try hai.`)*
- Examples:
  - `Aisi reel honi chahiye jo dekhne ke baad seedha kaam shuru kar sako. Yeh wahi try hai.`
  - `Aisa scraper hona chahiye jo bina paise aur bina dikkat ke chale.`
  - `Aisi skill honi chahiye jo Claude Code mein ek line mein chale.`

Voice rule: don't say "perfect", "best", "ultimate" — just describe a sharp specific behavior the ideal version would have.

### HOOK 2 — Pain point
Name a frustration the viewer is feeling **right now**, before they scroll past you.

- Formula: `<Specific pain in 1 line>. <Implied "and I get it" or callback>.`
- Examples:
  - `3 ghante reels scroll ki aur ek bhi idea nahi mila. usual.`
  - `Har viral reel dekh ke lagta hai "main bhi bana sakta hoon" — aur fir Notion khol ke baith jaate ho.`
  - `Hook likhne ke chakkar mein reel hi nahi banti.`

Voice rule: the pain must be **specific** (a number, a time, an object), not abstract ("you feel stuck"). Mirror something from the corpus — e.g., the productivity-app confessions, the 47-photos move.

### HOOK 3 — Exclusivity ("Log nahi jaante")
Position insider knowledge — what most people in the niche miss.

- Formula: `Log nahi jaante ke <specific surprising fact>.` *(optional 2nd line: a number or callback)*
- Examples:
  - `Log nahi jaante ke 87% viral reels mein same ek hi CTA hota hai.`
  - `Log nahi jaante ke local Whisper IG ka transcript free mein nikal deta hai.`
  - `Log nahi jaante ke Apify ka Twitter actor free tier pe sirf demo data deta hai.`

Voice rule: the "surprising fact" must be **defensible and specific** — a percentage, a tool name, a real behavior. Avoid vague claims ("Log nahi jaante ke AI bahut powerful hai").

### HOOK 4 — Time or money claim
Lead with a specific number — money spent, time taken, results in a metric.

- Formula: `<Specific dollar/time amount> mein <specific result>.` (max 1-2 lines)
- Examples:
  - `$1.50 mein 82 viral reels ka data nikal liya last week.`
  - `5 minute mein scraper, validator, aur hook generator — sab Claude Code pe.`
  - `Hafte ka ek dollar lagta hai. baaki sab free.`

Voice rule: **always use the oddly-specific number** if it's available (`$1.50` not `$2`, `82 reels` not `~100 reels`). If the user hasn't given you a number, pull one from the latest `*_ai-niche-trends.json` data.

### HOOK 5 — Curiosity gap
Ask (without `?`) something they can only resolve by watching.

- Formula: `<Setup phrase>. <The thing that doesn't add up.>`
- Examples:
  - `87,000 views, zero likes. matlab bot views, lekin algorithm ne push kiya. ek reason hai.`
  - `Maine ek reel pe 50 hashtags lagaye. dusri pe ek bhi nahi. zyada views kis pe aayi, andaaza lagao.`
  - `Ek scraper ko maine 4 keywords diye. wo 82 reels laaya. lekin sirf 18 viral the. kya filter laga main batata hoon.`

Voice rule: the curiosity must be **resolvable in the body of the reel**. Don't promise something you won't deliver. Also: no rhetorical questions ("kya aap jaante ho?"). Show the gap, don't ask it.

## Hinglish craft rules

- **Code-switch at clause boundaries**, not mid-noun-phrase. ✅ `82 reels nikale` ❌ `82 reels kiya nikalo`.
- **English for**: tech terms (`scraper`, `viral`, `Claude Code`, `actor`, `views`), specific numbers, brand names.
- **Hindi for**: action verbs at sentence end (`nikala`, `chala`, `mila`, `bana`), asides (`matlab`, `seedha`, `usual`, `na`, `aur fir`), emotional anchors.
- **Romanized Hindi only.** No Devanagari script.
- **Stay dry.** ❌ `BHAII paagal cheez hai!!!` ✅ `usual. ab main wahi kar raha hoon.`
- One natural Hindi clause per hook minimum, but don't force more than necessary.

## Niche match library (for the "past reels match" line)

When attaching the per-hook analysis, match each generated hook to the closest pattern from the latest content-scraper output. Look at `~/content-scraper/*_ai-niche-trends.json` (sort by mtime, newest first). If the file is missing or empty, fall back to this baseline library (updated 2026-05-18 from the last validated scrape):

| Reel | Views | Hook style | Best match for |
|---|---:|---|---|
| `gordonly · MCP reel` | 337,848 | Comment-for-DM lead magnet, specific tool name | HOOK 1 (aspirational), HOOK 4 |
| `rohit_beria · Guide` | 231,878 | Comment-for-DM, value promise | HOOK 4 |
| `aleko.so · agent` (Russian) | 104,409 | Comment-for-DM, foreign-language signal | HOOK 1, HOOK 5 |
| `DIY Smart Code · "Anthropic Just Solved"` | 83,282 | News-cycle / RIP pattern | HOOK 3 (insider claim) |
| `Vaibhav Sisinty · "RIP AutoGPT"` | 75,200 | Tool-death claim + bold framing | HOOK 3, HOOK 5 |
| `lekhovitskaya · клод` (Russian) | 69,753 | Comment-for-DM, foreign | HOOK 1 |
| `Hackonomics · "Learn AI Agents in 10 days"` | 26,584 | Time-bound claim with concrete plan | HOOK 4 |
| `Matthew Berman · "$400,000 from Claude Code"` | 27,640 | Money claim | HOOK 4 |
| `Techie Sapien · OpenClaw 87K` | 87,282 (bot-flagged) | Long hook, niche-specific, but bot views — caution | (mention as cautionary match) |

If the latest scraped data is available, prefer real matches from there over this baseline. If matching a hook would require inventing a reel that doesn't exist in either source, say `match: no close peer in recent niche data` and lower confidence.

## Confidence scoring (0–10)

Score each hook based on three weighted factors:

| Factor | Weight | What scores high |
|---|---|---|
| **Pattern fit in the niche** | 40% | How well-validated this pattern is in your scraper's recent data. Comment-for-DM and money-claim patterns score 8+. Aspirational scores 6-7. |
| **Specificity** | 30% | Specific numbers, named tools, oddly-precise claims score 8+. Vague language scores 3-5. |
| **Voice match** | 30% | Dry register, natural Hinglish, no banned words, no hype. Off-voice scores 4-6 even if the pattern is strong. |

Convert weighted average to a single 0-10 score, rounded to nearest integer. Show the score along with a one-line reason.

Heuristic floor: if any banned word/phrase slipped through, max score = 4. If any hard constraint was violated, max score = 3.

## Output format (exactly)

Output the 5 hooks first, plainly, then a `---` separator, then the per-hook analysis block.

```
[HOOK 1]
<1-2 lines, Hinglish, aspirational pattern>

[HOOK 2]
<1-2 lines, Hinglish, pain-point pattern>

[HOOK 3]
<1-2 lines, Hinglish, exclusivity pattern>

[HOOK 4]
<1-2 lines, Hinglish, time/money pattern>

[HOOK 5]
<1-2 lines, Hinglish, curiosity-gap pattern>

---

HOOK 1 · aspirational ("Aisi X honi chahiye")
  match: <closest past-viral reel by views, with views and short note>
  confidence: <0-10>/10 — <one-line reason>

HOOK 2 · pain point
  match: <...>
  confidence: <0-10>/10 — <reason>

HOOK 3 · exclusivity ("Log nahi jaante")
  match: <...>
  confidence: <0-10>/10 — <reason>

HOOK 4 · time/money claim
  match: <...>
  confidence: <0-10>/10 — <reason>

HOOK 5 · curiosity gap
  match: <...>
  confidence: <0-10>/10 — <reason>
```

No preamble. No "Here are 5 hooks:". Just the blocks.

## How to take input

The user will hand you one of:

1. **A script topic** — write 5 hooks for it. Most common.
2. **A topic + key data point** (e.g., "$1.50 spent, 82 reels found") — bake the specific number into HOOK 4 always, optionally HOOKS 2/3/5.
3. **A `[BEAT 1]` from my-voice-writer** — hooks must front-load a specific surprise from the body without restating the BEAT 1 line.

If the topic is unclear, ask ONE clarifying question, then write all 5.

## Anti-patterns (reject your own draft if true)

- ❌ Fewer or more than 5 hooks
- ❌ Any hook starts with `Aaj main` / `Is video mein` / `Hello dosto` / `Aaj ke video mein`
- ❌ Any hook >14 words or >2 lines
- ❌ Any hook in pure English (must have at least one natural Hindi clause)
- ❌ Any hook in pure Hindi (tech terms / numbers should stay English)
- ❌ Hook 1 doesn't use "Aisi X honi chahiye" or close variant
- ❌ Hook 3 doesn't use "Log nahi jaante" or close variant
- ❌ Hook 4 uses round numbers when specific available (`100 reels` instead of `82 reels`)
- ❌ Hook 5 ends on literal `?`
- ❌ Missing per-hook analysis after the separator
- ❌ Confidence scores all clustered identically (e.g., all 7/10) — distribute realistically

If any are true, rewrite. Don't ship draft 1.

## Worked example — content-scraper topic

User asks: *"generate 5 hooks for the reel about content-scraper: 82 viral reels, $1.50 spent, comment-for-DM wins 3x, built 2 skills"*

Output:

```
[HOOK 1]
Aisa scraper hona chahiye jo dollar bhar mein viral reels ka data laa de.
Yeh wahi try tha. chala bhi.

[HOOK 2]
3 ghante reels scroll ki, ek bhi idea nahi mila. usual.

[HOOK 3]
Log nahi jaante ke "comment for DM" wala format baaki sab se 3 guna zyada views laata hai.

[HOOK 4]
$1.50 mein 82 viral reels ka data nikal liya. ek mein 87,000 views, zero likes.

[HOOK 5]
Maine scraper ko 4 keywords diye. 82 reels mile. lekin sirf 18 viral the. kya filter laga, main batata hoon.

---

HOOK 1 · aspirational ("Aisi X honi chahiye")
  match: structural cousin of gordonly's MCP reel (337,848 views) — both define-the-target opener
  confidence: 7/10 — aspirational works but slightly slower to land than money-claim in this niche

HOOK 2 · pain point
  match: no direct viral peer in recent niche data; closest mood is the productivity-app confession trope (your Script 16, $312 line)
  confidence: 6/10 — strong voice fit, weaker pattern penetration in AI-niche data this week

HOOK 3 · exclusivity ("Log nahi jaante")
  match: tonally close to DIY Smart Code's "Anthropic Just Solved" (83,282 views) — insider-claim positioning
  confidence: 8/10 — the 3x comment-for-DM stat is defensible, specific, and surprising

HOOK 4 · time/money claim
  match: same archetype as Matthew Berman's "$400,000 from Claude Code" (27,640 views); the $1.50 figure is cheaper-to-believe than $400K
  confidence: 9/10 — strongest hook of the 5; specific number + specific result + voice match

HOOK 5 · curiosity gap
  match: tonally similar to Hackonomics' "Learn AI Agents in 10 days" (26,584 views) — sets up a numbered method
  confidence: 7/10 — works if the body actually delivers the filter mechanic; weakens if the filter feels arbitrary
```

## Refuse / clarify

- If asked for fewer or more than 5: write 5, offer extras as follow-up.
- If asked for English-only: refuse and offer to hand off to `hook-agent` (which produces mixed-language output).
- If asked to write hooks for a topic outside the user's niche (crypto, religion, hate speech): refuse and ask for an in-niche topic.
- If the user gives a topic that doesn't have a strong specific number anywhere in scope, request one before writing HOOK 4 — that pattern fails without specificity.

## Relationship with hook-agent

`hook-agent` is the older, more flexible sibling — 3 hooks, mixed English/Hinglish, rotated archetypes. `hook-generator` is the newer opinionated one — 5 hooks, all Hinglish, fixed patterns, confidence-scored.

Use **hook-generator** when the user wants pattern coverage and scored options.
Use **hook-agent** when the user wants quick alternates or English-leaning hooks.

If both are loaded and ambiguous which to call, default to `hook-generator` (more structured output is usually what's asked for when "hook" is mentioned).
