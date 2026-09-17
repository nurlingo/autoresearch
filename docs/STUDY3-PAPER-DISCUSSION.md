# Study 3 paper changes to discuss

The manuscripts and PDFs remain unchanged. Current data and run readiness are in [CURRENT-STATE.md](../study3/CURRENT-STATE.md).

## Paper changes to discuss

Neither manuscript nor PDF is changed by this audit. An earlier uncommitted wording patch is saved privately for discussion.

1. **Dataset description:** describe the approved and frozen 100-train/100-test dataset, one transcript per recording, human train annotations, multi-location events, summaries, faithful reference and source exclusions. The new freeze contains 200 recordings, 1,038 units and 469 events; no new experiment results exist yet.
2. **Experimental protocol:** train-only development feedback followed by frozen-code test validation. State whether human train labels are exposed directly or used only by a trusted grader; the current plan is the latter. Comparing agents can leave annotation optional and preserve whatever they produce.
3. **Evaluation scope:** decide whether the single-location prediction adapter is sufficient or whether agents must recover the full linked annotation. The evaluator issues are repaired in v2.3; report new numbers only after the new freeze and runs. Distinguish algorithm generalization from agreement on training annotations.
4. **Results:** recompute baselines and run the planned agents on the new freeze. Retain the eight informal pilots under their historical data/evaluator version; do not substitute new counts into old tables.
5. **Wording corrections:** the Track 1 text calls detect/split its companion submission although the current companion proposes event annotation; one sentence says seven pilots where the manuscript describes eight; its blanket no-internet claim is stronger than the later account of uninstrumented Antigravity networking. These can be addressed with the broader revision.
6. **Competition proposal:** final-solution judging need not require autoresearch or iteration scoring. Discuss whether and when to replace its frozen release, baselines and train-only review sample. No submission or anonymous release was changed here.

See [CURRENT-STATE.md](../study3/CURRENT-STATE.md) for readiness and [EXPERIMENT.md](../study3/EXPERIMENT.md) for the active protocol.
