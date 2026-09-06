# Stage 2 harness — within-ayah mistake events. Mirrors the Stage-1 Makefile.
PYTHON ?= $(shell pyenv which python 2>/dev/null || command -v python3)
# Pilot mode: the calibration batch is LLM-proposed + human-pending; score it too.
# Drop AR_EVAL_ARGS once labels are human-reviewed (label_status=reviewed).
export AR_EVAL_ARGS ?= --include-machine
FMR_REPO ?= $(abspath ../../follow_my_reading)

.PHONY: data eval exp test baselines freeze plot archive

data:            ## rebuild stage2/data from the root split + review labels (needs production files)
	@cd .. && $(PYTHON) stage2/tools/export.py

eval:            ## score solution.py on train
	@$(PYTHON) eval.py $(AR_EVAL_ARGS)

test:            ## score solution.py on the held-out test split (experimenters only)
	@$(PYTHON) eval.py $(AR_EVAL_ARGS) --data data/test.jsonl

exp:             ## one experiment: eval + uniform row in results.tsv. Usage: make exp DESC="..."
	@$(PYTHON) tools/log_experiment.py "$(DESC)"

baselines:       ## score all baselines on train and test -> baselines/RESULTS.md
	@FMR_REPO=$(FMR_REPO) $(PYTHON) tools/run_baselines.py

freeze:
	@mkdir -p runs && shasum -a 256 data/train.jsonl data/test.jsonl eval.py SCHEMA.md > runs/inputs.sha256 && cat runs/inputs.sha256

plot:
	@$(PYTHON) ../tools/plot.py

archive:
	@mkdir -p runs && cp results.tsv runs/$(AGENT)-$$(date +%y%m%d-%H%M).tsv
