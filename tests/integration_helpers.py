"""Shared helpers for Camtasia integration tests.

Contract enforced by `open_in_camtasia()`:

    Before save, run project.validate().
    After save, launch Camtasia.
    If Camtasia rejects the file AND validate() was silent,
    the test fails with a detailed diagnosis — this is a LIBRARY bug
    (our validator is incomplete), not a test bug.

This turns every integration test into a discovery mechanism for validator
gaps: every Camtasia rejection that isn't predicted by validate() becomes
an actionable bug.

Also provides cross-process serialization via filelock so integration
tests can safely run under pytest-xdist without Camtasia instances
killing each other.
"""
from __future__ import annotations

import subprocess
import time
import uuid
from pathlib import Path

import filelock
import pytest

from camtasia.project import Project

CAMTASIA_APP = Path('/Applications/Camtasia.app')
CAMTASIA_BIN = CAMTASIA_APP / 'Contents/MacOS/Camtasia'

# Serialize Camtasia-launching tests across xdist workers.
# Camtasia is single-instance on macOS; running multiple copies via
# subprocess + pkill leads to flaky tests. filelock guarantees
# one-at-a-time without forcing everything else to run serially.
_CAMTASIA_LOCK = Path('/tmp/pycamtasia_integration.lock')


def _launch_and_scan(project_path: str, timeout: int = 15) -> tuple[int, str]:
    """Launch Camtasia with a project, count EXCEPTION lines in stderr.

    Returns (exception_count, stderr_text). The stderr_text is captured
    so callers can include it in failure messages for diagnosis.
    """
    subprocess.run(['pkill', '-9', '-f', 'Camtasia'], capture_output=True)
    time.sleep(3)

    lock = Path(project_path) / '~project.tscproj'
    lock.unlink(missing_ok=True)

    log = Path(f'/tmp/cam_test_{uuid.uuid4().hex[:8]}.log')
    with log.open('w') as log_fh:
        proc = subprocess.Popen(
            [str(CAMTASIA_BIN), project_path],
            stderr=log_fh,
            stdout=subprocess.DEVNULL,
        )
    time.sleep(timeout)
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()

    text = log.read_text() if log.exists() else ''
    count = text.count('EXCEPTION')
    log.unlink(missing_ok=True)
    return count, text


def open_in_camtasia(project: Project, *, timeout: int = 15) -> None:
    """Save project, open in Camtasia, enforce validator-contract.

    The contract:

    * project.validate() is called BEFORE save
    * Camtasia is launched AFTER save
    * If Camtasia rejects the file AND validate() returned no issues,
      the assertion error identifies this as a VALIDATOR GAP — a library
      bug — and surfaces Camtasia's stderr for diagnosis

    This transforms every integration test into a test of both:
    1. Round-trip correctness (Camtasia accepts our output)
    2. Validator completeness (our validate() catches everything
       Camtasia would reject)

    Args:
        project: A loaded Project ready to save
        timeout: Seconds to wait for Camtasia to finish parsing (default 15)

    Raises:
        AssertionError: If Camtasia reports any EXCEPTION lines, with a
            detailed message distinguishing validator gaps from other
            failures.
    """
    pre_save_issues = list(project.validate())
    project.save()

    with filelock.FileLock(str(_CAMTASIA_LOCK), timeout=300):
        count, stderr = _launch_and_scan(str(project.file_path), timeout=timeout)

    if count == 0:
        return  # test passes

    # Camtasia rejected the file. Diagnose why.
    issues_summary = '\n'.join(
        f'  - [{iss.level}] {iss.message}' + (f' (id={iss.source_id})' if iss.source_id else '')
        for iss in pre_save_issues
    ) or '  (none — validator was silent)'

    # Find EXCEPTION lines + 2 lines of context
    exception_lines = []
    lines = stderr.splitlines()
    for i, line in enumerate(lines):
        if 'EXCEPTION' in line:
            start = max(0, i - 1)
            end = min(len(lines), i + 3)
            exception_lines.append('\n'.join(lines[start:end]))
    exception_snippet = '\n---\n'.join(exception_lines[:3])  # cap at 3

    if not pre_save_issues:
        # VALIDATOR GAP: Camtasia rejected but validate() was silent.
        # This is a library bug.
        raise AssertionError(
            f'VALIDATOR GAP: Camtasia rejected the project with {count} '
            f'exception(s), but project.validate() returned NO issues '
            f'before save.\n\n'
            f'This is a pycamtasia bug: validate() should have caught this '
            f'before we generated a file Camtasia cannot open. File a '
            f'validator-gap entry under "### Validation" in ROADMAP.md.\n\n'
            f'Project path: {project.file_path}\n'
            f'Camtasia stderr excerpt:\n{exception_snippet}'
        )

    # validate() did flag issues but we saved anyway and Camtasia rejected.
    # Tests should normally NOT save projects with validation errors; this
    # path catches the case where validation flagged it but the test
    # ignored the warning.
    raise AssertionError(
        f'Camtasia rejected the project with {count} exception(s), and '
        f'validate() DID flag issues beforehand:\n{issues_summary}\n\n'
        f'If these validation issues are the true cause, the test should '
        f'not be saving/opening a project with known validation errors. '
        f'If Camtasia is complaining about something ELSE, file a '
        f'validator-gap entry.\n\n'
        f'Project path: {project.file_path}\n'
        f'Camtasia stderr excerpt:\n{exception_snippet}'
    )


# Keep the old helper available for tests that deliberately do NOT want
# the validator-contract check (rare — typically only when testing the
# validator itself).
def launch_in_camtasia_raw(project_path: str, *, timeout: int = 15) -> int:
    """Launch Camtasia, return EXCEPTION count. No validator contract.

    Use open_in_camtasia() for normal tests. Use this only when you
    deliberately want to skip the validator contract (e.g., tests that
    assert the validator does NOT flag a particular false positive).
    """
    with filelock.FileLock(str(_CAMTASIA_LOCK), timeout=300):
        count, _stderr = _launch_and_scan(project_path, timeout=timeout)
    return count


# Shared pytest markers + skip conditions for integration tests.
# Import and use as: pytestmark = INTEGRATION_MARKERS
INTEGRATION_MARKERS = [
    pytest.mark.skipif(not CAMTASIA_APP.exists(), reason='Camtasia not installed'),
    pytest.mark.integration,
    pytest.mark.timeout(60),
]
