# Harnesses

The skills hold no harness-specific tool names, so any harness that reads Agent
Skills can run them. What differs is how the bench launcher starts a session,
and it has an adapter for each of these:

| Harness | Name | Status |
|---|---|---|
| Claude Code | `claude` | Validated |
| GitHub Copilot CLI | `copilot` | Validated |
| Codex CLI | `codex` | Adapter only |
| OpenCode | `opencode` | Adapter only |
| Pi | `pi` | Adapter only |
| Anything else | `custom` | Your command |

*Validated* means a bench ran on the real CLI and the result is recorded in the
[harness validation](https://github.com/ancelin-code/etabli/blob/main/docs/harness-validation.md).
*Adapter only* means the command line follows the harness's documentation and
a test proves the launcher passes it, but nobody has run a real bench there
yet. If you have the license, running the checks and sending the result is the
most useful contribution you can make.

## Safety differs by harness

Claude Code and Copilot CLI deny `terraform apply` and `terraform destroy`;
OpenCode denies them through the permission config the launcher passes; Codex
relies on its sandbox, which writes inside the worktree and has no network.

!!! danger "Pi has no permission system"

    Run Pi benches in a container or a throwaway machine.

`--no-web` is honoured by all five.

## Any other harness

For a harness without an adapter, set `ETABLI_BENCH_CMD` and
`--harness custom` (or `ETABLI_HARNESS=custom`). The template is a shell
command line, run in the bench's worktree, and these placeholders become the
bench's values:

| Placeholder | Value |
|---|---|
| `{prompt}` | What the session is told to do |
| `{model}` | The model the tier maps to, empty when there is none |
| `{worktree}` | The bench's worktree, also the current directory |
| `{plan_dir}` | The checkout that holds the planning files |

```sh
export ETABLI_BENCH_CMD='mycli run --model {model} --dir {worktree} {prompt}'
```

Placeholders are values, never pasted text, so quotes and `$(...)` in a path
or prompt do nothing. The command's exit status decides the rest: zero
publishes a draft pull request, non-zero gives the claim back if the bench left
no work.
