from pathlib import Path
import sys


def _unique_paths(paths):
    seen = set()
    result = []
    for path in paths:
        resolved = Path(path).resolve()
        if resolved not in seen:
            seen.add(resolved)
            result.append(resolved)
    return result


APP_DIR = Path(__file__).resolve().parent
RESOURCE_BASE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR)).resolve()
WRITABLE_BASE_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else APP_DIR
RESOURCE_SEARCH_DIRS = _unique_paths([WRITABLE_BASE_DIR, RESOURCE_BASE_DIR, Path.cwd()])


def resource_path(relative_path):
    """Return a path to a bundled or local resource."""
    relative = Path(relative_path)
    for base_dir in RESOURCE_SEARCH_DIRS:
        candidate = base_dir / relative
        if candidate.exists():
            return str(candidate)
    return str(RESOURCE_BASE_DIR / relative)


def writable_path(relative_path):
    """Return a path suitable for user-visible generated files."""
    return str(WRITABLE_BASE_DIR / relative_path)
