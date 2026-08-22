#!/usr/bin/env bash
# Mechanically count "hardcoded ayah ids" in each run's final solution.
#
# A verse id in this corpus is a six-digit string ("095001"), so the measure
# reduces to counting DISTINCT six-digit string literals in the final
# solution.py. No human judgment, no exclusion list: the muqatta'at table
# holds Arabic letter names, not ids, so it never enters the count.
#
# Reproduces the "Hardcoded ids" and "LOC" columns of Table 1 exactly.
#
#   tools/count_hardcoded_ids.sh              # all Study 1 finals, from tags
#   tools/count_hardcoded_ids.sh path/to/solution.py ...   # arbitrary files
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

ID_RE="[\"'][0-9]{6}[\"']"

count() {  # name, source-text
    local name="$1" src="$2"
    printf '%-34s LOC=%-5s ids=%s\n' "$name" \
        "$(printf '%s\n' "$src" | wc -l | tr -d ' ')" \
        "$(printf '%s\n' "$src" | grep -oE "$ID_RE" | sort -u | wc -l | tr -d ' ')"
}

if [ "$#" -gt 0 ]; then
    for f in "$@"; do count "$f" "$(cat "$f")"; done
    exit 0
fi

# Study 1 final artifacts, addressed by the tags published with this repo.
for tag in runs/ar-260630-claude-r1 runs/ar-260630-claude-r2 \
           runs/ar-260630-claude-r3 runs/codex-r1-run \
           runs/codex-r2-run runs/codex-r3-run; do
    if src="$(git -C "$ROOT" cat-file -p "$tag:solution.py" 2>/dev/null)"; then
        count "$tag" "$src"
    else
        printf '%-34s MISSING (fetch tags: git fetch --tags)\n' "$tag"
    fi
done
