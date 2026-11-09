# Watch and Resume Benches

!!! info "This page is for debugging"

    In practice the orchestrator watches the benches for you. The follow loop
    reads their state as pull requests are published and merged, and the
    orchestrator tells you which one needs you: a pull request to review, a
    failed bench, a stuck set. The commands here show how a bench works, and what
    to reach for when one misbehaves and you want to look yourself; you do not
    need them to run a project.

## Watch a running bench

Benches run detached, one process per task, with no terminal attached. Each
writes everything it does to `.logs/<task-id>.log` in the worktree root, beside
the worktrees and outside every repository, so a log survives the removal of
its worktree (`--log-dir` moves it).

A bench's log prints `REFINE` when its second session starts, `PUBLISHED` with
the pull request URL when it ends well, and `REFINE-FAILED` if the review
session failed and the change was published as the first session left it.

```sh
benches=${ETABLI_WORKTREE_ROOT:-../benches/$(basename "$PWD")}
tail -f "$benches/.logs/a-001.log"       # follow one bench
tail -n 40 "$benches"/.logs/*.log        # where each bench got to
pgrep -af 'tasks/.*\.md'               # which benches are still alive
```

The worktree is the other live view. The commands below name it once, from
the planning repository, wherever the launcher put it:

```sh
home=$PWD
bench=${ETABLI_WORKTREE_ROOT:-../benches/$(basename "$home")}/a-001
git -C "$bench" status                  # what the bench has changed
git -C "$bench" log --oneline           # what it has committed
```

That is usually a faster answer than reading its log.

## Stop a bench

To stop a bench, kill its process, then remove the worktree and the claim:

```sh
pkill -f 'tasks/a-001\.md'          # a bench is known by its task file
git worktree remove --force "$bench"
git push origin --delete task/a-001
```

Deleting the remote branch is what releases the claim. Skip it and the task
stays held by you and nobody else can pick it up.

A bench whose task names a `repo` belongs to that clone, not to the planning
repository: its worktree is registered there, and its claim is on that
repository's origin. Run the last two commands against the clone, for
`repo: shop-iac`:

```sh
git -C ../shop-iac worktree remove --force "$bench"
git -C ../shop-iac push origin --delete task/a-001
```

## Pick a bench back up by hand

You cannot type into a running bench: `-p` sessions have no input attached.
What you can do is resume the conversation once it has finished or stopped, in
the same worktree, with its context intact.

Copilot benches print the command to do it as their last line, so it is already
in the log:

```sh
grep -h 'copilot --resume' "$benches/.logs/a-001.log"
cd "$bench" && copilot --resume=<session-id>
```

Claude benches do not print a session id in text mode, so there is nothing in
the log to resume from. Use `claude --continue` from inside the bench worktree,
which picks up the most recent session for that directory:

```sh
cd "$bench" && claude --continue
```

That is reliable only while the bench is the last session started in that
worktree. When it is not, start a fresh session there and point it at the task
file and the branch:

```sh
cd "$bench" && claude "/etabli-implement $home/specs/tasks/a-001.md"
```

To redo only the review of a change the first session already left in the
worktree, run `/etabli-refine` on the same task file and `--report
.bench-report.md` instead.

Claude Code can also run benches as attachable background sessions
(`claude --bg`, then `claude attach <id>`), which would remove this asymmetry
on the Claude side. The launcher does not use it: Copilot CLI has no
equivalent, the logs come back as raw terminal output, and a background
session waits for input instead of exiting, so a stuck bench would hold its
claim indefinitely.
