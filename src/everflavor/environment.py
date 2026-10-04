"""Secrets (Colab Secrets or config/.env) and the download checker (2.3)."""
import os
from pathlib import Path


def in_colab():
    """True when running in Google Colab."""
    try:
        import google.colab  # noqa: F401
    except ImportError:
        return False
    return True


def short_path(p):
    """Show a path with the home folder as ~, so usernames stay out of saved outputs."""
    p, home = str(p), str(Path.home())
    return "~" + p[len(home):] if p.startswith(home) else p


def load_env_file(env_path):
    """Load KEY=value lines from an .env file into os.environ. Returns True if found."""
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


def get_secret(name):
    """Return a secret by name, or None if it is not set anywhere.

    Order: Colab Secrets (in Colab), then environment variables,
    which include everything loaded from .env.
    """
    if in_colab():
        try:
            from google.colab import userdata
            value = userdata.get(name)
        except Exception:  # noqa: BLE001 - secret not added or notebook access off; the error type varies by Colab version
            value = None
        if value:
            return value
    return os.environ.get(name) or None


def folder_has(folder, pattern):
    """Return the first file matching `pattern` under `folder`, or None."""
    folder = Path(folder).expanduser()
    return next(folder.rglob(pattern), None) if folder.is_dir() else None


def describe(path):
    """Size of a file or folder, plus the row count for Parquet files."""
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


def print_download_checks(checks, refresh=False):
    """Print each (step, item, path) with its size or MISSING; return the steps still to do."""
    print(f"{'Step':6s} {'Item':34s} Status")
    print("-" * 70)
    missing_steps = []
    for step, label, path in checks:
        present = path is not None and Path(path).exists() and (
            Path(path).is_file() or any(Path(path).iterdir()))
        status = f"yes  ({describe(path)})" if present else "MISSING"
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
