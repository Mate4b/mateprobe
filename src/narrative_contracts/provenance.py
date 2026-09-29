"""Opt-in provenance metadata for validator audits.

Provenance is descriptive metadata.  In particular, an observed commit is a
snapshot of the repository at observation time; it does not prove where a
callable was imported from or originated.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

_Commit = str | None
_Source = Literal["observed", "supplied"]
_FULL_SHA = re.compile(r"^(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})$")


@dataclass(frozen=True)
class GitProvenance:
    """A caller-supplied or explicitly observed repository snapshot.

    ``None`` for ``commit`` or ``dirty`` means unknown.  Unknown cleanliness
    is intentional: failure to inspect a repository must never be reported as
    a clean working tree.
    """

    commit: _Commit
    dirty: bool | None
    source: _Source
    error: str | None = None

    def __post_init__(self) -> None:
        if self.commit is not None:
            if not isinstance(self.commit, str) or not _FULL_SHA.fullmatch(self.commit):
                raise ValueError("commit must be a full 40- or 64-character hexadecimal SHA")
        if self.dirty is not None and type(self.dirty) is not bool:
            raise TypeError("dirty must be bool or None")
        if self.source not in ("observed", "supplied"):
            raise ValueError("source must be 'observed' or 'supplied'")
        if self.error is not None and (not isinstance(self.error, str) or not self.error):
            raise ValueError("error must be a nonempty string or None")


def supplied_git_provenance(commit: str | None, dirty: bool | None = None) -> GitProvenance:
    """Create unverified metadata supplied by the caller."""

    return GitProvenance(commit=commit, dirty=dirty, source="supplied")


def _failure(reason: str) -> GitProvenance:
    # Keep failures categorical and concise.  In particular, do not expose
    # subprocess stderr, which can contain arbitrary paths or environment data.
    return GitProvenance(commit=None, dirty=None, source="observed", error=reason)


def _head(path: str) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
        timeout=5.0,
    )
    commit = result.stdout.strip()
    if not _FULL_SHA.fullmatch(commit):
        raise ValueError("invalid_commit")
    return commit


def observe_git(path: str | Path) -> GitProvenance:
    """Explicitly inspect a repository at *path* using bounded git commands.

    The two HEAD reads bracket the status read.  If HEAD moves during the
    snapshot, all values are marked unknown with ``snapshot_changed``.
    """

    location = str(path)
    try:
        before = _head(location)
        status = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=location,
            check=True,
            capture_output=True,
            text=True,
            timeout=5.0,
        )
        after = _head(location)
    except subprocess.TimeoutExpired:
        return _failure("timeout")
    except FileNotFoundError:
        return _failure("git_unavailable")
    except NotADirectoryError:
        return _failure("not_a_repository")
    except ValueError:
        return _failure("invalid_commit")
    except subprocess.CalledProcessError:
        return _failure("not_a_repository")
    except (OSError, subprocess.SubprocessError):
        return _failure("git_error")

    if before != after:
        return _failure("snapshot_changed")
    return GitProvenance(commit=after, dirty=bool(status.stdout), source="observed")
