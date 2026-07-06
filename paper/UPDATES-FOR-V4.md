# Updates for paper v4 (from the experiments after the v3 PDF)

Everything below is committed in this repo; file pointers included so you can
verify numbers. Three new results + a set of fixes to v3.

## 1. NEW RESULT — incumbent baseline (the applied headline)

We wrapped the hand-built production pipeline (`AyahDetector` + alignment
segmenter from the app repo, iterated over months, historically tuned on a
22-case set overlapping ~20 of these recordings) in the same eval contract:
`tools/incumbent_baseline.py`.

| | held-out test (107) | full v1.1 (258) |
|---|---:|---:|
| incumbent | **0.760** (det 82.9%, split 91.1%, abstain 1/2) | 0.785 |
| agent winner (codex-r3) | **0.079** (det 94.3%, split 97.8%, abstain 2/2) | 0.034 |

Every agent arm's held-out core matched or beat the incumbent (even Cursor's
underfit ~0.27 ≈ incumbent's 0.26 det+split); the winner is ~10× better. The
comparison *favors* the incumbent (it saw ~20 of the rows historically).

**Insert:** §6.1 short paragraph + one sentence in abstract & conclusion
("one-hour unattended loops outperformed months of incremental hand
engineering on the deployed task").
**Fix §9:** "We include no human-researcher or classical-pipeline baseline
arm" is now half-false → keep only the human-researcher part.

## 2. NEW RESULT — the ensemble §8.1 recommends actually fails

v3 §8.1 claims Codex's aligner + Claude's abstention margin "would dominate
either arm alone." We built and measured it (scratch rigs; summary in
RESULTS.md "Incumbent baseline" + production/README.md):

| candidate | held-out test |
|---|---:|
| codex-r3 alone | 0.0793 |
| claude-r1 alone | 0.0796 |
| union abstention (either abstains) | **0.0983** — worse: Claude's gate false-abstains rows Codex gets right |
| claude-on-detection-disagreement | 0.0790 — +0.0003, noise, 2× maintenance |

**Replace the §8.1 sentence** with the tested outcome — suggested text:
"We tested the obvious composition (Codex's aligner gated by Claude's
abstention): the union gate degrades held-out score to 0.098 through false
abstentions, and a disagreement-router improves it by only 0.0003. The shipped
artifact is therefore the single best file, selected on held-out evidence —
the simplicity criterion applies to the experimenters too."
(Frame as deployment engineering, not a preregistered result — the selection
is test-informed.)

## 3. NEW RESULT — deployed to production

The winner is live in the app: `production/solution.py` (this repo) ported
verbatim into the worker (`backend/worker/services/autoresearch_solution.py`
in the app repo), behind an env flag with automatic legacy fallback, plus a
CI regression gate (behavioral smokes + full-dataset detection/abstention
thresholds). One sentence for the conclusion: the loop's artifact was not
only measured but *shipped*, replacing the incumbent it beat.
(For double-blind: phrase as "deployed in the production application"; no
repo names.)

## 4. Fixes to v3

- p.6 typo: "Mamn–Whitney" → "Mann–Whitney".
- Page budget: v3 is at the 15-page cap; items 1–3 need ~½ page — Appendix A
  has slack, and §2's third paragraph can compress.
- Fig. 1 legends illegible at print size — export at higher DPI or vector.
- Title (Nursultan's proposal, pending group agreement):
  *"Autoresearch with Coding Agents: Generalizers, Metric-Maximizers, and
  Abstention on Qur'an Recitation Data"* — note it drops "Karpathy loop"
  (stays as the intro's first citation) and should match the paper's
  "Qur'an" spelling.

## 5. Numbers provenance

- Incumbent + composition: RESULTS.md (bottom sections), tools/incumbent_baseline.py.
- Winner selection rationale: production/README.md.
- All run logs / holdout scores / bundles: runs/.
- Dataset v1.1 (post-study At-Tin fix, agent-flagged): METHODOLOGY.md §12 note.

Please push the LaTeX source to paper/latex/ on this branch so edits stay in
sync — right now the .tex only exists on your machine.
