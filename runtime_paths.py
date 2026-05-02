"""Runtime path setup for QArm Mini demos."""

import os
from pathlib import Path
import sys


def add_quanser_libraries() -> Path:
    """Add Quanser Python libraries when a local path is available."""
    current_path = Path(__file__).resolve()
    library_path = None

    env_path = os.environ.get("QUANSER_PYTHON_PATH")
    if env_path:
        library_path = Path(env_path)

    if library_path is None:
        for parent in current_path.parents:
            candidate = parent / "0_libraries" / "python"
            if candidate.exists():
                library_path = candidate
                break

    if library_path is None:
        library_path = current_path.parents[1] / "0_libraries" / "python"

    if library_path.exists():
        library_str = str(library_path)
        if library_str not in sys.path:
            sys.path.insert(0, library_str)
    return library_path


QUANSER_LIBRARY_PATH = add_quanser_libraries()
