"""Runtime path setup for running demos from the repository checkout."""

from pathlib import Path
import sys


def add_quanser_libraries() -> Path:
    """Add the repository's local Quanser Python libraries to sys.path."""
    current_path = Path(__file__).resolve()
    library_path = None

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
