"""Behavioural tests for the bench publisher.

``publish-bench.sh`` is the step between an unattended bench and the pull request
a human reviews, so the tests drive it the way the launcher does: in a claimed
bench worktree, against a shared bare remote, with ``gh`` stubbed to record what
it was asked to open.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.conftest import SH

SKILLS = Path(__file__).resolve().parents[2] / ".agents" / "skills"
SCRIPT = SKILLS / "etabli-orchestrator" / "scripts" / "publish-bench.sh"
CLAIM = SKILLS / "etabli-status" / "scripts" / "claim.sh"

OK = 0
USAGE_ERROR = 1
NOTHING = 3
URL = "https://example.test/pr/7"
TRIES = 3  # the first try, then one per ETABLI_GH_RETRY_DELAYS entry

pytestmark = pytest.mark.skipif(
    shutil.which("git") is None,
    reason="git is required",
)

FAKE_GH = """#!/usr/bin/env bash
printf '%s\\n' "$*" >> "$GH_LOG"
case "$1 $2" in
  "pr view")
    [[ -n "${GH_EXISTING:-}" ]] || exit 1
    printf '%s %s\\n' "${GH_EXISTING_STATE:-OPEN}" "$GH_EXISTING" ;;
  "pr create")
    if [[ -n "${GH_NO_LABEL:-}" && " $* " == *" --label "* ]]; then
      printf "could not add label: 'ai-assisted' not found\\n" >&2; exit 1
    fi
    # GH_FAILURES counts the creates that fail as a proxy timeout before one works.
    if [[ -n "${GH_FAILURES:-}" ]]; then
      done_so_far=$(grep -c '^pr create' "$GH_LOG")
      if ((done_so_far <= GH_FAILURES)); then
        printf 'Post "https://api.github.com/graphql": proxyconnect tcp: i/o timeout\\n' >&2; exit 1
      fi
    fi
    while (($# > 0)); do
      [[ "$1" == --body-file ]] && cp "$2" "$GH_BODY"
      shift
    done
    printf 'Creating draft pull request\\n%s\\n' "$GH_URL" ;;
esac
"""


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)  # noqa: S603, S607


def claimed_bench(tmp_path: Path, *, title: str = "Do a-001", task_type: str | None = None) -> Path:
    """A bench worktree on task/a-001 whose claim is already on the shared remote."""
    bare = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)  # noqa: S603, S607
    dev = tmp_path / "dev"
    dev.mkdir()
    git(dev, "init", "-q", "-b", "main")
    git(dev, "config", "user.email", "dev@example.com")
    git(dev, "config", "user.name", "dev")
    tasks = dev / "specs" / "tasks"
    tasks.mkdir(parents=True)
    type_line = "" if task_type is None else f"type: {task_type}\n"
    (tasks / "a-001.md").write_text(
        f"---\nid: a-001\ntitle: {title}\n{type_line}epic: a\ndepends_on: []\ntier: build\n---\n\n"
        "## Context\n\nWhy.\n\n## Acceptance criteria\n\n- the widget renders\n\n## Validation\n\nRun it.\n",
        encoding="utf-8",
    )
    git(dev, "add", "-A")
    git(dev, "commit", "-q", "-m", "init")
    git(dev, "remote", "add", "origin", str(bare))
    git(dev, "push", "-q", "origin", "HEAD:refs/heads/main")
    bench = tmp_path / "benches" / "a-001"
    git(dev, "worktree", "add", "-q", "-b", "task/a-001", str(bench))
    subprocess.run([SH, str(CLAIM), "a-001"], cwd=bench, capture_output=True, check=True)  # noqa: S603
    return bench


def publish(bench: Path, tmp_path: Path, **env_extra: str) -> subprocess.CompletedProcess[str]:
    bin_dir = tmp_path / "fakebin"
    bin_dir.mkdir(exist_ok=True)
    gh = bin_dir / "gh"
    gh.write_text(FAKE_GH, encoding="utf-8")
    gh.chmod(0o755)
    env = os.environ.copy()
    env.update(
        PATH=f"{bin_dir}{os.pathsep}{env['PATH']}",
        GH_LOG=str(tmp_path / "gh.log"),
        GH_BODY=str(tmp_path / "body.md"),
        GH_URL=URL,
        ETABLI_GH_RETRY_DELAYS="0 0",
        **env_extra,
    )
    (tmp_path / "gh.log").touch()
    return subprocess.run(  # noqa: S603
        [SH, str(SCRIPT), "specs/tasks/a-001.md"],
        cwd=bench,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def remote_subject(tmp_path: Path) -> str:
    return git(tmp_path / "origin.git", "log", "-1", "--format=%s", "task/a-001").stdout.strip()


class TestPublishing:
    def test_a_finished_bench_becomes_a_draft_pull_request(self, tmp_path: Path) -> None:
        # Given a claimed bench with an uncommitted change
        bench = claimed_bench(tmp_path)
        (bench / "widget.py").write_text("print('widget')\n", encoding="utf-8")

        # When it is published
        result = publish(bench, tmp_path)

        # Then the change is pushed and a labelled draft pull request opens
        assert result.returncode == OK, result.stderr
        assert result.stdout == f"PUBLISHED\ta-001\t{URL}\n"
        assert remote_subject(tmp_path) == "feat(a): do a-001"
        create = next(line for line in (tmp_path / "gh.log").read_text().splitlines() if line.startswith("pr create"))
        assert "--draft" in create
        assert "--label ai-assisted" in create

    def test_the_body_carries_the_criteria_and_the_report(self, tmp_path: Path) -> None:
        """The reviewer checks the diff against the criteria, and the report says what was run."""
        # Given a bench with a change and a report
        bench = claimed_bench(tmp_path)
        (bench / "widget.py").write_text("print('widget')\n", encoding="utf-8")
        (bench / ".bench-report.md").write_text("Validation run: pytest, 3 passed.\n", encoding="utf-8")

        # When it is published
        publish(bench, tmp_path)

        # Then the body has the criteria and the report, and nothing after the criteria
        body = (tmp_path / "body.md").read_text(encoding="utf-8")
        assert "- the widget renders" in body
        assert "Validation run: pytest, 3 passed." in body
        assert "Run it." not in body, "the section after the criteria leaked into the body"

    def test_the_report_is_never_committed(self, tmp_path: Path) -> None:
        # Given a bench with a change and a report
        bench = claimed_bench(tmp_path)
        (bench / "widget.py").write_text("print('widget')\n", encoding="utf-8")
        (bench / ".bench-report.md").write_text("report\n", encoding="utf-8")

        # When it is published
        publish(bench, tmp_path)

        # Then the change is pushed without the report
        files = git(tmp_path / "origin.git", "ls-tree", "-r", "--name-only", "task/a-001").stdout.split()
        assert "widget.py" in files
        assert ".bench-report.md" not in files

    @pytest.mark.parametrize(
        "template",
        [
            ".github/pull_request_template.md",
            "docs/PULL_REQUEST_TEMPLATE.md",
            ".github/PULL_REQUEST_TEMPLATE/feature.md",
        ],
    )
    def test_a_repository_template_makes_the_report_the_whole_body(self, tmp_path: Path, template: str) -> None:
        """The bench fills the template; wrapping it in Établi's own sections would break it."""
        # Given a repository pull request template, and a report that fills it
        bench = claimed_bench(tmp_path)
        (bench / template).parent.mkdir(parents=True, exist_ok=True)
        (bench / template).write_text("## Summary\n\n## Testing\n", encoding="utf-8")
        (bench / "widget.py").write_text("print('widget')\n", encoding="utf-8")
        filled = "## Summary\n\nAdds the widget. Task: specs/tasks/a-001.md\n\n## Testing\n\npytest\n"
        (bench / ".bench-report.md").write_text(filled, encoding="utf-8")

        # When the bench is published
        publish(bench, tmp_path)

        # Then the body is the report, unwrapped
        assert (tmp_path / "body.md").read_text(encoding="utf-8") == filled

    def test_without_a_report_the_template_does_not_hide_the_criteria(self, tmp_path: Path) -> None:
        # Given a repository template but no report
        bench = claimed_bench(tmp_path)
        (bench / ".github").mkdir()
        (bench / ".github" / "pull_request_template.md").write_text("## Summary\n", encoding="utf-8")
        (bench / "widget.py").write_text("print('widget')\n", encoding="utf-8")

        # When the bench is published
        publish(bench, tmp_path)

        # Then the body still has the criteria and says no report was written
        body = (tmp_path / "body.md").read_text(encoding="utf-8")
        assert "- the widget renders" in body
        assert "wrote no report" in body

    def test_says_when_the_bench_wrote_no_report(self, tmp_path: Path) -> None:
        # Given a bench with a change and no report
        bench = claimed_bench(tmp_path)
        (bench / "widget.py").write_text("print('widget')\n", encoding="utf-8")

        # When it is published
        publish(bench, tmp_path)

        # Then the body says no report was written
        assert "wrote no report" in (tmp_path / "body.md").read_text(encoding="utf-8")

    def test_a_bench_that_left_no_change_publishes_nothing(self, tmp_path: Path) -> None:
        """A bench that stopped on a bad task reverts its attempt; no pull request may open."""
        # Given a bench with a report but no change
        bench = claimed_bench(tmp_path)
        (bench / ".bench-report.md").write_text("Stopped: the task is wrong.\n", encoding="utf-8")

        # When it is published
        result = publish(bench, tmp_path)

        # Then nothing is pushed and gh is never called
        assert result.returncode == NOTHING
        assert result.stdout.startswith("NOTHING\ta-001")
        assert not (tmp_path / "gh.log").read_text(), "gh must not be called"

    def test_publishes_commits_the_bench_made_itself(self, tmp_path: Path) -> None:
        # Given a bench that committed its own change
        bench = claimed_bench(tmp_path)
        (bench / "widget.py").write_text("print('widget')\n", encoding="utf-8")
        git(bench, "add", "widget.py")
        git(bench, "commit", "-q", "-m", "feat(a): add the widget")

        # When it is published
        result = publish(bench, tmp_path)

        # Then that commit is pushed as it is
        assert result.returncode == OK, result.stderr
        assert remote_subject(tmp_path) == "feat(a): add the widget"


class TestCommitSubject:
    def test_uses_the_task_type(self, tmp_path: Path) -> None:
        # Given a fix task
        bench = claimed_bench(tmp_path, title="Stop the loader dropping footnotes", task_type="fix")
        (bench / "loader.py").write_text("x = 1\n", encoding="utf-8")

        # When its bench is published
        publish(bench, tmp_path)

        # Then the subject is a fix with the title in lower case
        assert remote_subject(tmp_path) == "fix(a): stop the loader dropping footnotes"

    def test_leaves_a_leading_acronym_alone(self, tmp_path: Path) -> None:
        # Given a title starting with an acronym
        bench = claimed_bench(tmp_path, title="DITA conrefs resolve")
        (bench / "loader.py").write_text("x = 1\n", encoding="utf-8")

        # When its bench is published
        publish(bench, tmp_path)

        # Then the acronym keeps its case
        assert remote_subject(tmp_path) == "feat(a): DITA conrefs resolve"


class TestPullRequest:
    def test_a_rerun_pushes_without_opening_a_second_pull_request(self, tmp_path: Path) -> None:
        # Given a bench whose pull request is already open
        bench = claimed_bench(tmp_path)
        (bench / "widget.py").write_text("print('widget')\n", encoding="utf-8")

        # When it is published again
        result = publish(bench, tmp_path, GH_EXISTING=URL)

        # Then the open pull request is reported and no other is created
        assert result.stdout == f"PUBLISHED\ta-001\t{URL}\n"
        assert "pr create" not in (tmp_path / "gh.log").read_text()

    def test_a_rerun_opens_a_pull_request_that_is_missing(self, tmp_path: Path) -> None:
        """Re-running is the recovery path, so an already pushed bench must still publish."""
        # Given a bench already pushed but with no pull request
        bench = claimed_bench(tmp_path)
        (bench / "widget.py").write_text("print('widget')\n", encoding="utf-8")
        git(bench, "add", "widget.py")
        git(bench, "commit", "-q", "-m", "feat(a): add the widget")
        git(bench, "push", "-q", "origin", "HEAD:refs/heads/task/a-001")

        # When it is published again
        result = publish(bench, tmp_path)

        # Then the pull request is created
        assert result.stdout == f"PUBLISHED\ta-001\t{URL}\n"
        assert "pr create" in (tmp_path / "gh.log").read_text()

    def test_a_closed_pull_request_is_not_reused(self, tmp_path: Path) -> None:
        """A relaunched task needs a new pull request, not the one that was closed."""
        # Given a bench whose earlier pull request was closed
        bench = claimed_bench(tmp_path)
        (bench / "widget.py").write_text("print('widget')\n", encoding="utf-8")

        # When it is published
        result = publish(bench, tmp_path, GH_EXISTING="https://example.test/pr/2", GH_EXISTING_STATE="CLOSED")

        # Then a new pull request is created
        assert result.stdout == f"PUBLISHED\ta-001\t{URL}\n"
        assert "pr create" in (tmp_path / "gh.log").read_text()

    def test_opens_the_pull_request_without_a_missing_label(self, tmp_path: Path) -> None:
        """The pull request is the point; a repository without the label must not block it."""
        # Given a repository without the ai-assisted label
        bench = claimed_bench(tmp_path)
        (bench / "widget.py").write_text("print('widget')\n", encoding="utf-8")

        # When a bench is published
        result = publish(bench, tmp_path, GH_NO_LABEL="1")

        # Then the pull request opens anyway, with a warning
        assert result.returncode == OK, result.stderr
        assert result.stdout == f"PUBLISHED\ta-001\t{URL}\n"
        assert "ai-assisted label could not be applied: could not add label" in result.stderr

    def test_a_transient_gh_failure_is_retried(self, tmp_path: Path) -> None:
        """A proxy timeout on a finished bench must not lose its pull request, or its label."""
        # Given a gh whose first two creates time out
        bench = claimed_bench(tmp_path)
        (bench / "widget.py").write_text("print('widget')\n", encoding="utf-8")

        # When a bench is published
        result = publish(bench, tmp_path, GH_FAILURES="2")

        # Then the third try opens it, labelled, and no label warning is given
        assert result.returncode == OK, result.stderr
        assert result.stdout == f"PUBLISHED\ta-001\t{URL}\n"
        creates = [line for line in (tmp_path / "gh.log").read_text().splitlines() if line.startswith("pr create")]
        assert len(creates) == TRIES
        assert "--label ai-assisted" in creates[-1]
        assert "label" not in result.stderr

    def test_a_lasting_gh_failure_says_the_work_is_pushed_and_how_to_finish(self, tmp_path: Path) -> None:
        """The bench succeeded; only the pull request is missing, and a re-run opens it."""
        # Given a gh that times out on every create
        bench = claimed_bench(tmp_path)
        (bench / "widget.py").write_text("print('widget')\n", encoding="utf-8")

        # When a bench is published
        result = publish(bench, tmp_path, GH_FAILURES="9")

        # Then the branch is pushed and the line names the error and the re-run
        assert result.returncode == USAGE_ERROR
        assert remote_subject(tmp_path) == "feat(a): do a-001"
        what, task_id, error, rerun = result.stdout.rstrip("\n").split("\t")
        assert (what, task_id) == ("PUBLISH-FAILED", "a-001")
        assert "proxyconnect tcp: i/o timeout" in error
        assert rerun == f"cd '{bench.resolve()}' && sh '{SCRIPT}' --report '.bench-report.md' 'specs/tasks/a-001.md'"
        assert "label" not in result.stderr

    def test_refuses_to_run_off_the_task_branch(self, tmp_path: Path) -> None:
        # Given a bench switched to another branch
        bench = claimed_bench(tmp_path)
        git(bench, "checkout", "-q", "-b", "elsewhere")

        # When it is published
        result = publish(bench, tmp_path)

        # Then it refuses
        assert result.returncode == USAGE_ERROR
        assert "not on task/a-001" in result.stderr
