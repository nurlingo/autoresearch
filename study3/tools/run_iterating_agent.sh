#!/usr/bin/env bash
# One measured autoresearch session: a first pass over TASK.md, then continuation
# passes until the time budget is spent.
#
# `claude -p` is a single non-interactive pass -- it works one turn and exits --
# so a budget only gets used if something re-invokes it. `claude -c` resumes the
# previous conversation, and resume state lives under HOME, which is tmpfs inside
# the container and does not survive a second `docker run`. The loop therefore
# has to run *inside* the container, which is what this script assembles.
#
# It exists so nobody has to paste a multi-line quoted shell string into an
# interactive prompt; getting that wrong leaves the terminal sitting at `quote>`.
#
#   ./tools/run_iterating_agent.sh <manifest> [model] [budget-seconds]
#
# Requires CLAUDE_CODE_OAUTH_TOKEN (from `claude setup-token`, a Claude
# subscription) or, if you prefer metered billing, edit CRED below.
set -euo pipefail

MANIFEST=${1:?usage: run_iterating_agent.sh <owner-manifest> [model] [budget-seconds]}
MODEL=${2:-claude-opus-5}
BUDGET=${3:-1800}
IMAGE=${IMAGE:-study3-claude:2.1.267}
CRED=${CRED:-CLAUDE_CODE_OAUTH_TOKEN}
# Overridable so the loop can be exercised without spending model time.
AGENT=${AGENT:-claude}
# Backstops against a pass that returns instantly: a floor on how often the
# loop may call the model, and a hard ceiling on passes.
MIN_PASS_SECONDS=${MIN_PASS_SECONDS:-20}
MAX_PASSES=${MAX_PASSES:-40}
# Study 1's stopping rule: stop after this many consecutive experiments that do
# not improve the score. Counted from score.py's history, not the agent's account.
PLATEAU=${PLATEAU:-15}
HOLDOUT=${HOLDOUT:-100}
STUDY3=$(cd "$(dirname "$0")/.." && pwd)

if [ -z "${!CRED:-}" ]; then
  echo "$CRED is unset. Run 'claude setup-token' and export it." >&2
  exit 2
fi

# Built here rather than pasted: the runtime values ($END, $PASS, $LEFT) stay
# escaped for the container's shell, while $MODEL and $BUDGET are substituted now.
DRIVER=$(cat <<DRIVER
set -u
END=\$(( \$(date +%s) + $BUDGET ))
PASS=0
$AGENT --model $MODEL --permission-mode bypassPermissions -p "\$(cat TASK.md)" || true
# Distinct solution versions scored since train micro F1 last set a new best.
streak() {
  python3 -c '
import json
best, seen, n = -1.0, set(), 0
try:
    rows = [json.loads(l) for l in open(".scores.jsonl") if l.strip()]
except OSError:
    rows = []
for r in rows:
    if r["micro_f1"] > best + 1e-9:
        best, seen, n = r["micro_f1"], {r["solution_sha256"]}, 0
    elif r["solution_sha256"] not in seen:
        seen.add(r["solution_sha256"]); n += 1
print(n)
' 2>/dev/null || echo 0
}
while [ "\$(date +%s)" -lt "\$END" ]; do
  STREAK=\$(streak)
  if [ "\$STREAK" -ge $PLATEAU ]; then
    echo "=== plateau: \$STREAK consecutive scored versions without improvement - stopping ==="
    break
  fi
  PASS=\$(( PASS + 1 ))
  if [ "\$PASS" -gt $MAX_PASSES ]; then
    echo "=== stopping: $MAX_PASSES continuation passes reached ==="
    break
  fi
  LEFT=\$(( (\$END - \$(date +%s) + 59) / 60 ))
  echo "=== continuation pass \$PASS - ~\${LEFT} min left ==="
  STARTED=\$(date +%s)
  $AGENT --model $MODEL --permission-mode bypassPermissions -c -p \
    "About \${LEFT} minutes remain. \${STREAK} consecutive scored versions have not improved train micro F1; the run stops at $PLATEAU. The result that counts is on $HOLDOUT unseen recordings. Make one change you would expect to hold there -- a structural fix or a fact about Arabic orthography, not a rule that separates one or two training recordings -- score it with python3 score.py, and state before and after. If you have no idea left that would generalise, say so and stop." \
    || true
  # Floor every pass, whatever its exit status. A pass that returns immediately
  # -- a refusal, an expired session, a quota message, all of which can exit 0 --
  # would otherwise spin the loop and spend real API calls as fast as it can.
  SPENT=\$(( \$(date +%s) - \$STARTED ))
  if [ "\$SPENT" -lt $MIN_PASS_SECONDS ]; then
    echo "--- pass returned in \${SPENT}s; pausing before the next one ---"
    sleep \$(( $MIN_PASS_SECONDS - \$SPENT ))
  fi
done
echo "=== loop ended after \$PASS continuation passes, streak \$(streak) ==="
DRIVER
)

# The launcher gets headroom over the loop's own budget so a final pass is not
# killed mid-write; if the loop overruns anyway, the launcher still cuts it off.
# A sleeping Mac freezes the agent while the container's wall clock keeps
# counting, so the loop's deadline passes with most of the budget unused -- a
# Fable run lost 1906 of 2928 seconds this way. caffeinate -is holds off idle
# and system sleep for exactly as long as the launcher runs.
# (No array here: an empty "${arr[@]}" is an unbound-variable error under
# set -u in the bash 3.2 macOS ships, and elsewhere caffeinate does not exist.)
KEEP_AWAKE=
if command -v caffeinate >/dev/null 2>&1; then
  KEEP_AWAKE="caffeinate -is"
fi

exec $KEEP_AWAKE python3 "$STUDY3/tools/launch_agent_container.py" \
  --manifest "$MANIFEST" \
  --image "$IMAGE" \
  --env "$CRED" \
  --seconds $(( BUDGET + 180 )) \
  -- sh -c "$DRIVER"
