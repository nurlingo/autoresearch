.PHONY: eval eval-json baseline

# Run the fixed scorecard against solution.py.
eval:
	@python3 eval.py

eval-json:
	@python3 eval.py --json

# Run eval, append a row to results.tsv, and echo the score.
# Usage: make baseline DESC="what changed"
baseline:
	@python3 eval.py > run.log 2>&1; \
	score=$$(grep '^research_score:' run.log | awk '{print $$2}'); \
	commit=$$(git rev-parse --short HEAD 2>/dev/null || echo none); \
	printf "%s\t%s\t%s\n" "$$commit" "$$score" "$${DESC:-run}" >> results.tsv; \
	cat run.log; \
	echo "logged: $$commit  $$score  $${DESC:-run}"
