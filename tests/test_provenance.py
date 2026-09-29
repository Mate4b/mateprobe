from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from mateprobe.model import plain
from mateprobe.provenance import GitProvenance, observe_git, supplied_git_provenance

SHA = "a" * 40


def _git(path: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=path, check=True, capture_output=True, text=True)


def _repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.name", "Test User")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    (tmp_path / "tracked.txt").write_text("initial\n")
    _git(tmp_path, "add", "tracked.txt")
    _git(tmp_path, "commit", "-m", "initial")
    return tmp_path


def test_supplied_metadata_is_distinguished_and_plain() -> None:
    value = supplied_git_provenance(SHA, dirty=None)
    assert value == GitProvenance(SHA, None, "supplied")
    assert plain(value) == {
        "commit": SHA,
        "dirty": None,
        "source": "supplied",
        "error": None,
    }


@pytest.mark.parametrize("commit", ["", "a" * 39, "a" * 41, "g" * 40])
def test_commit_must_be_full_sha(commit: str) -> None:
    with pytest.raises(ValueError):
        supplied_git_provenance(commit)


def test_observe_clean_and_dirty_states(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    clean = observe_git(repo)
    assert clean.source == "observed"
    assert len(clean.commit or "") == 40
    assert clean.dirty is False

    (repo / "tracked.txt").write_text("changed\n")
    assert observe_git(repo).dirty is True
    (repo / "untracked.txt").write_text("new\n")
    assert observe_git(repo).dirty is True


def test_observe_nonrepository_is_unknown(tmp_path: Path) -> None:
    result = observe_git(tmp_path)
    assert result == GitProvenance(None, None, "observed", "not_a_repository")


def test_observe_missing_path_is_unknown(tmp_path: Path) -> None:
    result = observe_git(tmp_path / "missing")
    assert result.commit is None and result.dirty is None
    assert result.source == "observed"


def test_observe_git_unavailable_is_unknown(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def missing(*args: object, **kwargs: object) -> None:
        raise FileNotFoundError("git")

    monkeypatch.setattr("mateprobe.provenance.subprocess.run", missing)
    result = observe_git(tmp_path)
    assert result == GitProvenance(None, None, "observed", "git_unavailable")


def test_observe_timeout_is_unknown(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def timeout(*args: object, **kwargs: object) -> None:
        raise subprocess.TimeoutExpired("git", 5.0)

    monkeypatch.setattr("mateprobe.provenance.subprocess.run", timeout)
    result = observe_git(tmp_path)
    assert result == GitProvenance(None, None, "observed", "timeout")
