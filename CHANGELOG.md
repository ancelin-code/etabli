# Changelog

All notable changes to Établi are recorded here. Établi is installed whole,
so one version covers every skill. Set the date on a release's heading when
tagging it.

## [Unreleased]

### Fixed

- `publish-bench.sh` retries a failed `gh` call after 5 and 15 seconds
  (`ETABLI_GH_RETRY_DELAYS`), and warns about the `ai-assisted` label only when
  the error is about the label. Once the branch is pushed, a lasting failure
  prints `PUBLISH-FAILED` with the error and the command that re-runs it, and
  `follow.sh` reports it as such rather than as `BENCH-FAILED`.

## [0.2.0] - 2026-11-09

### Breaking: Établi's own vocabulary

The names now follow the workbench: a **bench** is where a worker does one
task, and `specs/` holds the specifications of the project. The tagline is now
"Craft software with AI agents, from spec to pull request."

| Before | Now |
| --- | --- |
| `delivery/` (in a project) | `specs/` |
| `DELIVERY_*` variables | `ETABLI_*` (`DELIVERY_LANE_CMD` is `ETABLI_BENCH_CMD`) |
| lane | bench (`launch-benches.sh`, `publish-bench.sh`, `release-bench.sh`, `--max-benches`, `.bench-report.md`, `../benches/<repository>/`) |
| route | workflow |
| the kit | Établi |

To migrate a project, run `git mv delivery specs`, rename any `DELIVERY_*`
variable you export, and delete the old `.lanes/` directory and lane
worktrees. Task branches (`task/<id>`) and claims are unchanged, so work in
flight keeps its claims.

The project moves to Python 3.13, aligned with Tiroir, and the README follows
Tiroir's layout.

- A documentation site, <https://ancelin-code.github.io/etabli/>, built with
  Zensical and published from `develop`. The guides move there from the
  README, which keeps a quickstart.
- The GitHub-only requirement is now stated and recorded
  ([ADR-012](https://github.com/ancelin-code/etabli/blob/main/docs/decisions/ADR-012-github-only.md)):
  the status, snapshot and publishing helpers ask `gh` which pull requests exist.
  A forge-agnostic version is planned.
- Bench session logs are written to `.logs/` in the worktree root, beside the
  bench worktrees (`../benches/<repository>/.logs/` by default), instead of
  `.lanes/logs/` in the checkout. They live outside every repository, so
  nothing needs ignoring and a log survives the removal of its worktree.
  `--log-dir` still overrides it. A project that ran lanes before can delete its
  `.lanes/` directory.
- Milestones are the default of a full workflow: `etabli-decompose` plans them
  before the epics and cuts only the first. Only the user can decide against
  them, recorded as a `**Milestones:** none` line in the summary. The
  validator warns, without failing, when the summary has neither.

## [0.1.0] - 2026-11-04

First public release, under the name Établi (*établi*, French for workbench).

- Six skills that take a project from requirements to draft pull requests:
  `etabli-orchestrator`, `etabli-spec`, `etabli-decompose`,
  `etabli-implement`, `etabli-refine` and `etabli-status`.
- Parallel implementation lanes with claims made by create-only git pushes, so
  git is the only state. A lane's branch pushes to itself: a plain `git push`
  from a lane worktree reaches `task/<id>`, never the default branch.
- Every lane is two sessions: `etabli-implement`, then `etabli-refine`, which
  reviews the change on the tier above, fixes what it finds, simplifies it
  without changing its behaviour, re-validates, and adds a Refinement section to
  the pull request body. A tier can name its own `reviewer` in `tiers.conf`;
  `--no-refine` skips the second session
  ([ADR-011](https://github.com/ancelin-code/etabli/blob/main/docs/decisions/ADR-011-lane-refinement.md)).
- Tasks name a capability `tier` (`plan`, `build` or `chore`) instead of a
  vendor's model. A `tiers.conf` maps a tier to a harness and a model; with
  none, the harness picks its own default. Reasoning effort is left to the
  harness's own settings.
- Milestones: a large project is cut and run one end-to-end slice at a time,
  with a reviewed note closing each before the next is cut. `where.sh` and
  `follow.sh` stop at each boundary
  ([ADR-010](https://github.com/ancelin-code/etabli/blob/main/docs/decisions/ADR-010-milestones.md)).
- Requirement coverage: requirements carry ids, tasks list the ids they cover
  in full or in part, and `coverage.sh` reports what is left of each.
- A status snapshot that external tools can project into their own views,
  including milestones and coverage.
- An install split between `.claude/skills/` and `.agents/skills/`, as
  `npx skills update` can leave, is reported by `where.sh` as
  `NEXT repair-install`, and the lane launcher refuses to start without
  `etabli-implement` or `etabli-refine`. The README explains how to install
  so this cannot happen, and how to repair it.
- The helpers are POSIX `sh`: no bash is required, and they run on dash, macOS's
  own `sh` and BusyBox ([ADR-007](https://github.com/ancelin-code/etabli/blob/main/docs/decisions/ADR-007-posix-sh-helpers.md)).
- Harness adapters for Claude Code, Copilot CLI, Codex, OpenCode and Pi, and a
  `DELIVERY_LANE_CMD` template for any other
  ([ADR-008](https://github.com/ancelin-code/etabli/blob/main/docs/decisions/ADR-008-harness-adapters.md)).
- Multi-repository projects planned once and landed where each change belongs.
- `follow.sh --exit-on-human` ends the loop with exit code 4 when a lane
  publishes or fails, so any harness learns a person is expected from the
  command ending, with no background-output support needed.
- The direct implement path now says `etabli-refine` runs in a separate
  session from `etabli-implement`, so the reviewer did not write the change,
  and `etabli-implement`'s report names it as the next step.
- Licensed under Apache-2.0.
