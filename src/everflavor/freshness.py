"""Food freshness from photos (notebook 05): one label scheme for many image sources,
near-duplicate groups, a split without leakage, coverage, and the training loop.

The model only ever says how food LOOKS; it never says food is safe to eat."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from collections.abc import Callable, Iterable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

from .progress import progress_bar

__all__ = [
    "AGE_PATTERNS",
    "ALLOWED_LICENSES",
    "FOOD_GROUPS",
    "IMAGE_SIGNATURES",
    "IMAGE_SUFFIXES",
    "ITEM_ALIASES",
    "SAFETY_NOTE",
    "STATES",
    "STATE_MAP",
    "TRAINING_PLAN",
    "freshness_coverage",
    "group_near_duplicates",
    "image_hashes",
    "index_images",
    "mendeley_download",
    "pack_results",
    "sample_weights",
    "selection_score",
    "split_without_leakage",
    "train_all_groups",
    "train_freshness_model",
    "zenodo_download",
]

SAFETY_NOTE = ("This only says how the food looks. Check the smell, texture and date; "
               "when in doubt, throw it out (USDA).")
STATES = ["fresh", "aging", "spoiled"]
# Each source's own words -> one state. Team decision: is an overripe banana "aging" or "spoiled"?
# A source whose words mean something else gets its own rule (SOURCE_STATE_RULES in notebook 05).
STATE_MAP = {
    "fresh": "fresh", "good": "fresh", "highly fresh": "fresh", "green": "fresh", "semi-ripe": "fresh",
    "semiripe": "fresh", "semi ripe": "fresh", "unripe": "fresh",
    "semi-fresh": "aging", "semifresh": "aging", "semi fresh": "aging", "half-fresh": "aging", "halffresh": "aging",
    "half fresh": "aging", "ripe": "aging",
    "overripe": "aging", "medium": "aging",
    "rotten": "spoiled", "bad": "spoiled", "spoiled": "spoiled", "not fresh": "spoiled", "stale": "spoiled",
    "moldy": "spoiled", "mouldy": "spoiled",
}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
# Food group -> items we know the names of (folder or file names are matched against them)
FOOD_GROUPS = {
    "produce": ["apple", "banana", "guava", "mango", "orange", "pomegranate", "lime", "lemon", "tomato", "carrot",
                "potato", "cucumber", "okra", "bell pepper", "capsicum", "bitter gourd", "strawberry", "grape",
                "indian gooseberry", "amla", "papaya", "peach", "pear", "onion", "cabbage", "spinach", "eggplant",
                "pineapple", "bitter melon", "bittermelon", "bitter gourd"],
    "meat": ["beef", "pork", "lamb", "chicken", "meat"],
    "fish": ["mackerel", "tilapia", "tuna", "fish", "carp", "catfish", "rohu", "salmon", "sardine"],
    "bread": ["bread", "bun", "toast", "loaf"],
}
# Other names sources use for an item: path words -> (food group, item)
ITEM_ALIASES = {
    "cowmeat": ("meat", "beef"), "cow meat": ("meat", "beef"),
    # Fish Eyes datasets name the fish by species
    "chanos": ("fish", "milkfish"), "oreochromis": ("fish", "tilapia"), "rastrelliger": ("fish", "mackerel"),
    "upeneus": ("fish", "goatfish"), "nibea": ("fish", "croaker"), "johnius": ("fish", "croaker"),
    "eleutheronema": ("fish", "threadfin"),
}
# Storage age written in a path: "day3", "day_3", "d3", "3days", "1-2 days"
AGE_PATTERNS = [re.compile(r"\bday[ _-]?(\d+)\b"), re.compile(r"\bd(\d+)\b"),
                re.compile(r"\b(\d+)[ _-]?days?\b"), re.compile(r"\b(\d+)[ _-](\d+)[ _-]?days?\b")]


def _words(path: Path, root: Path) -> str:
    """The path below `root`, lowercased, with separators as spaces ("Rotten_Apple/IMG_1.jpg" -> "rotten apple img 1")."""
    rel = path.relative_to(root).with_suffix("")
    return re.sub(r"[\\/_.]+", " ", str(rel).lower())


def _state(words: str, state_map: Mapping[str, str] = STATE_MAP) -> str | None:
    """The state named in the path words (longest name first, so "semi-fresh" beats "fresh")."""
    for name in sorted(state_map, key=len, reverse=True):
        if re.search(rf"(?<![a-z-]){re.escape(name)}(?![a-z-])", words):
            return state_map[name]
    return None


def _item(words: str) -> tuple[str | None, str | None]:
    """(food group, item) named in the path words, longest item name first."""
    candidates = [(i, g, i) for g, items in FOOD_GROUPS.items() for i in items]
    candidates += [(name, g, i) for name, (g, i) in ITEM_ALIASES.items()]
    for name, group, item in sorted(candidates, key=lambda c: len(c[0]), reverse=True):
        if re.search(rf"\b{re.escape(name)}e?s?\b", words):
            return group, item
    return None, None


def _age(words: str) -> tuple[float | None, float | None]:
    """(min days, max days) of storage written in the path words, or (None, None)."""
    span = AGE_PATTERNS[3].search(words)
    if span:
        return float(span.group(1)), float(span.group(2))
    for pattern in AGE_PATTERNS[:3]:
        m = pattern.search(words)
        if m:
            return float(m.group(1)), float(m.group(1))
    return None, None


# ------------------------------------------------------------------ downloads (section 2)
MENDELEY_API = "https://data.mendeley.com/public-api/datasets/"
DOWNLOAD_HEADERS = {"User-Agent": "EverFlavorAI/0.1 (+https://github.com/Chloe-Tu2/The-EverFlavor-AI)",
                    "Accept": "application/json"}


def _get_bytes(url: str, timeout: int) -> bytes:
    """GET a URL with urllib (Mendeley's bot check refuses the requests library, but not urllib)."""
    if not url.startswith("https://"):
        raise ValueError(f"only https downloads are allowed: {url}")
    request = urllib.request.Request(url, headers=DOWNLOAD_HEADERS)  # noqa: S310 - https only, checked above
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - https only, checked above
        return response.read()


def _download_to(url: str, target: Path, timeout: int, chunk: int = 2**20) -> Path:
    """Stream a URL to a file in 1 MB pieces (archives of several GB never sit in memory).

    The file is written under a temporary name first, so an interrupted download is
    never mistaken for a finished one.
    """
    if not url.startswith("https://"):
        raise ValueError(f"only https downloads are allowed: {url}")
    partial = target.with_name(target.name + ".part")
    request = urllib.request.Request(url, headers=DOWNLOAD_HEADERS)  # noqa: S310 - https only, checked above
    with urllib.request.urlopen(request, timeout=timeout) as response, open(partial, "wb") as out:  # noqa: S310
        while block := response.read(chunk):
            out.write(block)
    partial.replace(target)
    return target


# Only licenses that allow use with credit; anything else is refused before downloading
ALLOWED_LICENSES = {"CC BY 4.0", "CC BY 3.0", "CC0 1.0", "CC0"}


def mendeley_download(dataset_id: str, folder: str | Path, name_contains: str = "",
                      skip_names: Sequence[str] = ("augmented", ".rar"), refresh: bool = False,
                      timeout: int = 600) -> list[Path]:
    """Download and unzip the files of a public Mendeley Data dataset, after checking its license.

    The license is read from the dataset's record (not from an article), so the
    "to confirm" licenses of section 2 are checked here. Zip files are unpacked;
    files whose names contain a `skip_names` word (a source's own augmented copies, or
    .rar archives Python can not open) are not downloaded. Files stream to disk, so
    archives of several GB never sit in memory.

    Args:
        dataset_id: The dataset's Mendeley ID ("ptfscwtnyz").
        folder: Where its files go (data/raw/freshness_images/<source>/).
        name_contains: Only files whose names contain this text ("" for all).
        skip_names: Words that mark files to leave out.
        refresh: True downloads again even when the folder has files.
        timeout: Seconds per file.

    Returns:
        The downloaded (or already present) files and folders.

    Raises:
        PermissionError: When the dataset's license is not in ALLOWED_LICENSES.
    """
    folder = Path(folder)
    if (folder / "LICENSE.txt").exists() and not refresh:   # written last: the download finished
        return sorted(folder.iterdir())
    if not re.fullmatch(r"[a-z0-9]+", dataset_id):
        raise ValueError(f"not a Mendeley dataset ID: {dataset_id!r}")
    data = json.loads(_get_bytes(MENDELEY_API + dataset_id, 60))
    license_id = (data.get("data_licence") or {}).get("short_name", "")
    if license_id not in ALLOWED_LICENSES:
        raise PermissionError(f"Mendeley dataset {dataset_id} has license {license_id!r}; not downloaded")
    folder.mkdir(parents=True, exist_ok=True)
    # Datasets stored as loose files keep their labels in Mendeley folder names ("Chanos Chanos - Fresh"):
    # each file goes into a subfolder of that name, so index_images can read the label
    folder_names: dict[str, str] = {}
    files = [e for e in data.get("files", []) if name_contains.lower() in e.get("filename", "").lower()
             and not any(w in e.get("filename", "").lower() for w in skip_names)]
    if any(e.get("folder_id") for e in files):
        listing = json.loads(_get_bytes(f"{MENDELEY_API}{dataset_id}/folders/{data.get('version', 1)}", 60))
        folder_names = {f["id"]: re.sub(r"[^\w .()-]+", "_", f.get("name", "")).strip() for f in listing}
    loose: list[tuple[str, Path]] = []
    for entry in files:
        name = entry.get("filename", "")
        url = (entry.get("content_details") or {}).get("download_url")
        if not url:
            continue
        subfolder = folder / folder_names[entry["folder_id"]] if entry.get("folder_id") in folder_names else folder
        subfolder.mkdir(parents=True, exist_ok=True)
        if not name.lower().endswith(".zip"):
            loose.append((url, subfolder / Path(name).name))
            continue
        saved = _download_to(url, subfolder / Path(name).name, timeout)
        with zipfile.ZipFile(saved) as archive:
            for member in archive.namelist():   # never write outside `folder`
                target = (folder / member).resolve()
                if not target.is_relative_to(folder.resolve()):
                    raise ValueError(f"unsafe path in {name}: {member}")
            archive.extractall(folder)
        saved.unlink()   # the unpacked photos are kept, not the archive
    # Loose files: 8 at a time, skipping those a stopped run already saved
    todo = [(url, target) for url, target in loose if refresh or not target.exists()]
    with ThreadPoolExecutor(max_workers=8) as pool:
        jobs = [pool.submit(_download_to, url, target, timeout) for url, target in todo]
        for job in progress_bar(as_completed(jobs), f"Mendeley {dataset_id}", total=len(jobs), show=len(jobs) > 20):
            job.result()
    credit = [data.get("name", dataset_id), f"{license_id}: {(data.get('data_licence') or {}).get('url', '')}",
              f"https://doi.org/{(data.get('doi') or {}).get('id', '')}"]
    (folder / "LICENSE.txt").write_text("\n".join(credit) + "\n", encoding="utf-8")
    return sorted(folder.iterdir())


ZENODO_API = "https://zenodo.org/api/records/"
# Zenodo license ids that allow use with credit
ZENODO_LICENSES = {"cc-by-4.0", "cc-by-3.0", "cc0-1.0"}


# What mendeley_download and zenodo_download can raise: network errors and refused licenses (OSError),
# unsafe archive paths and bad answers (ValueError), a missing .rar tool (RuntimeError), a failed unpack
DOWNLOAD_ERRORS = (OSError, ValueError, RuntimeError, subprocess.SubprocessError, zipfile.BadZipFile)


def _rar_tool() -> list[str]:
    """The command that unpacks a .rar archive here: Windows' own tar (libarchive), bsdtar or unrar.

    Raises:
        RuntimeError: If none is installed (Colab: `!apt-get install -y unrar`).
    """
    if sys.platform == "win32":
        # Windows 10/11 tar is bsdtar, which reads .rar; called by its full path, since Git Bash
        # puts its own GNU tar (which can not) first on PATH
        windows_tar = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "tar.exe"
        if windows_tar.exists():
            return [str(windows_tar)]
    for tool in ("bsdtar", "unrar"):
        if shutil.which(tool):
            return [tool]
    raise RuntimeError("No program to unpack .rar files: install unrar (Colab: !apt-get install -y unrar)")


def _unpack_rar(archive: Path, folder: Path) -> None:
    """List a .rar archive, refuse paths that leave `folder`, then unpack it there."""
    tool = _rar_tool()
    if tool[0] == "unrar":
        listing = subprocess.run(["unrar", "lb", str(archive)],  # noqa: S603, S607 - fixed tool, our own paths
                                 capture_output=True, text=True, check=True).stdout
        unpack = ["unrar", "x", "-o+", str(archive), str(folder) + "/"]
    else:
        listing = subprocess.run([*tool, "-tf", str(archive)],  # noqa: S603 - fixed tool, our own paths
                                 capture_output=True, text=True, check=True).stdout
        unpack = [*tool, "-xf", str(archive), "-C", str(folder)]
    for member in listing.splitlines():
        if member.strip() and not (folder / member.strip()).resolve().is_relative_to(folder.resolve()):
            raise ValueError(f"unsafe path in {archive.name}: {member}")
    subprocess.run(unpack, check=True, capture_output=True)  # noqa: S603 - every member path checked above


def zenodo_download(record_id: str, folder: str | Path, refresh: bool = False, timeout: int = 7200) -> list[Path]:
    """Download and unpack a public Zenodo record's files, after checking its license.

    The license is read from the record itself (MeatScan: CC BY 4.0). Files stream to
    disk; .zip and .rar archives are unpacked (paths that would leave `folder` are
    refused) and then deleted, so only the photos are kept.

    Args:
        record_id: The Zenodo record number ("16764338").
        folder: Where its files go (data/raw/freshness_images/<source>/).
        refresh: True downloads again even when the folder has files.
        timeout: Seconds per file.

    Returns:
        The downloaded (or already present) files and folders.

    Raises:
        PermissionError: When the record's license is not in ZENODO_LICENSES.
    """
    folder = Path(folder)
    if (folder / "LICENSE.txt").exists() and not refresh:   # written last: the download finished
        return sorted(folder.iterdir())
    if not re.fullmatch(r"\d+", record_id):
        raise ValueError(f"not a Zenodo record number: {record_id!r}")
    data = json.loads(_get_bytes(ZENODO_API + record_id, 60))
    meta = data.get("metadata", {})
    license_id = str((meta.get("license") or {}).get("id", "")).lower()
    if license_id not in ZENODO_LICENSES:
        raise PermissionError(f"Zenodo record {record_id} has license {license_id!r}; not downloaded")
    folder.mkdir(parents=True, exist_ok=True)
    for entry in data.get("files", []):
        name = Path(entry["key"]).name
        saved = folder / name
        if not (saved.exists() and saved.stat().st_size == entry.get("size")):   # finished earlier: reuse it
            _download_to(entry["links"]["self"], saved, timeout)
        if name.lower().endswith(".zip"):
            with zipfile.ZipFile(saved) as archive:
                for member in archive.namelist():
                    if not (folder / member).resolve().is_relative_to(folder.resolve()):
                        raise ValueError(f"unsafe path in {name}: {member}")
                archive.extractall(folder)
            saved.unlink()
        elif name.lower().endswith(".rar"):
            _unpack_rar(saved, folder)
            saved.unlink()
    credit = [meta.get("title", record_id), f"{license_id}: https://zenodo.org/records/{record_id}",
              f"https://doi.org/{data.get('doi', '')}"]
    (folder / "LICENSE.txt").write_text("\n".join(credit) + "\n", encoding="utf-8")
    return sorted(folder.iterdir())


# How each image format begins; a file that begins otherwise (MeatScan has 439 files of zero bytes) is skipped
IMAGE_SIGNATURES = (b"\xff\xd8\xff", b"\x89PNG", b"BM", b"RIFF")


def _looks_like_image(path: Path) -> bool:
    """True when the file begins like a JPEG, PNG, BMP or WebP image."""
    with open(path, "rb") as f:
        return f.read(4).startswith(IMAGE_SIGNATURES)


def index_images(source: str, folder: str | Path, license_name: str = "", group: str | None = None,
                 series: bool = False, state_rules: Mapping[str, str] | None = None) -> pd.DataFrame:
    """One row per image of a source, with the label scheme read from its folder and file names.

    Most sources put the state and item in folder names ("Rotten/Apple/1.jpg",
    "fresh_banana_12.png"); those words are mapped with STATE_MAP and FOOD_GROUPS.
    Copies made by a source's own augmentation ("aug", "flip", "rotate" in the name)
    are skipped: augmentation happens during training, never as saved files.

    Args:
        source: The source's short name (IMAGE_SOURCES in notebook 05).
        folder: Where its images were unpacked.
        license_name: The source's license, kept on every row.
        group: The food group when the whole source is one group ("fish"); None reads it from the names.
        series: True when each folder holds one item photographed over time (DaFiF's fish,
            TriModal's fruit, the team's photos): the folder is then the photo set. False
            (most sources: one photo per item, folders named after the class) makes every
            image its own photo set; near-duplicates are still grouped later.
        state_rules: Words this source uses differently, over STATE_MAP (Multistage Fish
            Eyes calls fish kept 2-4 days "Fresh", which is "aging" in our scheme).

    Returns:
        path, source, license, group, item, state, age_days_min, age_days_max, photo_set
        (images of one item or session, kept in one split).
        Images whose state can not be read are kept with an empty state, for a hand check.
    """
    root = Path(folder)
    state_map = {**STATE_MAP, **(state_rules or {})}
    rows = []
    not_images = 0
    for path in sorted(p for p in root.rglob("*") if p.suffix.lower() in IMAGE_SUFFIXES):
        if not _looks_like_image(path):
            not_images += 1
            continue
        words = _words(path, root)
        if re.search(r"\b(?:aug|augmented|flip|flipped|rotate|rotated)\b", words):
            continue
        found_group, item = _item(words)
        age_min, age_max = _age(words)
        rows.append({"path": str(path), "source": source, "license": license_name, "group": group or found_group,
                     "item": item, "state": _state(words, state_map), "age_days_min": age_min, "age_days_max": age_max,
                     "photo_set": f"{source}:{(path.parent if series else path).relative_to(root).as_posix()}"})
    if not_images:
        print(f"{source}: skipped {not_images} files that are not images (empty or broken)")
    return pd.DataFrame(rows, columns=["path", "source", "license", "group", "item", "state", "age_days_min",
                                       "age_days_max", "photo_set"])


def _popcount(values: np.ndarray) -> np.ndarray:
    """Bits set in each 64-bit value (NumPy 2's bitwise_count, or the same count on older NumPy)."""
    if hasattr(np, "bitwise_count"):
        return np.bitwise_count(values)
    return np.unpackbits(values.astype(">u8").view(np.uint8).reshape(-1, 8), axis=1).sum(axis=1)


def group_near_duplicates(index: pd.DataFrame, max_distance: int = 4, hashes: Sequence[object] | None = None) -> pd.Series:
    """Group images whose perceptual hashes (imagehash.phash) differ by at most `max_distance` bits.

    Near-identical photos (the same fruit from two angles, or a dataset that copies
    another) must stay in one split, like ingredient_group in notebook 01.

    Args:
        index: Images with a `path` column.
        max_distance: Largest Hamming distance between two hashes of one group.
        hashes: Precomputed hashes in `index` order (tests); None computes them with imagehash.

    Returns:
        A duplicate-group id per image (the index of the group's first image), aligned with `index`.
    """
    if hashes is None:
        import imagehash
        from PIL import Image, ImageFile
        ImageFile.LOAD_TRUNCATED_IMAGES = True   # a photo missing its last bytes still hashes (MeatScan has one)
        hashes = []
        for path in progress_bar(index["path"], "Perceptual hashes", show=len(index) >= 2000):
            try:
                with Image.open(path) as image:
                    hashes.append(imagehash.phash(image))
            except OSError:
                hashes.append(None)
    unreadable = [i for i, h in enumerate(hashes) if h is None]
    if unreadable:
        print(f"{len(unreadable)} unreadable images, each kept in a group of its own:",
              [str(index["path"].iloc[i]) for i in unreadable[:5]])
    # Unreadable images get a placeholder hash and are never joined to another image
    bits = np.array([np.asarray(h.hash if hasattr(h, "hash") else h, dtype=bool).ravel() if h is not None
                     else np.zeros(64, dtype=bool) for h in hashes])
    loners = set(unreadable)
    # Each 64-bit hash as one integer: two hashes differ in popcount(a XOR b) bits, which is fast
    # enough to compare tens of thousands of photos with each other
    packed = np.packbits(bits, axis=1).view(">u8").ravel() if len(bits) else np.array([], dtype=">u8")
    parent = list(range(len(bits)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(bits)):
        if i in loners:
            continue
        close = np.nonzero(_popcount(packed[i + 1:] ^ packed[i]) <= max_distance)[0] + i + 1
        for j in close:
            if int(j) not in loners:
                parent[find(int(j))] = find(i)
    return pd.Series([find(i) for i in range(len(bits))], index=index.index, name="duplicate_group")


def split_without_leakage(index: pd.DataFrame, fractions: Mapping[str, float] | None = None,
                          seed: int = 0) -> pd.Series:
    """Assign train / val / test by photo set and duplicate group, never by single image.

    DaFiF photographs one fish for 11 days, so a random split would put day 3 of a
    fish in training and day 4 of the same fish in test. Every image of a photo set,
    and every near-duplicate of it, gets the same split (the same idea as
    `ingredient_group` in notebook 01). The split comes from a hash of the group, so
    it does not change when images are added.

    Args:
        index: Images with `photo_set` and, if computed, `duplicate_group`.
        fractions: {"train": 0.7, "val": 0.15, "test": 0.15} by default.
        seed: Changes the assignment.

    Returns:
        "train", "val" or "test" per image, aligned with `index`.
    """
    fractions = dict(fractions or {"train": 0.7, "val": 0.15, "test": 0.15})
    # Photo sets joined by a near-duplicate become one group
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    if "duplicate_group" in index:
        for _, sets in index.groupby("duplicate_group")["photo_set"]:
            first = find(str(sets.iloc[0]))
            for s in sets.iloc[1:]:
                parent[find(str(s))] = first
    groups = index["photo_set"].astype(str).map(find)
    cuts = np.cumsum(list(fractions.values()))

    def assign(group: str) -> str:
        u = int(hashlib.sha1(f"{seed}:{group}".encode(), usedforsecurity=False).hexdigest()[:8], 16) / 0xFFFFFFFF
        return list(fractions)[int(np.searchsorted(cuts, u * cuts[-1], side="right").clip(0, len(cuts) - 1))]

    return groups.map(assign).rename("split")


def freshness_coverage(index: pd.DataFrame, min_images: int = 100) -> pd.DataFrame:
    """Images per group, item, state and source, with a warning where an item and state are thin.

    Returns:
        group, item, state, source, images, item_state_images (all sources together),
        warning ("fewer than N images" or "").
    """
    labeled = index.dropna(subset=["state"])
    counts = (labeled.groupby(["group", "item", "state", "source"], dropna=False).size()
              .rename("images").reset_index())
    totals = labeled.groupby(["group", "item", "state"], dropna=False).size().rename("item_state_images")
    counts = counts.merge(totals.reset_index(), on=["group", "item", "state"])
    counts["warning"] = np.where(counts["item_state_images"] < min_images, f"fewer than {min_images} images", "")
    return counts.sort_values(["group", "item", "state", "source"], ignore_index=True)


def sample_weights(index: pd.DataFrame) -> pd.Series:
    """Training weights: every source counts equally, and within a source every state counts equally.

    So a large dataset does not drown out a small one, and a source with few
    spoiled photos still teaches what spoiled looks like. Weights average 1.

    Returns:
        One weight per image, aligned with `index`.
    """
    n_sources = index["source"].nunique()
    per_cell = index.groupby(["source", "state"])["source"].transform("size")
    states_in_source = index.groupby("source")["state"].transform("nunique")
    weights = 1.0 / (n_sources * states_in_source * per_cell)
    return (weights * len(index) / weights.sum()).rename("weight")


def selection_score(true_states: Iterable[str], predicted: Iterable[str]) -> dict[str, float]:
    """The scores that pick the best epoch, safety first.

    `spoiled_called_fresh`: the share of spoiled photos the model calls fresh (the
    costly error, lower is better), then `macro_f1` (every state counts equally).

    Returns:
        {"spoiled_called_fresh", "macro_f1", "accuracy"}.
    """
    from sklearn.metrics import accuracy_score, f1_score

    y, p = np.asarray(list(true_states)), np.asarray(list(predicted))
    spoiled = y == "spoiled"
    return {"spoiled_called_fresh": float((p[spoiled] == "fresh").mean()) if spoiled.any() else 0.0,
            "macro_f1": float(f1_score(y, p, labels=STATES, average="macro", zero_division=0)),
            "accuracy": float(accuracy_score(y, p))}


TRAINING_PLAN = {
    "image_size": 224,
    "batch_size": 32,
    "head_only_epochs": 5,
    "max_finetune_epochs": 30,
    "patience": 5,               # fine-tuning epochs without a new best before stopping
    "head_learning_rate": 1e-3,
    "finetune_learning_rate": 1e-4,
    "selection_metric": "fewest spoiled_called_fresh among epochs within f1_tolerance of the best macro F1, then macro F1",
    "f1_tolerance": 0.05,
    "weights": "equal per source, then equal per state within a source",
    "seeds": [0, 1, 2],
}


def training_device() -> tuple[str, str | None]:
    """Where training runs: ("cuda", GPU name), ("mps", "Apple GPU") or ("cpu", None).

    NVIDIA GPUs (Colab's T4, a gaming PC) come first, then the GPU built into Apple
    M-series Macs; everything else trains on the processor. ("cpu", None) also when
    torch is not installed (it is only needed to train).
    """
    try:
        import torch
    except ImportError:
        return "cpu", None
    if torch.cuda.is_available():
        return "cuda", torch.cuda.get_device_name(0)
    if torch.backends.mps.is_available():
        return "mps", "Apple GPU (MPS)"
    return "cpu", None


def _ram_gb() -> float | None:
    """Total memory in GB, with the standard library only (None if it can not be read)."""
    # getattr: windll exists only on Windows and sysconf only elsewhere, so the type check reads the same everywhere
    try:
        if os.name == "nt":
            import ctypes

            class MemoryStatus(ctypes.Structure):
                _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong), ("total", ctypes.c_ulonglong),
                            ("available", ctypes.c_ulonglong), ("page_total", ctypes.c_ulonglong),
                            ("page_free", ctypes.c_ulonglong), ("virtual_total", ctypes.c_ulonglong),
                            ("virtual_free", ctypes.c_ulonglong), ("extended", ctypes.c_ulonglong)]

            status = MemoryStatus()
            status.length = ctypes.sizeof(MemoryStatus)
            getattr(ctypes, "windll").kernel32.GlobalMemoryStatusEx(ctypes.byref(status))   # noqa: B009
            return float(status.total) / 1e9
        sysconf = getattr(os, "sysconf")   # noqa: B009
        return float(sysconf("SC_PAGE_SIZE") * sysconf("SC_PHYS_PAGES")) / 1e9
    except (AttributeError, OSError, ValueError):
        return None


def _gpu_names() -> list[str]:
    """Every graphics card the system reports (NVIDIA, AMD, Intel, Apple, Qualcomm...), any vendor."""
    if sys.platform == "win32":
        command = ["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_VideoController).Name"]
    elif sys.platform == "darwin":
        command = ["system_profiler", "SPDisplaysDataType"]
    elif shutil.which("nvidia-smi"):
        command = ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"]
    else:
        command = ["lspci"]
    try:
        lines = subprocess.run(command, check=False, capture_output=True,  # noqa: S603 - fixed commands
                               text=True, timeout=30).stdout.splitlines()
    except (OSError, subprocess.SubprocessError):
        return []
    if command[0] == "system_profiler":
        lines = [line.split(":", 1)[1] for line in lines if "Chipset Model" in line]
    elif command[0] == "lspci":
        lines = [line.split(": ", 1)[-1] for line in lines if "VGA" in line or "3D controller" in line]
    return [line.strip() for line in lines if line.strip()]


def system_check(folder: str | Path = ".") -> dict:
    """What this computer has: processor cores, memory, free disk where the photos go, graphics cards
    and the device PyTorch would train on (training_device)."""
    device, device_name = training_device()
    ram = _ram_gb()
    return {"cpu_cores": os.cpu_count() or 1, "ram_gb": None if ram is None else round(ram, 1),
            "free_disk_gb": round(shutil.disk_usage(folder).free / 1e9, 1), "gpus": _gpu_names(),
            "device": device, "device_name": device_name}


def system_verdict(info: Mapping[str, object], in_colab: bool = False, disk_needed_gb: float = 10.0) -> list[str]:
    """Plain sentences on what this computer can handle, from system_check.

    The photos need about 7 GB (MeatScan adds about 50 GB while it unpacks); training needs a GPU
    PyTorch can use (NVIDIA, or Apple M-series) and about 8 GB of memory.
    """
    gpus = [str(g) for g in info.get("gpus") or []]   # type: ignore[attr-defined]
    ram, disk, device = info.get("ram_gb"), float(str(info.get("free_disk_gb") or 0)), info.get("device")
    lines = []
    if disk < disk_needed_gb:
        lines.append(f"NOT ENOUGH DISK: {disk:.0f} GB free, the photos need about {disk_needed_gb:.0f} GB. "
                     "Free some space or run in Colab.")
    else:
        lines.append(f"Disk: OK ({disk:.0f} GB free; the photos need about {disk_needed_gb:.0f} GB).")
    if isinstance(ram, (int, float)) and ram < 8:
        lines.append(f"LOW MEMORY: {ram:.0f} GB; sections 2-4 work, but training may run out of memory. Use Colab to train.")
    if device in ("cuda", "mps"):
        lines.append(f"Training: OK, on {info.get('device_name')}.")
    elif in_colab:
        lines.append("Training: no GPU in this session. Runtime > Change runtime type > T4 GPU, then run all again.")
    elif any("nvidia" in g.lower() for g in gpus):
        lines.append("Training: an NVIDIA GPU is here, but PyTorch can not use it yet. Install the CUDA build "
                     "from https://pytorch.org/get-started/locally/ and restart the kernel.")
    else:
        found = ", ".join(gpus) if gpus else "none found"
        lines.append(f"Training: no GPU PyTorch can use (graphics: {found}; PyTorch trains on NVIDIA or Apple "
                     "M-series GPUs). It would run on the processor: hours even for one group and one seed. "
                     "Sections 2-4 and 7 run fine here; train in Colab (free T4 GPU).")
    return lines


def pick_best_epoch(history: Sequence[Mapping[str, object]], tolerance: float = 0.05) -> Mapping[str, object]:
    """The epoch to keep: the fewest spoiled photos called fresh, then the best macro F1, among the
    epochs whose macro F1 is within `tolerance` of the best one.

    Safety comes first, but only among good models: without the tolerance, an early epoch that
    happened to call few spoiled photos fresh while getting most others wrong could win (fish,
    seed 1, Colab run of 2026-10-13: macro F1 0.60 kept over 0.73-0.78).
    """
    top = max(float(str(h["macro_f1"])) for h in history)
    eligible = [h for h in history if float(str(h["macro_f1"])) >= top - tolerance]
    return min(eligible, key=lambda h: (float(str(h["spoiled_called_fresh"])), -float(str(h["macro_f1"]))))


_IMAGENET = ([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])   # the pretrained model's color scaling


def _eval_transform(size: int):
    """How a photo is prepared for scoring (validation during training, and the final test)."""
    from torchvision import transforms
    return transforms.Compose([transforms.Resize(int(size * 1.14)), transforms.CenterCrop(size),
                               transforms.ToTensor(), transforms.Normalize(*_IMAGENET)])


def train_freshness_model(index: pd.DataFrame, group: str, out_dir: str | Path,
                          plan: Mapping[str, object] = TRAINING_PLAN, seed: int = 0) -> dict:
    """Fine-tune MobileNetV3 on one food group's `state`, with early stopping on the validation split.

    Phase 1 trains only the new last layer (the pretrained model frozen); phase 2
    fine-tunes the whole model with a lower learning rate. After every epoch the
    validation split is scored with selection_score and the best epoch (pick_best_epoch)
    is kept, not the last one; training stops after `patience` fine-tuning epochs without
    a new best (the head-only epochs do not count). The test split is never read here: it is used once, at the very end.
    Augmentation (random crops, flips, small color changes) happens on the fly.

    Needs torch and torchvision (and, in practice, a GPU: Colab > Runtime > Change runtime type > GPU).

    Args:
        index: Images with path, group, state, split and weight (sample_weights).
        group: The food group to train ("produce", "meat", "fish", "bread").
        out_dir: Where the best model is saved (models/freshness/, not stored in GitHub).
        plan: TRAINING_PLAN.
        seed: Random seed; run with each of plan["seeds"] and report the average and spread.

    Returns:
        {"group", "seed", "best_epoch", "val_scores", "model_path", "history"}.
    """
    import torch
    from PIL import Image, ImageFile
    ImageFile.LOAD_TRUNCATED_IMAGES = True
    from torch import nn
    from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
    from torchvision import models, transforms

    torch.manual_seed(seed)
    data = index[(index["group"] == group) & index["state"].notna()]
    if data.empty:
        raise ValueError(f"no labeled images for group {group!r}")
    size = int(str(plan["image_size"]))
    train_tf = transforms.Compose([transforms.RandomResizedCrop(size, scale=(0.7, 1.0)), transforms.RandomHorizontalFlip(),
                                   transforms.ColorJitter(0.2, 0.2, 0.2), transforms.ToTensor(), transforms.Normalize(*_IMAGENET)])
    eval_tf = _eval_transform(size)

    class Images(Dataset):
        def __init__(self, rows: pd.DataFrame, tf: object):
            self.paths, self.tf = rows["path"].tolist(), tf
            self.labels = [STATES.index(s) for s in rows["state"]]

        def __len__(self) -> int:
            return len(self.paths)

        def __getitem__(self, i: int):
            with Image.open(self.paths[i]) as image:
                return self.tf(image.convert("RGB")), self.labels[i]   # type: ignore[operator]

    train, val = data[data["split"] == "train"], data[data["split"] == "val"]
    batch = int(str(plan["batch_size"]))
    sampler = WeightedRandomSampler(train["weight"].astype(float).tolist(), len(train))
    # Two loader processes on Linux (Colab); none on Windows or macOS, which start them by pickling the
    # dataset, and this one is defined inside the function (smoke test on Windows, 2026-10-11)
    workers = 2 if sys.platform.startswith("linux") else 0
    train_loader = DataLoader(Images(train, train_tf), batch_size=batch, sampler=sampler, num_workers=workers)
    val_loader = DataLoader(Images(val, eval_tf), batch_size=batch, num_workers=workers)
    device = training_device()[0]
    model = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
    model.classifier[-1] = nn.Linear(model.classifier[-1].in_features, len(STATES))
    model.to(device)
    loss_fn = nn.CrossEntropyLoss()

    def run_epoch(optimizer: torch.optim.Optimizer) -> None:
        model.train()
        for x, y in train_loader:
            optimizer.zero_grad()
            loss_fn(model(x.to(device)), y.to(device)).backward()
            optimizer.step()

    def evaluate() -> dict[str, float]:
        model.eval()
        predicted: list[str] = []
        with torch.no_grad():
            for x, _ in val_loader:
                predicted += [STATES[i] for i in model(x.to(device)).argmax(1).tolist()]
        return selection_score(val["state"], predicted)

    out = Path(out_dir) / f"freshness_{group}_seed{seed}.pt"
    out.parent.mkdir(parents=True, exist_ok=True)
    tolerance, patience = float(str(plan["f1_tolerance"])), int(str(plan["patience"]))
    history: list[dict] = []
    weights: dict[int, dict] = {}   # copies of the epochs that can still be picked (about 6 MB each)
    best_epoch, epoch = None, 0
    phases = [("head", int(str(plan["head_only_epochs"])), float(str(plan["head_learning_rate"])), False),
              ("finetune", int(str(plan["max_finetune_epochs"])), float(str(plan["finetune_learning_rate"])), True)]
    epoch = 0
    for phase, epochs, rate, all_layers in phases:
        for name, param in model.named_parameters():
            param.requires_grad = all_layers or name.startswith("classifier")
        optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=rate)
        since_best = 0
        for _ in range(epochs):
            epoch += 1
            run_epoch(optimizer)
            history.append({"epoch": epoch, "phase": phase, **evaluate()})
            weights[epoch] = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            # The best macro F1 only rises, so an epoch that falls out of the tolerance never comes back
            top = max(h["macro_f1"] for h in history)
            weights = {e: w for e, w in weights.items() if history[e - 1]["macro_f1"] >= top - tolerance}
            picked = int(str(pick_best_epoch(history, tolerance)["epoch"]))
            if picked != best_epoch:
                best_epoch, since_best = picked, 0
                torch.save(weights[picked], out)
            elif phase == "finetune":
                since_best += 1
                if since_best >= patience:
                    break
    best = pick_best_epoch(history, tolerance)
    return {"group": group, "seed": seed, "best_epoch": best["epoch"],
            "val_scores": {k: v for k, v in best.items() if k not in ("epoch", "phase")},
            "model_path": str(out), "history": history}


# ---------------------------------------------------------------- long runs (Google Colab, 2026-10-10)
def image_hashes(paths: Sequence[str | Path], cache_file: str | Path | None = None) -> list[object]:
    """Perceptual hashes (imagehash.phash) for group_near_duplicates, reusing a saved cache.

    Hashing about 45,000 photos takes about half an hour, and Colab forgets everything when a
    session ends, so the hashes are kept in `cache_file` (path, file size, hash): a later run
    hashes only new files and files whose size changed. The file's date is not used, because
    every new Colab session downloads the photos again with new dates.

    Args:
        paths: Image paths, in the order of the image index.
        cache_file: A .parquet file to read and update; None hashes everything without a cache.

    Returns:
        One hash per path (an imagehash.ImageHash), or None for an image that can not be read.
    """
    import imagehash
    from PIL import Image, ImageFile
    ImageFile.LOAD_TRUNCATED_IMAGES = True   # a photo missing its last bytes still hashes (MeatScan has one)
    cache: dict[tuple[str, int], str] = {}
    if cache_file is not None and Path(cache_file).exists():
        saved = pd.read_parquet(cache_file)
        cache = {(p, int(s)): h for p, s, h in zip(saved["path"], saved["size"], saved["hash"])}
    hashes: list[object] = []
    rows = []
    for path in progress_bar([str(p) for p in paths], "Perceptual hashes", show=len(paths) >= 2000):
        size = Path(path).stat().st_size if Path(path).exists() else -1
        known = cache.get((path, size))
        if known is None:
            try:
                with Image.open(path) as image:
                    known = str(imagehash.phash(image))
            except OSError:
                known = ""
        hashes.append(imagehash.hex_to_hash(known) if known else None)
        rows.append((path, size, known))
    if cache_file is not None:
        Path(cache_file).parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows, columns=["path", "size", "hash"]).to_parquet(cache_file, index=False)
    return hashes


def train_all_groups(index: pd.DataFrame, groups: Sequence[str], seeds: Sequence[int], model_dir: str | Path,
                     results_dir: str | Path, plan: Mapping[str, object] = TRAINING_PLAN,
                     train: Callable[..., dict] | None = None) -> list[dict]:
    """Train one model per food group and seed, saving each result as soon as it is done.

    Free Colab sessions can disconnect after a few hours; a model that finished is not trained
    again: its saved result (results_dir/freshness_<group>_seed<seed>.json) is read back, so running
    the cell again continues where the session stopped. A saved result whose kept epoch is not the
    one pick_best_epoch chooses from its history (trained under an older rule) is trained again.

    Args:
        index: Images with path, group, state, split and weight.
        groups: Food groups to train ("produce", "fish" ...).
        seeds: Random seeds (TRAINING_PLAN["seeds"]).
        model_dir: Where the models are saved.
        results_dir: Where each result is saved as JSON.
        plan: TRAINING_PLAN.
        train: The training function (train_freshness_model; the tests pass a fake one).

    Returns:
        One result per group and seed, as train_freshness_model returns it.
    """
    train = train or train_freshness_model
    tolerance = float(str(plan["f1_tolerance"]))
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for group in groups:
        for seed in seeds:
            saved = results_dir / f"freshness_{group}_seed{seed}.json"
            if saved.exists():
                old = json.loads(saved.read_text(encoding="utf-8"))
                history = old.get("history")
                if not history or pick_best_epoch(history, tolerance)["epoch"] == old["best_epoch"]:
                    results.append(old)
                    continue
            result = train(index, group, model_dir, plan, seed)
            saved.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
            results.append(result)
    return results


def pack_results(paths: Sequence[str | Path], zip_file: str | Path) -> list[str]:
    """Put files and folders into one zip to share (from Colab: download it, or keep it on Drive).

    Args:
        paths: Files or folders; missing ones are skipped.
        zip_file: The zip to write (replaced if it exists).

    Returns:
        The names stored in the zip.
    """
    zip_file = Path(zip_file)
    zip_file.parent.mkdir(parents=True, exist_ok=True)
    names: list[str] = []
    with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in map(Path, paths):
            files = sorted(p for p in path.rglob("*") if p.is_file()) if path.is_dir() else [path] if path.exists() else []
            for file in files:
                if file.resolve() == zip_file.resolve():
                    continue
                name = str(file.relative_to(path.parent)).replace("\\", "/")
                archive.write(file, name)
                names.append(name)
    return names


def predict_states(paths: Sequence[str | Path], model_paths: Sequence[str | Path],
                   plan: Mapping[str, object] = TRAINING_PLAN, batch_size: int = 64) -> np.ndarray:
    """The probability of each state (STATES order) for each photo, from each saved model.

    Each photo is read once and scored by every model (the seeds of one food group). Runs on
    the GPU when there is one, otherwise on the processor (a few minutes for a few thousand photos).

    Returns:
        An array of shape (models, photos, 3).
    """
    import torch
    from PIL import Image, ImageFile
    ImageFile.LOAD_TRUNCATED_IMAGES = True
    from torch import nn
    from torchvision import models as tv_models

    device = training_device()[0]
    nets = []
    for model_path in model_paths:
        net = tv_models.mobilenet_v3_small(weights=None)
        net.classifier[-1] = nn.Linear(net.classifier[-1].in_features, len(STATES))
        net.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
        nets.append(net.to(device).eval())
    transform = _eval_transform(int(str(plan["image_size"])))
    out = np.zeros((len(nets), len(paths), len(STATES)), dtype=np.float32)
    with torch.no_grad():
        for start in progress_bar(range(0, len(paths), batch_size), "Scoring photos"):
            batch = []
            for path in paths[start:start + batch_size]:
                with Image.open(path) as image:
                    batch.append(transform(image.convert("RGB")))
            x = torch.stack(batch).to(device)
            for m, net in enumerate(nets):
                out[m, start:start + len(batch)] = torch.softmax(net(x), dim=1).cpu().numpy()
    return out


def apply_spoiled_threshold(probabilities: np.ndarray, threshold: float | None = None) -> list[str]:
    """The predicted state: the most likely one, but "spoiled" whenever its probability reaches
    `threshold` (None: the most likely state only)."""
    predicted = np.asarray(STATES)[probabilities.argmax(axis=1)]
    if threshold is not None:
        predicted = np.where(probabilities[:, STATES.index("spoiled")] >= threshold, "spoiled", predicted)
    return predicted.tolist()


def choose_spoiled_threshold(true_states: Sequence[str], probabilities: np.ndarray,
                             target: float = 0.005) -> float | None:
    """The highest spoiled threshold that keeps spoiled_called_fresh at or under `target` on these photos
    (the validation split; never the test split).

    The highest such threshold adds the fewest "check it" warnings on fresh food. None when the most
    likely state already meets the target (no threshold needed).
    """
    def called_fresh(threshold: float | None) -> float:
        return selection_score(true_states, apply_spoiled_threshold(probabilities, threshold))["spoiled_called_fresh"]

    if called_fresh(None) <= target:
        return None
    # Lowering the threshold only turns more photos into "spoiled", so the first one that meets the target
    # (from the top) is the highest
    for threshold in sorted({round(float(v), 4) for v in probabilities[:, STATES.index("spoiled")]}, reverse=True):
        if called_fresh(threshold) <= target:
            return threshold
    return 0.0


def detailed_scores(true_states: Sequence[str], predicted: Sequence[str]) -> dict:
    """selection_score plus what the safety rule costs (fresh photos called spoiled), the share of each
    state found (recall), and the confusion matrix (rows: true state; columns: predicted)."""
    from sklearn.metrics import confusion_matrix, recall_score

    y, p = np.asarray(list(true_states)), np.asarray(list(predicted))
    fresh = y == "fresh"
    recall = recall_score(y, p, labels=STATES, average=None, zero_division=0)
    return {**selection_score(y, p),
            "fresh_called_spoiled": float((p[fresh] == "spoiled").mean()) if fresh.any() else 0.0,
            "recall": {state: float(r) for state, r in zip(STATES, recall)},
            "confusion": confusion_matrix(y, p, labels=STATES).tolist(),
            "photos": len(y)}


def final_test(index: pd.DataFrame, model_dir: str | Path, results_dir: str | Path,
               plan: Mapping[str, object] = TRAINING_PLAN, target: float = 0.005,
               predict: Callable[..., np.ndarray] | None = None) -> dict:
    """Score the saved models on the test split, once, for every food group that has models.

    Per group: each seed on its own (the spread), then the seeds averaged (the model the app would use).
    The spoiled threshold is chosen on the validation split (choose_spoiled_threshold) and only then
    applied to the test split. Predictions are saved (results_dir/predictions_<group>.parquet), so running
    it again reads them back instead of scoring the photos again; the summary goes to results_dir/final_test.json.

    Args:
        index: Images with path, group, state and split (the split the models were trained on).
        model_dir: Where the models are (freshness_<group>_seed<seed>.pt).
        results_dir: Where the predictions and the summary are saved.
        plan: TRAINING_PLAN (image size).
        target: The most spoiled_called_fresh the threshold allows on the validation split.
        predict: The scoring function (predict_states; the tests pass a fake one).

    Returns:
        {group: {"seeds", "threshold", "test_without_threshold", "test", "by_source"}}.
    """
    predict = predict or predict_states
    model_dir, results_dir = Path(model_dir), Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    summary: dict = {}
    for group in sorted(index["group"].dropna().unique()):
        model_paths = sorted(model_dir.glob(f"freshness_{group}_seed*.pt"))
        if not model_paths:
            continue
        seeds = [int(path.stem.rsplit("seed", 1)[1]) for path in model_paths]
        rows = index[(index["group"] == group) & index["state"].notna() & index["split"].isin(["val", "test"])]
        rows = rows.reset_index(drop=True)
        saved = results_dir / f"predictions_{group}.parquet"
        columns = [f"seed{seed}_{state}" for seed in seeds for state in STATES]
        cached = pd.read_parquet(saved) if saved.exists() else None
        if cached is not None and set(columns) <= set(cached.columns) and cached["path"].tolist() == rows["path"].tolist():
            scores = cached
        else:
            probabilities = predict(rows["path"].tolist(), model_paths, plan)
            scores = rows[["path", "source", "split", "state"]].copy()
            for m, seed in enumerate(seeds):
                for k, state in enumerate(STATES):
                    scores[f"seed{seed}_{state}"] = probabilities[m, :, k]
            scores.to_parquet(saved, index=False)

        def probs(split: str, seed: int | None = None, scores: pd.DataFrame = scores,
                  seeds: list[int] = seeds) -> np.ndarray:
            """The probabilities of one seed, or of all seeds averaged, on one split."""
            part = scores[scores["split"] == split]
            chosen = [seed] if seed is not None else seeds
            return np.mean([part[[f"seed{s}_{state}" for state in STATES]].to_numpy() for s in chosen], axis=0)

        val_true = scores.loc[scores["split"] == "val", "state"].tolist()
        test = scores[scores["split"] == "test"]
        threshold = choose_spoiled_threshold(val_true, probs("val"), target)
        predicted = apply_spoiled_threshold(probs("test"), threshold)
        by_source = {source: detailed_scores(test.loc[part, "state"].tolist(),
                                             [predicted[i] for i in np.flatnonzero(part.to_numpy())])
                     for source, part in ((s, test["source"] == s) for s in sorted(test["source"].unique()))}
        summary[group] = {
            "seeds": {seed: selection_score(test["state"], apply_spoiled_threshold(probs("test", seed)))
                      for seed in seeds},
            "threshold": threshold,
            "test_without_threshold": detailed_scores(test["state"].tolist(), apply_spoiled_threshold(probs("test"))),
            "test": detailed_scores(test["state"].tolist(), predicted),
            "by_source": by_source,
        }
    (results_dir / "final_test.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return summary
