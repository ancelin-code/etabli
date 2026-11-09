<p align="center">
  <img src="docs/assets/logo.svg" alt="Établi logo: a workbench" width="120">
</p>

<h1 align="center">Établi</h1>

<p align="center">
  <a href="https://github.com/ancelin-code/etabli/releases/latest"><img alt="Release" src="https://img.shields.io/github/v/release/ancelin-code/etabli"></a>
  <a href="https://github.com/ancelin-code/etabli/actions/workflows/ci.yaml"><img alt="CI" src="https://github.com/ancelin-code/etabli/actions/workflows/ci.yaml/badge.svg?branch=develop"></a>
  <a href="https://ancelin-code.github.io/etabli/"><img alt="Docs" src="https://github.com/ancelin-code/etabli/actions/workflows/docs.yaml/badge.svg?branch=develop"></a>
  <a href="LICENSE"><img alt="License: Apache-2.0" src="https://img.shields.io/github/license/ancelin-code/etabli"></a>
  <img alt="Harnesses: Claude Code, Copilot CLI, Codex CLI, OpenCode, Pi" src="https://img.shields.io/badge/harnesses-5-informational">
</p>

**Craft software with AI agents, from spec to pull request.** *Établi* is French for
*workbench*.

Give an agent a project the way a craftsperson takes a commission: first the
specification, then the cut into tasks, then one bench per task, each ending as
a draft pull request you review. Établi is a family of Agent Skills that takes a
project from an intent to merged pull requests. A person approves every phase
before the workflow goes on, and git is the only state: no server, no database,
no status file.

**Documentation: [ancelin-code.github.io/etabli](https://ancelin-code.github.io/etabli/)**

> **Status: early.** Établi is used on real projects. Conventions may still
> change between versions: install a release tag, read
> [CHANGELOG.md](CHANGELOG.md) before updating, and expect breaking changes to
> be called out there rather than migrated.

## Principles

- **Git is the only state.** Claims are create-only pushes, status is derived
  from refs and pull requests, and nothing else is stored.
- **Specs are plain files.** Requirements, contracts, decisions and tasks live
  in `specs/`, in your repository, readable and reviewable.
- **A person approves each phase.** The workflow stops at every gate, so no
  session has to stay alive across one.
- **One bench per task.** Each task gets its own worktree and branch, and up to
  three benches run at once, because three is what one person can review.
- **Tiers, not model names.** A task says how much capability it needs; your
  own mapping says which model that means. No single vendor's licence is
  required.
- **A rule earns its tokens.** A skill must beat an unassisted harness on its
  task, or be free. Deterministic steps are POSIX `sh`, not prose.

## Quickstart

Each machine needs `git`, a POSIX `sh`, and an authenticated `gh` 2.0 or later.
In the repository that holds the project's plan:

```sh
npx skills add https://github.com/ancelin-code/etabli/tree/v0.1.0 --skill '*' -y
sh .agents/skills/etabli-orchestrator/scripts/install-routing.sh
```

Commit what that produced, then tell the orchestrator what you want built:

```text
/etabli-orchestrator <what to build>
```

It writes the requirements, then the tasks, and stops at each for your
approval; then benches build the tasks and open draft pull requests. The six
skills are one workflow, not a catalogue: install them together.

Then follow the documentation:

- [Install Établi](https://ancelin-code.github.io/etabli/start/install/):
  the skills, the routing block and the tools each machine needs.
- [Drive the Workflow](https://ancelin-code.github.io/etabli/start/workflow/):
  ask for what you want built and approve each phase.
- [Benches](https://ancelin-code.github.io/etabli/concepts/benches/): what a
  bench does and how to watch or resume one.

## Contributing

`mise run dev` sets up the local environment and git hooks, `mise run lint` and
`mise run test` run the checks CI runs, and `mise run docs:serve` previews the
documentation site. Read [AGENTS.md](AGENTS.md) first: it holds the rules every
change is checked against, and the branch and pull request conventions.

## Project documents

- [Agent instructions](AGENTS.md): the rule that governs Établi, and how to
  change it.
- [Changelog](CHANGELOG.md): what each release changed, and how to migrate.
- [Decision records](docs/decisions/): the choices whose reasons are not
  recoverable from the code.
- [Harness validation](docs/harness-validation.md): which harness assumptions
  were tested, against which CLI versions, and what to re-check after an
  upgrade.

## Licence

[Apache-2.0](LICENSE).
