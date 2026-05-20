"""Streamlit GUI for the content-scraper pipeline.

7 numbered steps, each with Run / Edit / Regenerate / Return-to-Edit controls.
File-based persistence via ~/content-scraper/YYYY-MM-DD-reel-package/.

Run:
    streamlit run gui/app.py
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

# -- Paths ---------------------------------------------------------------------

REPO = Path(__file__).resolve().parent.parent
HOME = Path.home()
WORK = HOME / "content-scraper"
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
PKG = WORK / f"{TODAY}-reel-package"
PKG.mkdir(parents=True, exist_ok=True)

# -- State files (per-step artifacts) ------------------------------------------

ARTIFACTS = {
    "scrape":   PKG / f"{TODAY}_ai-niche-trends.json",
    "validate": PKG / "validation.md",
    "topics":   PKG / "topics.md",
    "hooks":    PKG / "hooks.md",
    "script":   PKG / "script.md",
    "shotlist": PKG / "shotlist.md",
    "profiles": PKG / "profiles.json",
    "dms":      PKG / "dms.md",
}

# -- Step definitions ----------------------------------------------------------

STEPS = [
    ("1. Setup",       "setup"),
    ("2. Scrape",      "scrape"),
    ("3. Validate",    "validate"),
    ("4. Topics",      "topics"),
    ("5. Hooks",       "hooks"),
    ("6. Script",      "script"),
    ("7. Shotlist",    "shotlist"),
    ("8. DMs",         "dms"),
    ("9. Done",        "done"),
]


# -- Helpers -------------------------------------------------------------------

def has_artifact(key: str) -> bool:
    p = ARTIFACTS.get(key)
    return p is not None and p.exists() and p.stat().st_size > 0


def read_artifact(key: str) -> str:
    p = ARTIFACTS.get(key)
    return p.read_text() if p and p.exists() else ""


def write_artifact(key: str, content: str) -> None:
    p = ARTIFACTS.get(key)
    if p:
        p.write_text(content)


def claude_available() -> bool:
    return shutil.which("claude") is not None


def run_subprocess(cmd: str, cwd: Path | None = None) -> tuple[int, str, str]:
    """Run a shell command, return (returncode, stdout, stderr)."""
    proc = subprocess.run(
        cmd, shell=True, cwd=cwd or REPO,
        capture_output=True, text=True, env={**os.environ},
    )
    return proc.returncode, proc.stdout, proc.stderr


def call_claude(prompt: str) -> str:
    """Invoke Claude Code headlessly. Returns stdout or an error message."""
    if not claude_available():
        return f"⚠️ `claude` CLI not on PATH.\n\nManually run this in a Claude Code session and paste the output here:\n\n```\n{prompt}\n```"
    rc, out, err = run_subprocess(f"claude -p {shlex.quote(prompt)}")
    if rc != 0:
        return f"⚠️ claude returned exit {rc}:\n\n{err}"
    return out


def goto(step_key: str) -> None:
    st.session_state["step"] = step_key
    st.rerun()


# -- State init ----------------------------------------------------------------

def init_state() -> None:
    if "step" not in st.session_state:
        st.session_state["step"] = "setup"
    if "topic" not in st.session_state:
        st.session_state["topic"] = ""
    if "use_cache" not in st.session_state:
        st.session_state["use_cache"] = True
    if "chosen_hook" not in st.session_state:
        st.session_state["chosen_hook"] = None
    if "log" not in st.session_state:
        st.session_state["log"] = []


def log(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state["log"].append(f"[{ts}] {msg}")


# -- UI: Sidebar ---------------------------------------------------------------

def render_sidebar() -> None:
    st.sidebar.title("📦 reel pipeline")
    st.sidebar.caption(f"package: {PKG.name}")

    st.sidebar.markdown("---")
    st.sidebar.subheader("Steps")
    current = st.session_state["step"]
    for label, key in STEPS:
        done = key in ARTIFACTS and has_artifact(key)
        prefix = "✅" if done else ("🟢" if key == current else "  ")
        if st.sidebar.button(f"{prefix} {label}", key=f"nav_{key}", use_container_width=True):
            goto(key)

    st.sidebar.markdown("---")
    st.sidebar.subheader("Environment")
    apify_ok = bool(os.environ.get("APIFY_TOKEN"))
    claude_ok = claude_available()
    st.sidebar.markdown(f"- APIFY_TOKEN: {'✅' if apify_ok else '❌'}")
    st.sidebar.markdown(f"- claude CLI: {'✅' if claude_ok else '⚠️ (manual fallback)'}")

    if st.session_state["log"]:
        with st.sidebar.expander(f"Log ({len(st.session_state['log'])} lines)", expanded=False):
            for line in st.session_state["log"][-30:]:
                st.text(line)

    st.sidebar.markdown("---")
    if st.sidebar.button("🗑️ Reset session", use_container_width=True):
        st.session_state.clear()
        st.rerun()


# -- UI: Step renderers --------------------------------------------------------

def render_setup() -> None:
    st.header("1. Setup")
    st.caption("Topic + scrape preferences. The whole pipeline keys off these.")

    st.session_state["topic"] = st.text_input(
        "Reel topic",
        value=st.session_state["topic"] or "(auto-pick from top cluster)",
        help="What's today's reel about? Leave as auto-pick to let the validator's top cluster decide.",
    )
    st.session_state["use_cache"] = st.checkbox(
        "Use cached scrape if available today",
        value=st.session_state["use_cache"],
        help=f"If unchecked, re-runs the Apify scrape (~$0.50). Cache lives in {WORK}.",
    )

    if not os.environ.get("APIFY_TOKEN"):
        st.error("APIFY_TOKEN env var not set. Run `source ~/.zshrc` before launching Streamlit, or export it inline.")
        return

    if st.button("Continue → Scrape", type="primary"):
        goto("scrape")


def render_scrape() -> None:
    st.header("2. Scrape")
    st.caption("Pulls last-7-day IG Reels + YouTube Shorts via Apify, then runs process.py.")

    cached = has_artifact("scrape")
    if cached and st.session_state.get("use_cache"):
        st.success(f"✅ Cached scrape found: {ARTIFACTS['scrape'].name}")
        trends = json.loads(read_artifact("scrape"))
        st.metric("Posts kept", len(trends))
        viral = sum(1 for r in trends if r.get("viral"))
        st.metric("VIRAL flagged", viral)
        st.dataframe(
            [{"platform": r["platform"], "author": r["author"], "views": r["views"],
              "er": r["er"], "viral": r["viral"], "hook": (r["hook"] or "")[:60]}
             for r in sorted(trends, key=lambda x: x.get("views", 0), reverse=True)[:20]],
            use_container_width=True, height=400,
        )

    col1, col2 = st.columns([1, 1])
    with col1:
        run_label = "Re-scrape (~$0.50)" if cached else "Run scrape (~$0.50)"
        if st.button(run_label, type="primary"):
            with st.spinner("Running Apify scrape — this takes 3-10 min..."):
                rc, out, err = run_subprocess("bash bin/run-scrape.sh", cwd=REPO)
                log(f"scrape rc={rc}")
                if rc == 0:
                    # Copy artifacts into PKG
                    for src_name in (f"{TODAY}_ai-niche-trends.json", f"{TODAY}_ai-niche-trends.csv"):
                        src = WORK / src_name
                        if src.exists():
                            shutil.copy(src, PKG / src_name)
                    st.success("Scrape complete.")
                    st.rerun()
                else:
                    st.error(f"Scrape failed (rc={rc}):\n```\n{err}\n```")
    with col2:
        if cached and st.button("Continue → Validate"):
            goto("validate")


def render_validate() -> None:
    st.header("3. Validate")
    st.caption("Strict niche filter + hook quality + bot detection + transcript completeness.")

    if not has_artifact("scrape"):
        st.warning("Run scrape first.")
        if st.button("← Back to Scrape"):
            goto("scrape")
        return

    cached = has_artifact("validate")
    if cached:
        st.markdown(read_artifact("validate"))

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Re-validate" if cached else "Run validate", type="primary"):
            with st.spinner("Validating..."):
                rc, out, err = run_subprocess(f"python3 content-validator/validate.py", cwd=REPO)
                log(f"validate rc={rc}")
                if rc == 0:
                    write_artifact("validate", out)
                    st.rerun()
                else:
                    st.error(f"Validate failed (rc={rc}):\n{err}")
    with col2:
        if cached and st.button("Continue → Topics"):
            goto("topics")


def render_topics() -> None:
    st.header("4. Topics")
    st.caption("Cluster posts by topic, rank by total views. Pick the top one or override.")

    if not has_artifact("scrape"):
        st.warning("Run scrape first.")
        return

    cached = has_artifact("topics")
    if cached:
        st.markdown(read_artifact("topics"))

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("Re-cluster" if cached else "Run cluster", type="primary"):
            with st.spinner("Clustering..."):
                rc, out, err = run_subprocess("python3 bin/cluster-topics.py", cwd=REPO)
                log(f"cluster rc={rc}")
                if rc == 0:
                    write_artifact("topics", out)
                    st.rerun()
                else:
                    st.error(f"Cluster failed (rc={rc}):\n{err}")
    with col2:
        if cached and st.button("Use top topic"):
            # Parse "_Top topic: **X**_" from the markdown
            text = read_artifact("topics")
            for line in text.splitlines():
                if line.strip().startswith("_Top topic:"):
                    inferred = line.split("**")[1] if "**" in line else ""
                    st.session_state["topic"] = inferred
                    log(f"selected top topic: {inferred}")
                    goto("hooks")
                    break
    with col3:
        if st.button("Continue with manual topic →"):
            goto("hooks")


def render_hooks() -> None:
    st.header("5. Hooks")
    st.caption("5 hooks via hook-generator skill. Pick one or edit any.")
    st.info(f"Topic: **{st.session_state['topic'] or '(none — set in setup)'}**")

    cached = has_artifact("hooks")
    if cached:
        st.markdown(read_artifact("hooks"))

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Generate 5 hooks" if not cached else "Regenerate", type="primary"):
            prompt = f"Use the hook-generator skill on topic: {st.session_state['topic']}. Reference: {ARTIFACTS['topics']}"
            with st.spinner("Generating hooks..."):
                out = call_claude(prompt)
                write_artifact("hooks", out)
                log("hooks generated")
                st.rerun()
    with col2:
        if cached and st.button("Continue → Script"):
            goto("script")

    if cached:
        st.markdown("---")
        st.subheader("Edit hooks manually")
        edited = st.text_area("Hooks (markdown)", value=read_artifact("hooks"), height=400)
        if st.button("Save hook edits"):
            write_artifact("hooks", edited)
            log("hooks edited manually")
            st.success("Saved.")


def render_script() -> None:
    st.header("6. Script")
    st.caption("BEAT 1 → BEAT 2 → BEAT 3 → CTA via my-voice-writer.")
    st.info(f"Topic: **{st.session_state['topic'] or '(none)'}**")

    cached = has_artifact("script")
    if cached:
        st.code(read_artifact("script"), language="markdown")

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Generate script" if not cached else "Regenerate", type="primary"):
            prompt = (
                f"Use the my-voice-writer skill on topic: {st.session_state['topic']}. "
                f"Reference: {ARTIFACTS['topics']} and {ARTIFACTS['hooks']}"
            )
            with st.spinner("Writing in your voice..."):
                out = call_claude(prompt)
                write_artifact("script", out)
                log("script generated")
                st.rerun()
    with col2:
        if cached and st.button("Continue → Shotlist"):
            goto("shotlist")

    if cached:
        st.markdown("---")
        st.subheader("Edit script inline")
        edited = st.text_area("Script", value=read_artifact("script"), height=350)
        if st.button("Save script edits"):
            write_artifact("script", edited)
            log("script edited manually")
            st.success("Saved.")


def render_shotlist() -> None:
    st.header("7. Shotlist")
    st.caption("AI-generation shotlist via ai-visuals-writer.")

    if not has_artifact("script") or not has_artifact("hooks"):
        st.warning("Need script + hooks first.")
        return

    cached = has_artifact("shotlist")
    if cached:
        st.markdown(read_artifact("shotlist"))

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Generate shotlist" if not cached else "Regenerate", type="primary"):
            prompt = (
                f"Use the ai-visuals-writer skill. Script: {ARTIFACTS['script']}. "
                f"Hooks: {ARTIFACTS['hooks']}. Pick the highest-confidence hook as the opener."
            )
            with st.spinner("Building shotlist..."):
                out = call_claude(prompt)
                write_artifact("shotlist", out)
                log("shotlist generated")
                st.rerun()
    with col2:
        if cached and st.button("Continue → DMs"):
            goto("dms")


def render_dms() -> None:
    st.header("8. DMs (post-shoot)")
    st.caption("Personalized DMs for each commenter. Run after posting the reel.")

    st.markdown("Paste IG handles (one per line, with or without @):")
    handles = st.text_area("Handles", height=150, placeholder="@aleko_so\n@harryleemedia\ngordonly")

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Fetch profiles via Apify", type="primary"):
            if not handles.strip():
                st.warning("Paste some handles first.")
                return
            handles_file = PKG / "_handles.txt"
            handles_file.write_text(handles)
            cost_low = len(handles.splitlines()) * 0.01
            cost_high = len(handles.splitlines()) * 0.05
            with st.spinner(f"Fetching profiles (~${cost_low:.2f}-${cost_high:.2f})..."):
                rc, out, err = run_subprocess(
                    f"python3 dm-responder/fetch_commenters.py --file {handles_file}",
                    cwd=REPO,
                )
                if rc == 0:
                    write_artifact("profiles", out)
                    log(f"profiles fetched ({len(handles.splitlines())} handles)")
                    st.success("Profiles fetched.")
                    st.rerun()
                else:
                    st.error(f"Fetch failed:\n{err}")

    if has_artifact("profiles"):
        st.success(f"✅ Profiles cached: {ARTIFACTS['profiles'].name}")
        with col2:
            if st.button("Draft DMs", type="primary"):
                prompt = f"Use the dm-responder skill on profiles: {ARTIFACTS['profiles']}"
                with st.spinner("Drafting personalized DMs..."):
                    out = call_claude(prompt)
                    write_artifact("dms", out)
                    log("DMs drafted")
                    st.rerun()

    if has_artifact("dms"):
        st.markdown("---")
        st.subheader("Drafted DMs")
        st.markdown(read_artifact("dms"))


def render_done() -> None:
    st.header("9. Done")
    st.balloons()
    st.markdown(f"All artifacts saved to: `{PKG}`")

    files = sorted(PKG.glob("*"))
    if files:
        st.subheader("Package contents")
        for f in files:
            size_kb = f.stat().st_size / 1024
            col1, col2, col3 = st.columns([4, 1, 1])
            col1.text(f.name)
            col2.text(f"{size_kb:.1f} KB")
            with col3:
                if f.suffix in (".md", ".json", ".csv", ".txt"):
                    try:
                        st.download_button(
                            "↓", data=f.read_bytes(), file_name=f.name,
                            key=f"dl_{f.name}", use_container_width=True,
                        )
                    except Exception:
                        pass

    st.markdown("---")
    st.subheader("Return to edit")
    st.caption("Jump back to any step to refine before shipping.")
    cols = st.columns(7)
    edit_targets = [
        ("Setup", "setup"), ("Scrape", "scrape"), ("Validate", "validate"),
        ("Topics", "topics"), ("Hooks", "hooks"), ("Script", "script"),
        ("Shotlist", "shotlist"),
    ]
    for col, (label, key) in zip(cols, edit_targets):
        with col:
            if st.button(f"↩ {label}", key=f"return_{key}", use_container_width=True):
                goto(key)


# -- Universal "Return to Edit" footer -----------------------------------------

def render_return_to_edit_footer(current_step: str) -> None:
    st.markdown("---")
    edit_targets = [k for _, k in STEPS if k != current_step and k != "done"]
    cols = st.columns(len(edit_targets))
    for col, key in zip(cols, edit_targets):
        with col:
            label = next(lbl for lbl, k in STEPS if k == key)
            short = label.split(" ", 1)[1] if " " in label else label
            if st.button(f"↩ {short}", key=f"footer_return_{key}", use_container_width=True):
                goto(key)


# -- Main ----------------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title="reel pipeline", layout="wide", initial_sidebar_state="expanded")
    init_state()
    render_sidebar()

    step = st.session_state["step"]
    renderers = {
        "setup": render_setup,
        "scrape": render_scrape,
        "validate": render_validate,
        "topics": render_topics,
        "hooks": render_hooks,
        "script": render_script,
        "shotlist": render_shotlist,
        "dms": render_dms,
        "done": render_done,
    }
    renderer = renderers.get(step, render_setup)
    renderer()

    if step != "setup" and step != "done":
        render_return_to_edit_footer(step)


if __name__ == "__main__":
    main()
