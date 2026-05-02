"""Runtime path setup for running demos from the repository checkout."""

from pathlib import Path
import sys


def add_quanser_libraries() -> Path:
    """Add the repository's local Quanser Python libraries to sys.path."""
    repo_root = Path(__file__).resolve().parents[3]
    library_path = repo_root / "0_libraries" / "python"
    if library_path.exists():
        library_str = str(library_path)
        if library_str not in sys.path:
            sys.path.insert(0, library_str)
    return library_path


QUANSER_LIBRARY_PATH = add_quanser_libraries()

