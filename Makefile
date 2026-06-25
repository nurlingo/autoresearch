# Resolve the env313 interpreter (matplotlib + 3.13) via pyenv; fall back to python3.
PYTHON ?= $(shell pyenv which python 2>/dev/null || command -v python3)

.PHONY: eval exp plot compare archive

# Score solution.py against the fixed dataset.
eval:
	@$(PYTHON) eval.py

# One experiment: run eval + append a uniform row to results.tsv.
# Usage: make exp DESC="increase detector trigram weight"
exp:
	@$(PYTHON) tools/log_experiment.py "$(DESC)"

# Render this run's progress -> progress.png
plot:
	@$(PYTHON) tools/plot.py

# Overlay multiple runs -> comparison.png
# Usage: make compare RUNS="runs/claude-*.tsv runs/codex-*.tsv"
compare:
	@$(PYTHON) tools/plot.py --compare $(RUNS)

# Archive the current run log for the paper. Usage: make archive AGENT=claude
archive:
	@mkdir -p runs && cp results.tsv runs/$(AGENT)-$$(date +%y%m%d-%H%M).tsv && \
	  echo "archived -> runs/$(AGENT)-$$(date +%y%m%d-%H%M).tsv"
