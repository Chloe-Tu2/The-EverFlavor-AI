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
from collections.abc import Iterable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

from .progress import progress_bar

__all__ = [
    "AGE_PATTERNS",
    "ALLOWED_LICENCES",
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
    "index_images",
    "mendeley_download",
    "sample_weights",
    "selection_score",
    "split_without_leakage",
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
    request = urllib.request.Request(url, headers=DOWNLOAD_HEADERS)
    with urllib.request.urlopen(request, timeout=timeout) as response:   # https only, checked above
        return response.read()


def _download_to(url: str, target: Path, timeout: int, chunk: int = 2**20) -> Path:
    """Stream a URL to a file in 1 MB pieces (archives of several GB never sit in memory).

    The file is written under a temporary name first, so an interrupted download is
    never mistaken for a finished one.
    """
    if not url.startswith("https://"):
        raise ValueError(f"only https downloads are allowed: {url}")
    partial = target.with_name(target.name + ".part")
    request = urllib.request.Request(url, headers=DOWNLOAD_HEADERS)
    with urllib.request.urlopen(request, timeout=timeout) as response, open(partial, "wb") as out:
        while block := response.read(chunk):
            out.write(block)
    partial.replace(target)
    return target


# Only licenses that allow use with credit; anything else is refused before downloading
ALLOWED_LICENCES = {"CC BY 4.0", "CC BY 3.0", "CC0 1.0", "CC0"}


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
        PermissionError: When the dataset's license is not in ALLOWED_LICENCES.
    """
    folder = Path(folder)
    if (folder / "LICENSE.txt").exists() and not refresh:   # written last: the download finished
        return sorted(folder.iterdir())
    if not re.fullmatch(r"[a-z0-9]+", dataset_id):
        raise ValueError(f"not a Mendeley dataset ID: {dataset_id!r}")
    data = json.loads(_get_bytes(MENDELEY_API + dataset_id, 60))
    licence = (data.get("data_licence") or {}).get("short_name", "")
    if licence not in ALLOWED_LICENCES:
        raise PermissionError(f"Mendeley dataset {dataset_id} has license {licence!r}; not downloaded")
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
    credit = [data.get("name", dataset_id), f"{licence}: {(data.get('data_licence') or {}).get('url', '')}",
              f"https://doi.org/{(data.get('doi') or {}).get('id', '')}"]
    (folder / "LICENSE.txt").write_text("\n".join(credit) + "\n", encoding="utf-8")
    return sorted(folder.iterdir())


ZENODO_API = "https://zenodo.org/api/records/"
# Zenodo license ids that allow use with credit
ZENODO_LICENCES = {"cc-by-4.0", "cc-by-3.0", "cc0-1.0"}


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
        listing = subprocess.run(["unrar", "lb", str(archive)], capture_output=True, text=True, check=True).stdout
        unpack = ["unrar", "x", "-o+", str(archive), str(folder) + "/"]
    else:
        listing = subprocess.run([*tool, "-tf", str(archive)], capture_output=True, text=True, check=True).stdout
        unpack = [*tool, "-xf", str(archive), "-C", str(folder)]
    for member in listing.splitlines():
        if member.strip() and not (folder / member.strip()).resolve().is_relative_to(folder.resolve()):
            raise ValueError(f"unsafe path in {archive.name}: {member}")
    subprocess.run(unpack, check=True, capture_output=True)


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
        PermissionError: When the record's license is not in ZENODO_LICENCES.
    """
    folder = Path(folder)
    if (folder / "LICENSE.txt").exists() and not refresh:   # written last: the download finished
        return sorted(folder.iterdir())
    if not re.fullmatch(r"\d+", record_id):
        raise ValueError(f"not a Zenodo record number: {record_id!r}")
    data = json.loads(_get_bytes(ZENODO_API + record_id, 60))
    meta = data.get("metadata", {})
    licence = str((meta.get("license") or {}).get("id", "")).lower()
    if licence not in ZENODO_LICENCES:
        raise PermissionError(f"Zenodo record {record_id} has license {licence!r}; not downloaded")
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
    credit = [meta.get("title", record_id), f"{licence}: https://zenodo.org/records/{record_id}",
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
        for dup, sets in index.groupby("duplicate_group")["photo_set"]:
            first = find(str(sets.iloc[0]))
            for s in sets.iloc[1:]:
                parent[find(str(s))] = first
    groups = index["photo_set"].astype(str).map(find)
    cuts = np.cumsum(list(fractions.values()))

    def assign(group: str) -> str:
        u = int(hashlib.sha1(f"{seed}:{group}".encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
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
    "patience": 5,               # epochs without improvement before stopping
    "head_learning_rate": 1e-3,
    "finetune_learning_rate": 1e-4,
    "selection_metric": "spoiled_called_fresh (lower is better), then macro F1",
    "weights": "equal per source, then equal per state within a source",
    "seeds": [0, 1, 2],
}


def train_freshness_model(index: pd.DataFrame, group: str, out_dir: str | Path,
                          plan: Mapping[str, object] = TRAINING_PLAN, seed: int = 0) -> dict:
    """Fine-tune MobileNetV3 on one food group's `state`, with early stopping on the validation split.

    Phase 1 trains only the new last layer (the pretrained model frozen); phase 2
    fine-tunes the whole model with a lower learning rate. After every epoch the
    validation split is scored with selection_score and the best epoch is kept, not
    the last one. The test split is never read here: it is used once, at the very end.
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
    normalize = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    train_tf = transforms.Compose([transforms.RandomResizedCrop(size, scale=(0.7, 1.0)), transforms.RandomHorizontalFlip(),
                                   transforms.ColorJitter(0.2, 0.2, 0.2), transforms.ToTensor(), normalize])
    eval_tf = transforms.Compose([transforms.Resize(int(size * 1.14)), transforms.CenterCrop(size),
                                  transforms.ToTensor(), normalize])

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
    sampler = WeightedRandomSampler(torch.tensor(train["weight"].to_numpy(), dtype=torch.double), len(train))
    train_loader = DataLoader(Images(train, train_tf), batch_size=batch, sampler=sampler, num_workers=2)
    val_loader = DataLoader(Images(val, eval_tf), batch_size=batch, num_workers=2)
    device = "cuda" if torch.cuda.is_available() else "cpu"
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
    history, best, best_key, since_best = [], {}, (float("inf"), 0.0), 0
    phases = [("head", int(str(plan["head_only_epochs"])), float(str(plan["head_learning_rate"])), False),
              ("finetune", int(str(plan["max_finetune_epochs"])), float(str(plan["finetune_learning_rate"])), True)]
    epoch = 0
    for phase, epochs, rate, all_layers in phases:
        for name, param in model.named_parameters():
            param.requires_grad = all_layers or name.startswith("classifier")
        optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=rate)
        for _ in range(epochs):
            epoch += 1
            run_epoch(optimizer)
            scores = evaluate()
            history.append({"epoch": epoch, "phase": phase, **scores})
            key = (scores["spoiled_called_fresh"], -scores["macro_f1"])
            if key < best_key:
                best_key, best, since_best = key, {"epoch": epoch, **scores}, 0
                torch.save(model.state_dict(), out)
            else:
                since_best += 1
                if phase == "finetune" and since_best >= int(str(plan["patience"])):
                    break
    return {"group": group, "seed": seed, "best_epoch": best.get("epoch"),
            "val_scores": {k: v for k, v in best.items() if k != "epoch"}, "model_path": str(out), "history": history}
