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
while [ "\$(date +%s)" -lt "\$END" ]; do
  PASS=\$(( PASS + 1 ))
  if [ "\$PASS" -gt $MAX_PASSES ]; then
    echo "=== stopping: $MAX_PASSES continuation passes reached ==="
    break
  fi
  LEFT=\$(( (\$END - \$(date +%s) + 59) / 60 ))
  echo "=== continuation pass \$PASS - ~\${LEFT} min left ==="
  STARTED=\$(date +%s)
  $AGENT --model $MODEL --permission-mode bypassPermissions -c -p \
    "About \${LEFT} minutes remain and you must keep working until they are gone. Run python3 score.py, identify the weakest label, make one targeted change, re-score, and keep it only if micro F1 improved -- revert it otherwise. State the before and after numbers for every change. Do not stop early." \
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
echo "=== budget spent after \$PASS continuation passes ==="
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
