# The Six Skills

| Skill | Owns | Produces | Runs as |
|---|---|---|---|
| `etabli-orchestrator` | Where the project stands, the workflow, the gates, the bench policy | decisions about what happens next | a human's session |
| `etabli-spec` | Requirements (stage A), then decisions and contracts (stage B) | `specs/prd.md`, decision records, `specs/contracts/` | a human's session |
| `etabli-decompose` | Splitting approved work into epics and independent tasks | `specs/decomposition.md` and `specs/tasks/<id>.md`, validated | a human's session |
| `etabli-status` | Claims and run state, read from git | exit codes and tab-separated rows | `sh`, no model |
| `etabli-implement` | One task into one validated change | a working tree and a handoff report | an unattended bench |
| `etabli-refine` | Reviewing that change, fixing what the review finds, and simplifying it | the same working tree, and a Refinement section in the report | the same bench, a second session on a stronger model |

Only `etabli-orchestrator` is invoked by a human directly. The rest are reached
through it, or through `launch-benches.sh`.

## Refinement, the second session

`etabli-refine` is the second session of every bench. It did not write the
change, it runs on the [tier](../guides/tiers.md) above the task's, and it
works in one pass: review the change against the task's acceptance criteria,
fix what that finds, then simplify the lines the change added without altering
their behaviour, and re-run validation.

Simplifying last means the fixes get tidied too, and no effort goes into
polishing code about to change. A failed refinement never loses the
implementation: the change is published as it was, and the report says so.
`--no-refine` on the launcher skips it.

## Why the spec is one skill

`etabli-spec` covers two stages rather than shipping as two skills: they are
written in one sitting from the same source material, and the design spine is
worthless without approved requirements to hang it on.

## Review is not shipped

Review is deliberately **not** part of Établi: use the harness's own review
capability, or install a review skill alongside Établi and compare it against
the unassisted harness before adopting it.

The orchestrator can suggest a review skill for each pull request; see
[Review the Pull Requests](../guides/review.md).

## The rule behind every skill

A skill must beat what the harness does unassisted on its task, or be free. A
rule stays in Établi only if removing it measurably degrades results. Établi
exists because an earlier skill lost to an unassisted harness by adding
ceremony the model did not need.
