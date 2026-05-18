#!/usr/bin/env python3
"""Validate the latest content-scraper trends file.

Usage:
    python validate.py                 # report-only, no transcription
    python validate.py --fill-transcripts  # also re-run local Whisper on missing transcripts (slow, ~30-60s each)
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.home() / "content-scraper"


# --- Strict niche filter ----------------------------------------------------

PRIMARY = re.compile(
    r"\b(claude\s*code|claudecode|"
    r"ai\s*agents?|aiagent|"
    r"\bn8n\b|"
    r"vibe\s*coding|vibecoding|"
    r"claude\s*skills?|claudeskill|"
    r"openclaw)\b",
    re.IGNORECASE,
)

SECONDARY = re.compile(
    r"\b(cursor|windsurf|mcp|langgraph|langchain|replit\s*agent|"
    r"lovable|bolt\.new|v0\.dev|agent\s*sdk|crewai|autogpt|"
    r"chatgpt\s*agent|gpt\s*agent|anthropic|copilot)\b",
    re.IGNORECASE,
)

AUTOMATION_VERBS = re.compile(
    r"\b(automate[ds]?|automation|workflow|agent that|build a (bot|agent)|"
    r"no[- ]?code|low[- ]?code|trigger|webhook|integration)\b",
    re.IGNORECASE,
)

GENERIC_AI_NOISE = re.compile(
    r"\b(midjourney|dalle|stable diffusion|ai (made|generated) (image|art)|"
    r"ai (girlfriend|gf)|ai influencer|ai (porn|nsfw))\b",
    re.IGNORECASE,
)


def strict_niche(text: str) -> tuple[bool, str]:
    """Return (pass, reason). Stricter than the scraper's filter."""
    if not text:
        return False, "empty_text"

    if GENERIC_AI_NOISE.search(text):
        return False, "generic_ai_noise"

    if PRIMARY.search(text):
        return True, "primary_match"

    secondary_count = len(SECONDARY.findall(text))
    if secondary_count >= 2:
        return True, "multi_secondary"

    if SECONDARY.search(text) and AUTOMATION_VERBS.search(text):
        return True, "secondary_plus_automation"

    return False, "no_strong_signal"


# --- Hook scoring -----------------------------------------------------------

NUMBER_RE = re.compile(r"\$[\d,]+|[\d,]{2,}|\b\d+x\b", re.IGNORECASE)
TOOL_RE = re.compile(r"\b(claude|n8n|cursor|gpt|anthropic|mcp|openclaw|agent)\b", re.IGNORECASE)
CLAIM_RE = re.compile(
    r"\b(just\s+solved|nobody\s+uses|will\s+change|rip\b|secret|actually|"
    r"changed\s+everything|biggest|never|always|truth|exposed|"
    r"\?$)",
    re.IGNORECASE,
)
CTA_RE = re.compile(
    r"\b(comment\s+[\"“‘]?\w+|save\s+this|try\s+this|"
    r"Напиши|Пиши|"  # Russian "write"/"type"
    r"send\s+me|dm\s+me)\b",
    re.IGNORECASE,
)
TRIGGER_RE = re.compile(
    r"(\$[\d,]+k?|\bsecret\b|\brip\b|🤯|😱|\bwild\b|\binsane\b|\bcrazy\b)",
    re.IGNORECASE,
)


def hook_score(hook: str) -> tuple[int, list[str]]:
    if not hook:
        return 0, ["empty"]
    h = hook.strip()
    score = 0
    reasons = []
    if NUMBER_RE.search(h) or TOOL_RE.search(h):
        score += 1
        reasons.append("specific")
    if CLAIM_RE.search(h):
        score += 1
        reasons.append("claim_or_q")
    if CTA_RE.search(h):
        score += 1
        reasons.append("cta")
    if 25 <= len(h) <= 75:
        score += 1
        reasons.append("good_length")
    if TRIGGER_RE.search(h):
        score += 1
        reasons.append("trigger")
    return score, reasons


# --- ER sanity --------------------------------------------------------------

def er_flags(row: dict) -> list[str]:
    flags = []
    v = row.get("views") or 0
    l = row.get("likes") or 0
    c = row.get("comments") or 0
    er = row.get("er") or 0
    if v > 50_000 and l < 10:
        flags.append("suspicious_bot_views")
    if v > 100_000 and (l + c) / max(v, 1) < 0.001:
        flags.append("extreme_engagement_suppression")
    if row.get("viral") and row.get("er_basis") not in ("views",):
        flags.append("viral_no_view_data")
    if er > 0.3 and v < 5_000:
        flags.append("low_volume_high_er")
    return flags


# --- Transcript completeness ------------------------------------------------

NON_SPEECH_RE = re.compile(r"^\s*(\[[^\]]+\]\s*)+$", re.IGNORECASE)


def transcript_status(t: str) -> str:
    if not t or not t.strip():
        return "missing"
    s = t.strip()
    if NON_SPEECH_RE.match(s):
        return "non_speech"
    if len(s) < 20:
        return "too_short"
    return "ok"


# --- Main -------------------------------------------------------------------

def find_latest():
    files = sorted(ROOT.glob("*_ai-niche-trends.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        print(f"no trends file in {ROOT}", file=sys.stderr)
        sys.exit(1)
    return files[0]


def md_table(rows: list[dict], cols: list[str], limit: int = 20) -> str:
    if not rows:
        return "_(none)_\n"
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for r in rows[:limit]:
        cells = []
        for c in cols:
            v = r.get(c, "")
            if isinstance(v, (int, float)):
                v = f"{v:,}" if isinstance(v, int) else f"{v:.3f}"
            else:
                v = str(v).replace("|", "\\|").replace("\n", " ")[:60]
            cells.append(v)
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out) + "\n"


def fill_transcripts(rows: list[dict]) -> int:
    """Run local `transcribe` on rows whose transcript_status != 'ok'. Mutates rows in place."""
    targets = [r for r in rows if r.get("_t_status") != "ok" and r.get("url")]
    filled = 0
    for i, r in enumerate(targets, 1):
        print(f"[{i}/{len(targets)}] transcribe {r['platform']} {r['url']}...", file=sys.stderr)
        try:
            result = subprocess.run(
                ["transcribe", r["url"], "-l", "auto"],
                capture_output=True, text=True, timeout=300,
            )
            if result.returncode == 0 and result.stdout.strip():
                # strip timestamp lines, keep text
                lines = []
                for line in result.stdout.splitlines():
                    m = re.match(r"^\[[\d:.]+\s*-->\s*[\d:.]+\]\s*(.+)$", line)
                    lines.append(m.group(1) if m else line.strip())
                r["transcript"] = " ".join(l for l in lines if l).strip()
                r["_t_status"] = transcript_status(r["transcript"])
                if r["_t_status"] == "ok":
                    filled += 1
                    print(f"  ok ({len(r['transcript'])} chars)", file=sys.stderr)
                else:
                    print(f"  still {r['_t_status']}", file=sys.stderr)
            else:
                print(f"  failed: {result.stderr.splitlines()[-1] if result.stderr else 'no output'}", file=sys.stderr)
        except subprocess.TimeoutExpired:
            print(f"  timeout", file=sys.stderr)
        except FileNotFoundError:
            print(f"  ERROR: `transcribe` not on PATH. Install per content-scraper SKILL.md.", file=sys.stderr)
            return filled
    return filled


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fill-transcripts", action="store_true",
                    help="Run local Whisper on rows with missing transcripts (~30-60s each)")
    ap.add_argument("--input", help="Specific trends.json (default: newest)")
    args = ap.parse_args()

    path = Path(args.input) if args.input else find_latest()
    print(f"# Validating {path.name}\n", file=sys.stderr)
    rows = json.load(open(path))

    # Niche
    false_pos = []
    for r in rows:
        text = " ".join([r.get("hook", ""), r.get("caption", ""), r.get("transcript", "")])
        ok, reason = strict_niche(text)
        r["_niche_ok"] = ok
        r["_niche_reason"] = reason
        if not ok:
            false_pos.append(r)

    # Hooks
    for r in rows:
        s, why = hook_score(r.get("hook", ""))
        r["_hook_score"] = s
        r["_hook_reasons"] = why

    top_hooks = sorted([r for r in rows if r["_hook_score"] >= 4], key=lambda x: -x["views"])
    weak_hooks = sorted([r for r in rows if r["_hook_score"] <= 1], key=lambda x: -x["views"])

    # ER sanity
    for r in rows:
        r["_er_flags"] = er_flags(r)
    sus = [r for r in rows if r["_er_flags"]]

    # Transcripts (VIRAL only)
    for r in rows:
        r["_t_status"] = transcript_status(r.get("transcript", ""))
    viral_rows = [r for r in rows if r.get("viral")]
    missing_tr = [r for r in viral_rows if r["_t_status"] != "ok"]

    # Optionally fill transcripts
    if args.fill_transcripts and missing_tr:
        print(f"\n→ Filling {len(missing_tr)} missing transcripts via local Whisper...", file=sys.stderr)
        filled = fill_transcripts(missing_tr)
        print(f"→ Filled {filled}/{len(missing_tr)}\n", file=sys.stderr)
        # Persist back to source trends file so future runs don't redo
        clean_rows = [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]
        with open(path, "w") as f:
            json.dump(clean_rows, f, indent=2, default=str)
        print(f"→ Persisted updated transcripts to {path.name}", file=sys.stderr)
        # Recompute final missing list after fill
        missing_tr = [r for r in viral_rows if r["_t_status"] != "ok"]

    # --- Report ---
    print(f"# Validation Report — {path.name}\n")
    print(f"## Summary\n")
    print(f"- Total posts: **{len(rows)}**")
    print(f"- False positives (strict niche): **{len(false_pos)}** ({100*len(false_pos)/len(rows):.0f}%)")
    print(f"- Strong hooks (score ≥4): **{len(top_hooks)}**")
    print(f"- Weak hooks (score ≤1): **{len(weak_hooks)}**")
    print(f"- Suspicious engagement rows: **{len(sus)}**")
    print(f"- VIRAL posts missing real transcripts: **{len(missing_tr)}/{len(viral_rows)}**\n")

    print("## False positives (strict niche failed)\n")
    print(md_table(
        [{"platform": r["platform"], "author": r["author"], "views": r["views"],
          "reason": r["_niche_reason"], "hook": r["hook"]} for r in false_pos],
        ["platform", "author", "views", "reason", "hook"],
        limit=15,
    ))

    print("## Top hooks (score ≥4)\n")
    print(md_table(
        [{"score": r["_hook_score"], "platform": r["platform"], "views": r["views"],
          "hook": r["hook"]} for r in top_hooks],
        ["score", "platform", "views", "hook"],
        limit=10,
    ))

    print("## Weak hooks (score ≤1)\n")
    print(md_table(
        [{"score": r["_hook_score"], "platform": r["platform"], "views": r["views"],
          "hook": r["hook"]} for r in weak_hooks],
        ["score", "platform", "views", "hook"],
        limit=10,
    ))

    print("## Suspicious engagement\n")
    print(md_table(
        [{"platform": r["platform"], "author": r["author"], "views": r["views"],
          "likes": r["likes"], "er": r["er"], "flags": ", ".join(r["_er_flags"])} for r in sus],
        ["platform", "author", "views", "likes", "er", "flags"],
        limit=15,
    ))

    print("## Missing/weak transcripts (VIRAL only)\n")
    print(md_table(
        [{"platform": r["platform"], "author": r["author"], "views": r["views"],
          "status": r["_t_status"], "url": r["url"]} for r in missing_tr],
        ["platform", "author", "views", "status", "url"],
        limit=20,
    ))

    # Save full validation file
    out_path = ROOT / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}_validation.json"
    with open(out_path, "w") as f:
        json.dump({
            "source": str(path),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total": len(rows),
                "false_positives": len(false_pos),
                "top_hooks": len(top_hooks),
                "weak_hooks": len(weak_hooks),
                "suspicious_er": len(sus),
                "missing_transcripts_viral": len(missing_tr),
            },
            "rows": [{k: v for k, v in r.items()} for r in rows],
        }, f, indent=2, default=str)
    print(f"\n_Full output: `{out_path}`_")
    if missing_tr and not args.fill_transcripts:
        mins = round(len(missing_tr) * 0.75, 1)
        print(f"\n→ Run with `--fill-transcripts` to fill {len(missing_tr)} gaps via local Whisper (~{mins} min).")


if __name__ == "__main__":
    main()
