"""Behavioural tests for the bench release.

``release-bench.sh`` deletes a claim on the shared remote, so the tests are mostly
about the claims it must leave alone: a bench with work in it, and a branch that
is no longer this bench's claim.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from tests.conftest import SH
from tests.unit.test_publish_bench_script import claimed_bench, git

SKILLS = Path(__file__).resolve().parents[2] / ".agents" / "skills"
SCRIPT = SKILLS / "etabli-orchestrator" / "scripts" / "release-bench.sh"

RELEASED = 0
USAGE_ERROR = 1
KEPT = 3

pytestmark = pytest.mark.skipif(
    shutil.which("git") is None,
    reason="git is required",
)


def release(bench: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [SH, str(SCRIPT), "specs/tasks/a-001.md"],
        cwd=bench,
        capture_output=True,
        text=True,
        check=False,
    )


def remote_has_claim(tmp_path: Path) -> bool:
    refs = git(tmp_path / "origin.git", "for-each-ref", "--format=%(refname)", "refs/heads/task/").stdout
    return "refs/heads/task/a-001" in refs


class TestRelease:
    def test_an_untouched_bench_gives_its_task_back(self, tmp_path: Path) -> None:
        """A session that died at startup must not hold the task until someone notices."""
        # Given a claimed bench where nothing was done
        bench = claimed_bench(tmp_path)

        # When it is released
        result = release(bench)

        # Then the claim is gone from the remote
        assert result.returncode == RELEASED, result.stderr
        assert result.stdout == "RELEASED\ta-001\n"
        assert not remote_has_claim(tmp_path)

    def test_removes_the_worktree_and_local_branch(self, tmp_path: Path) -> None:
        """Otherwise the next launch finds the path taken and skips the task."""
        # Given a claimed bench where nothing was done
        bench = claimed_bench(tmp_path)

        # When it is released
        release(bench)

        # Then its worktree and local branch are gone too
        assert not bench.exists()
        assert "task/a-001" not in git(tmp_path / "dev", "branch", "--list").stdout

    def test_keeps_a_bench_with_uncommitted_work(self, tmp_path: Path) -> None:
        # Given a bench with an uncommitted file
        bench = claimed_bench(tmp_path)
        (bench / "widget.py").write_text("print('half done')\n", encoding="utf-8")

        # When it is released
        result = release(bench)

        # Then the claim and the work are kept
        assert result.returncode == KEPT
        assert "has changes" in result.stdout
        assert remote_has_claim(tmp_path)
        assert (bench / "widget.py").exists()

    def test_keeps_a_bench_that_committed(self, tmp_path: Path) -> None:
        # Given a bench that committed past its claim
        bench = claimed_bench(tmp_path)
        (bench / "widget.py").write_text("print('widget')\n", encoding="utf-8")
        git(bench, "add", "widget.py")
        git(bench, "commit", "-q", "-m", "feat(a): add the widget")

        # When it is released
        result = release(bench)

        # Then the claim is kept
        assert result.returncode == KEPT
        assert "commits past the claim" in result.stdout
        assert remote_has_claim(tmp_path)

    def test_never_deletes_a_branch_that_moved_on(self, tmp_path: Path) -> None:
        """The remote is the truth: someone may have pushed to the task since."""
        # Given someone else pushed to the task branch since the claim
        bench = claimed_bench(tmp_path)
        other = tmp_path / "other"
        subprocess.run(["git", "clone", "-q", str(tmp_path / "origin.git"), str(other)], check=True)  # noqa: S603, S607
        git(other, "config", "user.email", "o@example.com")
        git(other, "config", "user.name", "other")
        git(other, "checkout", "-q", "task/a-001")
        git(other, "commit", "-q", "--allow-empty", "-m", "feat(a): someone else's work")
        git(other, "push", "-q", "origin", "task/a-001")

        # When the bench is released
        result = release(bench)

        # Then the remote branch is left alone
        assert result.returncode == KEPT
        assert "no longer this claim" in result.stdout
        assert remote_has_claim(tmp_path)

    def test_refuses_to_run_off_the_task_branch(self, tmp_path: Path) -> None:
        # Given a bench switched to another branch
        bench = claimed_bench(tmp_path)
        git(bench, "checkout", "-q", "-b", "elsewhere")

        # When it is released
        result = release(bench)

        # Then it refuses, and the claim stays
        assert result.returncode == USAGE_ERROR
        assert remote_has_claim(tmp_path)
