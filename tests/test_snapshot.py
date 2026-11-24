import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import snapshot  # noqa: E402


def scratch_dir(test: unittest.TestCase) -> Path:
    base = ROOT / "tmp" / "scratch" / "tests"
    base.mkdir(parents=True, exist_ok=True)
    path = Path(tempfile.mkdtemp(dir=base))
    test.addCleanup(shutil.rmtree, path, True)
    return path


def git(project: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=project, capture_output=True, text=True, check=True).stdout


class SnapshotTest(unittest.TestCase):
    def repo(self) -> Path:
        project = scratch_dir(self)
        git(project, "init", "-q")
        git(project, "config", "user.email", "t@example.com")
        git(project, "config", "user.name", "t")
        for name in ("kept.txt", "changed.txt", "deleted.txt", "staged.txt"):
            (project / name).write_text(name, encoding="utf-8")
        git(project, "add", "-A")
        git(project, "commit", "-q", "-m", "base")
        return project

    def test_snapshot_holds_the_working_tree_and_leaves_the_index_alone(self):
        project = self.repo()
        (project / "changed.txt").write_text("changed", encoding="utf-8")
        (project / "deleted.txt").unlink()
        (project / "staged.txt").write_text("staged", encoding="utf-8")
        git(project, "add", "staged.txt")
        (project / "new.txt").write_text("new", encoding="utf-8")
        status_before = git(project, "status", "--porcelain")

        commit = snapshot.snapshot(project)

        files = set(git(project, "ls-tree", "-r", "--name-only", commit).split())
        self.assertEqual(files, {"kept.txt", "changed.txt", "staged.txt", "new.txt"})
        self.assertEqual(git(project, "show", f"{commit}:changed.txt"), "changed")
        self.assertEqual(git(project, "status", "--porcelain"), status_before)
        self.assertEqual(git(project, "rev-parse", f"{commit}^"), git(project, "rev-parse", "HEAD"))

    def test_snapshot_without_commits(self):
        project = scratch_dir(self)
        git(project, "init", "-q")
        (project / "a.txt").write_text("a", encoding="utf-8")
        commit = snapshot.snapshot(project)
        self.assertEqual(git(project, "ls-tree", "-r", "--name-only", commit).split(), ["a.txt"])


if __name__ == "__main__":
    unittest.main()
