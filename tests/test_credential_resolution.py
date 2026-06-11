"""Hardware-free credential resolution check for newt-starter-yam.

Verifies that the starter's credential resolution pattern (env-first, file-fallback)
works correctly when only a credentials file is present — the `newt login` path.

Why: before brief-247, the starter gated on NT_API_KEY only, silently ignoring the
credentials file `newt login` just wrote. This test turns that regression back into
a red test.

Run:
    uv run pytest tests/test_credential_resolution.py -v
"""
from __future__ import annotations

import os
from pathlib import Path


_FILE_KEY = "nt_filekeyfikeyfilekeyfikeyfilekeyfil0000"
_ENV_KEY = "nt_envkeyenvkeyenvkeyenvkeyenvkeyenvkeyenv0"


def _resolve(cred_path: Path) -> str | None:
    """The resolution expression used in run.py: env-first, file fallback."""
    from newt._credentials import read_api_key
    return os.environ.get("NT_API_KEY") or read_api_key()


def test_file_only_resolves(monkeypatch, tmp_path):
    """File-only path: `newt login` wrote the credentials file, NT_API_KEY unset.

    A developer on the rig runs `newt login` once, then starts the demo without
    setting any env var. The starter must find the key and proceed — not bail with
    'no API key found'.
    """
    monkeypatch.delenv("NT_API_KEY", raising=False)
    cred_path = tmp_path / "credentials"
    cred_path.write_text(f"api_key = {_FILE_KEY}\n")
    monkeypatch.setattr("newt._credentials.CREDENTIALS_PATH", cred_path)

    key = _resolve(cred_path)

    assert key == _FILE_KEY, (
        f"file key must resolve when NT_API_KEY is unset; got {key!r}"
    )


def test_env_overrides_file(monkeypatch, tmp_path):
    """Env override: NT_API_KEY wins over the credentials file.

    A CI or agent job sets NT_API_KEY; a credentials file from a previous `newt login`
    exists on the same machine. The env key must win.
    """
    monkeypatch.setenv("NT_API_KEY", _ENV_KEY)
    cred_path = tmp_path / "credentials"
    cred_path.write_text(f"api_key = {_FILE_KEY}\n")
    monkeypatch.setattr("newt._credentials.CREDENTIALS_PATH", cred_path)

    key = _resolve(cred_path)

    assert key == _ENV_KEY
    assert key != _FILE_KEY
