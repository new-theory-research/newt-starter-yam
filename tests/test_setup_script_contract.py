"""The kit ships the one repair command the SDK is allowed to name.

`newt` prints `./scripts/setup` as the single fix-command when a kit's deps fall
out from under it — one literal string, no per-kit hedging. That makes "this kit
ships an executable scripts/setup" a contract, and a contract nothing checks is a
promise until the first person tests it. This file is the check.

Two ways it can break, and the tests are separate because the fixes are:

  * the file goes missing — a developer types the command `newt` handed them and
    the shell says "no such file"
  * the file survives but loses its mode bit — worse, because it looks fine in the
    tree and `./scripts/setup` still fails, and because a mode bit is lost silently
    by a tarball round-trip, a `git add` on a Windows checkout, or a rewrite that
    creates the file fresh

Run:
    uv run pytest tests/test_setup_script_contract.py -v
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent

# The literal path the SDK names. `newt-python` keeps it as KIT_SETUP in
# src/newt/_cli/_source_spec.py and asserts its own two copies stay equal; this
# side of the contract is the file existing at that path. Spelled out rather than
# imported: the SDK pin in pyproject.toml predates that constant, and refreshing
# the pin to import it would tie a kit's own check to whichever SDK is installed.
SETUP_REL = "scripts/setup"


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True
    )


def test_setup_script_exists():
    """`newt`'s fix-command names a file. The file is here.

    A yam developer who hits an import failure is told to run `./scripts/setup`.
    If this goes red, that developer goes looking for a file the tool promised
    them and learns the tool does not know what their kit contains.
    """
    setup = REPO_ROOT / SETUP_REL
    assert setup.is_file(), (
        f"{SETUP_REL} is missing from this kit. `newt` hands developers "
        f"`./{SETUP_REL}` as the one command that repairs a broken install — "
        "delete the file and that message points at nothing."
    )


def test_setup_script_is_executable_on_disk():
    """A checkout of this kit can run the command as printed.

    `./scripts/setup` is copy-pasted verbatim from an error message. Without the
    execute bit that paste dies on "permission denied", which reads to a developer
    as the tool being broken rather than the file being wrong.
    """
    setup = REPO_ROOT / SETUP_REL
    if not setup.exists():
        pytest.fail(
            f"{SETUP_REL} does not exist, so its mode says nothing — the missing "
            "file is the failure, and test_setup_script_exists reports it."
        )
    assert os.access(setup, os.X_OK), (
        f"{SETUP_REL} exists but is not executable in this checkout "
        f"(mode {oct(setup.stat().st_mode & 0o777)}). Fix with `chmod +x {SETUP_REL}` "
        "and commit the mode change."
    )


def test_setup_script_mode_bit_is_committed():
    """The execute bit is in git, not just on this one machine.

    `os.access` above passes on a machine where someone ran `chmod +x` locally and
    never committed it — every *other* clone is then broken while this one looks
    fine. Git stores the bit as the file mode in the index, so that is what gets
    asserted: 100755, not 100644.
    """
    if _git("rev-parse", "--git-dir").returncode != 0:
        pytest.skip(
            f"{REPO_ROOT} is not a git checkout, so the committed mode bit cannot "
            "be read here. The on-disk executable check above still ran."
        )

    result = _git("ls-files", "-s", SETUP_REL)
    assert result.returncode == 0, f"git ls-files failed: {result.stderr.strip()}"
    assert result.stdout.strip(), (
        f"{SETUP_REL} is not tracked by git. It exists on this machine only — a "
        "fresh clone would not get it."
    )

    mode = result.stdout.split()[0]
    assert mode == "100755", (
        f"{SETUP_REL} is committed with mode {mode}, not 100755. Every fresh clone "
        f"gets a non-executable file at the path `newt` tells developers to run. "
        f"Fix with `chmod +x {SETUP_REL} && git add {SETUP_REL}`."
    )
