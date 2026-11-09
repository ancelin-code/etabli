# Établi

**Craft software with AI agents, from spec to pull request.** *Établi* is French for *workbench*.

Établi takes a project from an intent to merged pull requests: requirements
and a design spine, decomposition into tasks, parallel implementation benches,
review. Each phase writes a file the next one reads, and a person approves it
before the workflow goes on. Git is the only state: no server, no database, no
status file.

!!! note "Status: early"

    Établi is used on real projects.
    Conventions may still change between versions. Install a release tag, read
    the [Changelog](changelog.md) before updating, and expect breaking changes
    to be called out there rather than migrated.

## Who it is for

- **Developers** who want an agent to build more than one change at a time,
  without losing track of what was decided and what is in flight.
- **Teams** that share one task set: several people pick tasks from it, and a
  claim made in git says who holds which.
- Anyone on **Claude Code, GitHub Copilot CLI, Codex CLI, OpenCode or Pi**.
  The skills hold no harness-specific tool names, and the bench launcher has an
  adapter for each, plus a custom command for any other.

## What version 0.2.0 does

- Six skills that are one workflow: `etabli-orchestrator` routes every request,
  `etabli-spec` writes requirements and contracts, `etabli-decompose` cuts them
  into tasks, `etabli-status` claims tasks, and each bench runs
  `etabli-implement` then `etabli-refine`. See [The Six Skills](concepts/skills.md).
- Up to three **benches** at once, each in its own git worktree, each ending as a
  draft pull request. See [Benches](concepts/benches.md).
- **Tiers** instead of model names: a task says how much capability it needs,
  and your own mapping says which model that means. See
  [Choose Models with Tiers](guides/tiers.md).
- **Milestones** for a project too large to cut at once, and **requirement
  coverage** that says what is left of each requirement.
- One project planned **across several repositories**, each task landing where
  its change belongs. See [Several Repositories](guides/repositories.md).
- A JSON **snapshot** of the project that connectors copy into tools such as
  Jira. See [Plug a Connector](guides/connectors.md).

## Where to start

1. [Install Établi](start/install.md): add the six skills to a repository and
   make the orchestrator its default assistant.
2. [Drive the Workflow](start/workflow.md): ask for what you want built, approve each
   phase, and let the benches run.
3. [Watch and Resume Benches](start/benches.md): see what a bench is doing, stop it,
   or pick it back up by hand.
4. [The Workflow](concepts/workflow.md): how the phases, the gates and the files fit
   together.

Établi is open source under the Apache-2.0 licence; its code is on
[GitHub](https://github.com/ancelin-code/etabli). Its sibling,
[Tiroir](https://ancelin-code.github.io/tiroir/), was built with it.
