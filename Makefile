# Makefile — chain the 7-skill pipeline end-to-end.
#
# Quick start:
#   make reel                              full pre-shoot pipeline (skills 1-6)
#   make reel TOPIC="text-photo vs text-video memes"
#   make dms HANDLES=commenters.txt        post-shoot DM generation (skill 7)
#   make help                              list all targets
#
# Requires: APIFY_TOKEN env var, curl, python3.
# Optionally: `claude` CLI on PATH (auto-invokes LLM-driven targets non-interactively).
# Without claude CLI, those targets print copy-paste instructions for a Claude Code session.

REPO        := $(shell pwd)
WORK        := $(HOME)/content-scraper
DATE        := $(shell date +%Y-%m-%d)
PKG         := $(WORK)/$(DATE)-reel-package
TOPIC       ?= the content-scraper itself (today's auto-pick)
HANDLES     ?=

# Detect optional Claude Code CLI
CLAUDE      := $(shell command -v claude 2>/dev/null)

# ANSI colors for readability
CYAN        := \033[1;36m
YELLOW      := \033[1;33m
GREEN       := \033[1;32m
DIM         := \033[2m
RESET       := \033[0m

.DEFAULT_GOAL := help
.PHONY: help reel gui scrape validate cluster hook script shotlist dms clean check-deps doctor

help:  ## Show this help
	@printf "$(CYAN)Usage:$(RESET)\n"
	@printf "  make $(YELLOW)TARGET$(RESET) [VAR=value]\n\n"
	@printf "$(CYAN)Variables:$(RESET)\n"
	@printf "  $(YELLOW)TOPIC$(RESET)=...     reel topic (default: auto-picked from top cluster)\n"
	@printf "  $(YELLOW)HANDLES$(RESET)=...   path to text file with one IG handle per line (for 'make dms')\n\n"
	@printf "$(CYAN)Targets:$(RESET)\n"
	@awk 'BEGIN {FS = ":.*?##"} /^[a-zA-Z_-]+:.*?##/ {printf "  $(YELLOW)%-12s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@printf "\n$(DIM)Claude CLI: %s$(RESET)\n" "$(if $(CLAUDE),detected at $(CLAUDE),NOT on PATH — LLM targets will print instructions)"

doctor: check-deps  ## Diagnose environment (token + tools)
	@printf "$(CYAN)Diagnostics$(RESET)\n"
	@printf "  repo:       $(REPO)\n"
	@printf "  work dir:   $(WORK)\n"
	@printf "  date:       $(DATE)\n"
	@printf "  package:    $(PKG)\n"
	@if [ -n "$$APIFY_TOKEN" ]; then printf "  $(GREEN)✓$(RESET) APIFY_TOKEN set\n"; else printf "  $(YELLOW)✗ APIFY_TOKEN not set — required for scrape$(RESET)\n"; fi
	@if [ -n "$(CLAUDE)" ]; then printf "  $(GREEN)✓$(RESET) claude CLI: $(CLAUDE)\n"; else printf "  $(YELLOW)✗ claude CLI not found — LLM targets need manual invocation$(RESET)\n"; fi
	@command -v transcribe >/dev/null 2>&1 && printf "  $(GREEN)✓$(RESET) transcribe (local Whisper)\n" || printf "  $(YELLOW)✗ transcribe not on PATH — see setup.md$(RESET)\n"

check-deps:
	@command -v curl >/dev/null 2>&1 || { echo "❌ curl required"; exit 1; }
	@command -v python3 >/dev/null 2>&1 || { echo "❌ python3 required"; exit 1; }

reel: scrape validate cluster hook script shotlist  ## Full pre-shoot pipeline (skills 1-6)
	@printf "\n$(GREEN)✅ Reel package ready:$(RESET) $(PKG)\n"
	@ls -1 $(PKG)/
	@printf "\n$(CYAN)Next:$(RESET) review $(PKG)/script.md, then shoot/generate per $(PKG)/shotlist.md\n"

gui:  ## Launch the Streamlit GUI (full pipeline, point-and-click)
	@command -v streamlit >/dev/null 2>&1 || python3 -c "import streamlit" 2>/dev/null || { \
		printf "$(YELLOW)Streamlit not installed.$(RESET) Run:\n"; \
		printf "  python3 -m pip install --user -r gui/requirements.txt\n"; \
		exit 1; }
	@printf "$(CYAN)→ Launching GUI at http://localhost:8501$(RESET)\n"
	@python3 -m streamlit run $(REPO)/gui/app.py

# --- Step 1/6 : Apify scrape ---
scrape: check-deps | $(PKG)  ## 1/6 — Apify scrape + process (IG + YT, ~5 min, ~$0.50)
	@printf "$(CYAN)→ Step 1/6:$(RESET) scrape\n"
	@bash $(REPO)/bin/run-scrape.sh
	@cp $(WORK)/$(DATE)_ai-niche-trends.csv $(PKG)/ 2>/dev/null || true
	@cp $(WORK)/$(DATE)_ai-niche-trends.json $(PKG)/ 2>/dev/null || true

# --- Step 2/6 : Validate ---
validate: | $(PKG)  ## 2/6 — content-validator (filter, hook scores, bot detection)
	@printf "$(CYAN)→ Step 2/6:$(RESET) validate\n"
	@python3 $(REPO)/content-validator/validate.py > $(PKG)/validation.md 2>&1 || (cat $(PKG)/validation.md; exit 1)
	@grep -E "^- " $(PKG)/validation.md | head -8 || true

# --- Step 3/6 : Cluster topics ---
cluster: | $(PKG)  ## 3/6 — topic clustering (picks the angle)
	@printf "$(CYAN)→ Step 3/6:$(RESET) cluster\n"
	@python3 $(REPO)/bin/cluster-topics.py > $(PKG)/topics.md
	@head -15 $(PKG)/topics.md
	@printf "$(DIM)... full table in $(PKG)/topics.md$(RESET)\n"

# --- Step 4/6 : Hook generator (LLM) ---
hook: | $(PKG)  ## 4/6 — hook-generator (5 Hinglish hooks, scored)
	@printf "$(CYAN)→ Step 4/6:$(RESET) hook-generator\n"
ifneq ($(CLAUDE),)
	@$(CLAUDE) -p "Use the hook-generator skill on topic: $(TOPIC). Reference: $(PKG)/topics.md" > $(PKG)/hooks.md
	@printf "$(GREEN)  saved:$(RESET) $(PKG)/hooks.md\n"
else
	@printf "$(YELLOW)  ⚠ claude CLI not on PATH$(RESET)\n"
	@printf "  Manual step: in a Claude Code session, run:\n"
	@printf "    $(DIM)\"Read $(PKG)/topics.md, then run hook-generator on: $(TOPIC)\"$(RESET)\n"
	@printf "  Save output as $(PKG)/hooks.md before continuing.\n"
endif

# --- Step 5/6 : Voice writer (LLM) ---
script: | $(PKG)  ## 5/6 — my-voice-writer ([BEAT 1] → [CTA] script)
	@printf "$(CYAN)→ Step 5/6:$(RESET) my-voice-writer\n"
ifneq ($(CLAUDE),)
	@$(CLAUDE) -p "Use the my-voice-writer skill on topic: $(TOPIC). Reference: $(PKG)/topics.md and $(PKG)/hooks.md" > $(PKG)/script.md
	@printf "$(GREEN)  saved:$(RESET) $(PKG)/script.md\n"
else
	@printf "$(YELLOW)  ⚠ claude CLI not on PATH$(RESET)\n"
	@printf "  Manual step: in a Claude Code session, run:\n"
	@printf "    $(DIM)\"Run my-voice-writer on: $(TOPIC) (data: $(PKG)/topics.md)\"$(RESET)\n"
	@printf "  Save output as $(PKG)/script.md before continuing.\n"
endif

# --- Step 6/6 : AI visuals ---
shotlist: | $(PKG)  ## 6/6 — ai-visuals-writer (AI shotlist + VO + music + budget)
	@printf "$(CYAN)→ Step 6/6:$(RESET) ai-visuals-writer\n"
ifneq ($(CLAUDE),)
	@$(CLAUDE) -p "Use the ai-visuals-writer skill. Script: $(PKG)/script.md. Hooks: $(PKG)/hooks.md. Pick the highest-confidence hook as the opener." > $(PKG)/shotlist.md
	@printf "$(GREEN)  saved:$(RESET) $(PKG)/shotlist.md\n"
else
	@printf "$(YELLOW)  ⚠ claude CLI not on PATH$(RESET)\n"
	@printf "  Manual step: in a Claude Code session, run:\n"
	@printf "    $(DIM)\"Run ai-visuals-writer on script $(PKG)/script.md and hooks $(PKG)/hooks.md\"$(RESET)\n"
endif

# --- Post-shoot : DMs (skill 7) ---
dms:  ## Post-shoot — personalized DMs for commenters. HANDLES=path/to/file.txt
	@if [ -z "$(HANDLES)" ]; then \
		printf "$(YELLOW)error:$(RESET) HANDLES variable required\n"; \
		printf "  usage: make dms HANDLES=commenters.txt\n"; \
		exit 2; \
	fi
	@printf "$(CYAN)→ Post-shoot:$(RESET) dm-responder\n"
	@mkdir -p $(PKG)
	@printf "  1. cost estimate...\n"
	@python3 $(REPO)/dm-responder/fetch_commenters.py --file $(HANDLES) --dry-run 2>&1 | tail -3
	@printf "  2. fetching profiles via Apify...\n"
	@python3 $(REPO)/dm-responder/fetch_commenters.py --file $(HANDLES) > $(PKG)/profiles.json
ifneq ($(CLAUDE),)
	@printf "  3. drafting personalized DMs...\n"
	@$(CLAUDE) -p "Use the dm-responder skill. Profiles JSON: $(PKG)/profiles.json" > $(PKG)/dms.md
	@printf "$(GREEN)✅ Done:$(RESET) $(PKG)/dms.md\n"
else
	@printf "$(YELLOW)  ⚠ claude CLI not on PATH$(RESET)\n"
	@printf "  Manual step: in a Claude Code session, run:\n"
	@printf "    $(DIM)\"Use dm-responder on profiles in $(PKG)/profiles.json\"$(RESET)\n"
endif

# --- Housekeeping ---
clean:  ## Remove today's package dir
	rm -rf $(PKG)
	@printf "$(GREEN)removed:$(RESET) $(PKG)\n"

$(PKG):
	@mkdir -p $@
