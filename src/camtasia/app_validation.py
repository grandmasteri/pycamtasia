"""Launch Camtasia and check for exceptions — integration test harness."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import tempfile
import time

CAMTASIA_PATH = Path('/Applications/Camtasia.app/Contents/MacOS/Camtasia')

_EXCEPTION_RE = re.compile(r'EXCEPTION|Abort')


@dataclass
class CamtasiaValidationResult:
    """Result of a Camtasia project validation run."""

    success: bool
    exception_count: int
    log_output: str
    project_path: Path


def camtasia_validate(
    project_path: Path | str,
    timeout_seconds: int = 15,
    camtasia_path: Path | str = CAMTASIA_PATH,
) -> CamtasiaValidationResult:
    """Launch Camtasia, open a project, and check for exceptions.

    Returns a CamtasiaValidationResult with success=True if zero exceptions.
    """
    project_path = Path(project_path)
    camtasia_path = Path(camtasia_path)

    # 1. Kill any running Camtasia instances
    subprocess.run(['pkill', '-f', 'Camtasia'], stderr=subprocess.DEVNULL)
    time.sleep(2)

    # 2. Remove auto-save file if present
    autosave = project_path.parent / f'~{project_path.name}'
    if autosave.exists():
        autosave.unlink()

    # 3. Launch Camtasia with stderr captured to a temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as log_file:
        log_path = Path(log_file.name)

    try:
        with open(log_path, 'w') as stderr_file:
            proc = subprocess.Popen(
                [str(camtasia_path), str(project_path)],
                stderr=stderr_file,
            )

        # 4. Wait timeout_seconds
        time.sleep(timeout_seconds)

        # 5. Terminate the process (matching integration_helpers pattern)
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

        # 6. Read log and count exceptions
        log_output = log_path.read_text()
        exception_count = len(_EXCEPTION_RE.findall(log_output))

        # 7. Kill any remaining Camtasia instances (belt-and-suspenders)
        subprocess.run(['pkill', '-f', 'Camtasia'], stderr=subprocess.DEVNULL)
    finally:
        # Clean up temp log file
        log_path.unlink(missing_ok=True)

    # 8. Return result
    return CamtasiaValidationResult(
        success=exception_count == 0,
        exception_count=exception_count,
        log_output=log_output,
        project_path=project_path,
    )
