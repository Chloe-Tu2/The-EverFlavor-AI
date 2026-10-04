"""Secrets (Colab Secrets or config/.env) and the download checker (2.3)."""
from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path

__all__ = [
    "folder_has",
    "get_secret",
    "load_env_file",
    "print_download_checks",
    "short_path",
]


def _in_colab() -> bool:
    """Return True when running in Google Colab."""
    try:
        import google.colab  # noqa: F401
    except ImportError:
        return False
    return True


def short_path(p: str | Path) -> str:
    """Return a path with the home folder shown as ~, so usernames stay out of saved outputs.

    Windows paths ignore case (VS Code may open the project with a lowercase
    drive letter), so the comparison does too, and only a whole folder name
    counts as the home folder.
    """
    p, home = str(p), str(Path.home())
    norm_p, norm_home = os.path.normcase(p), os.path.normcase(home).rstrip("\\/")
    if norm_p == norm_home or norm_p.startswith(norm_home + os.sep):
        return "~" + p[len(norm_home):]
    return p


def load_env_file(env_path: Path) -> bool:
    """Load KEY=value lines from an .env file into the environment variables.

    Blank lines and # comments are skipped, "export KEY=..." and quoted values
    are accepted, and values already set are never replaced.

    Args:
        env_path: The .env file, for example config/.env.

    Returns:
        True if the file exists (and was read), False otherwise.
    """
    if not env_path.is_file():
        return False
    # utf-8-sig also handles files saved by Windows Notepad (which adds a BOM)
    with open(env_path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key.startswith("export "):
                key = key[len("export "):].strip()
            value = value.strip().strip('"').strip("'")
            if value and key not in os.environ:
                os.environ[key] = value
    return True


def get_secret(name: str) -> str | None:
    """Return a secret such as an API key, without ever printing it.

    Colab Secrets come first (in Colab), then environment variables, which
    include everything loaded from config/.env.

    Args:
        name: The secret's name, for example "USDA_API_KEY".

    Returns:
        The value, or None if it is not set anywhere.
    """
    if _in_colab():
        try:
            from google.colab import userdata
            value = userdata.get(name)
        except Exception:  # noqa: BLE001 - secret not added or notebook access off; the error type varies by Colab version
            value = None
        if value:
            return value
    return os.environ.get(name) or None


def folder_has(folder: str | Path, pattern: str) -> Path | None:
    """Return the first file matching `pattern` anywhere under `folder`, or None."""
    folder = Path(folder).expanduser()
    return next(folder.rglob(pattern), None) if folder.is_dir() else None


def _describe(path: str | Path) -> str:
    """Describe a file or folder: its size, plus the row count for Parquet files."""
    path = Path(path)
    files = [path] if path.is_file() else [f for f in path.rglob("*") if f.is_file()]
    total = sum(f.stat().st_size for f in files)
    size = f"{total / 1e6:,.1f} MB" if total >= 1e6 else f"{total / 1e3:,.0f} KB"
    if path.suffix == ".parquet":
        try:
            import pyarrow.parquet as pq
            return f"{size}, {pq.ParquetFile(path).metadata.num_rows:,} rows"
        except Exception:  # noqa: BLE001 - unreadable or partly written file: show the size only
            return size
    if path.is_dir():
        return f"{size}, {len(files)} files"
    return size


def print_download_checks(checks: Sequence[tuple[str, str, Path | None]], refresh: bool = False) -> list[str]:
    """Print which downloads and outputs exist, without downloading anything.

    Args:
        checks: (notebook step, item, file or folder that proves it is there) per item.
        refresh: Whether REFRESH_DOWNLOADS is on (adds a reminder line).

    Returns:
        The steps that still have something missing, in order.
    """
    print(f"{'Step':6s} {'Item':34s} Status")
    print("-" * 70)
    missing_steps = []
    for step, label, path in checks:
        present = path is not None and Path(path).exists() and (
            Path(path).is_file() or any(Path(path).iterdir()))
        status = f"yes  ({_describe(path)})" if present and path is not None else "MISSING"
        print(f"{step:6s} {label:34s} {status}")
        if not present and step not in missing_steps:
            missing_steps.append(step)
    print()
    if not missing_steps:
        print("Everything is downloaded and built. Running all cells reuses it.")
    else:
        print(f"Still to do: {', '.join(missing_steps)}. Run all cells; finished parts are skipped.")
    if refresh:
        print("REFRESH_DOWNLOADS is True: the cells in 2.4 will download everything again.")
    return missing_steps
