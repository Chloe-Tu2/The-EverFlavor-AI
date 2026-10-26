"""Cuisine families (5.4.1), country / region of origin from source labels (5.4.6), and the broad areas
and name words that guide the country model (5.9)."""
from __future__ import annotations

import re
from collections.abc import Iterable, Sequence

import numpy as np

from .parsing import parse_label_list

__all__ = [
    "AREA_COUNTRIES",
    "AREA_LABELS",
    "CUISINE_FAMILIES",
    "CUISINE_MAP",
    "FAMILY_PRIORITY",
    "NAME_ORIGINS",
    "ORIGIN_LABELS",
    "area_countries",
    "area_mask",
    "best_in_area",
    "cuisine_names",
    "map_cuisine",
    "origin_areas",
    "origin_from_labels",
    "origin_from_name",
]


CUISINE_FAMILIES = {
    "Asian": [
        "asian", "south east asian", "southeast asian", "south east asia", "chinese", "china",
        "cantonese", "szechuan", "hunan", "beijing", "japanese", "japan", "korean", "korea",
        "south korean", "thai", "thailand", "vietnamese", "indian", "india", "indian subcontinent",
        "south asian", "pakistani", "nepalese", "bangladeshi", "sri lankan", "indonesian",
        "malaysian", "filipino", "cambodian", "laotian", "mongolian", "burmese", "singaporean",
        "taiwanese", "cambodia", "laos", "bangladesh", "afghan", "afghanistan",
    ],
    "European": [
        "european", "central europe", "eastern europe", "british", "british isles", "english",
        "irish", "scottish", "welsh", "nordic", "scandinavian", "scandinavia", "swedish",
        "norwegian", "norway", "danish", "finnish", "icelandic", "italian", "italy", "french",
        "france", "greek", "greece", "spanish", "spain", "portuguese", "misc.: portugal", "german",
        "dach countries", "austrian", "swiss", "belgian", "misc.: belgian", "dutch", "netherlands",
        "misc.: dutch", "polish", "russian", "ukrainian", "hungarian", "czech", "croatian",
        "slovakia", "mediterranean", "albania", "albanian", "denmark", "bulgaria",
        "bulgarian", "estonia", "estonian", "belgium", "austria", "andorra",
    ],
    "Latin American": [
        "latin american", "mexican", "mexico", "oaxacan", "baja", "caribbean", "jamaican", "cuban",
        "puerto rican", "central american", "misc.: central america", "costa rican", "guatemalan",
        "honduran", "south american", "south america", "brazilian", "brazil", "peruvian",
        "chilean", "colombian", "argentine", "argentina", "venezuelan", "venezuela", "ecuadorean",
        "uruguayan", "dominica", "colombia", "chile", "costa rica", "cuba", "barbados",
        "aruba", "bahamas", "cayman islands", "antigua and barbuda",
    ],
    "African": [
        "african", "africa", "north african", "west african", "south african", "moroccan",
        "algerian", "tunisian", "libyan", "egyptian", "ethiopian", "nigerian", "kenyan", "somali",
        "somalian", "sudanese", "congolese", "angolan", "namibian", "ghanaian", "senegalese",
        "botswana", "angola",
    ],
    "Middle Eastern": [
        "middle eastern", "middle east", "turkish", "lebanese", "syrian", "persian", "iranian",
        "iranian persian", "iraqi", "palestinian", "israeli", "jordanian", "saudi arabian",
        "yemeni", "emirati", "armenia", "armenian", "azerbaijan", "azerbaijani",
    ],
}
CUISINE_MAP = {name: family for family, names in CUISINE_FAMILIES.items() for name in names}

# A recipe can carry labels from more than one family (for example the
# Food.com tags 'african' and 'middle-eastern' on a Moroccan dish).
# The first family in this list wins. Smaller families come first so
# that a broad tag such as 'european' does not hide a more specific one.
FAMILY_PRIORITY = ["African", "Middle Eastern", "Latin American", "Asian", "European"]


def map_cuisine(raw_cuisine: object, substring_match: bool = True) -> str:
    """Map a recipe's raw cuisine labels to one of the five EverFlavor families.

    Each label is matched exactly against CUISINE_MAP (hyphens count as spaces,
    so the Food.com tag 'south-african' matches 'south african'). If nothing
    matches and `substring_match` is True, a known name inside a label also
    counts. When labels point to several families, FAMILY_PRIORITY decides.

    Args:
        raw_cuisine: The raw label(s): a single label, a list, or a list stored as text.
        substring_match: Allow the substring fallback (Food.com tags use exact matches only).

    Returns:
        "Asian", "European", "Latin American", "African", "Middle Eastern" or "Other".
    """
    labels = [label.replace("-", " ") for label in parse_label_list(raw_cuisine)]
    families = {CUISINE_MAP[label] for label in labels if label in CUISINE_MAP}
    if not families and substring_match:
        families = {family for label in labels
                    for key, family in CUISINE_MAP.items() if key in label}
    for family in FAMILY_PRIORITY:
        if family in families:
            return family
    return "Other"


def cuisine_names(raw: object) -> str:
    """Return the labels in `raw` that are known cuisine names, joined by ', '."""
    return ", ".join(l for l in parse_label_list(raw) if l.replace("-", " ") in CUISINE_MAP)


US, UK, CN, MX, CA = "United States", "United Kingdom", "China", "Mexico", "Canada"

# label (lowercase, hyphens as spaces) -> (country, region or None)
ORIGIN_LABELS = {
    # North America, with the regions the sources name
    "american": (US, None), "usa": (US, None), "united states": (US, None), "native american": (US, None),
    "cajun": (US, "Louisiana"), "creole": (US, "Louisiana"), "tex mex": (US, "Texas"),
    "southern united states": (US, "Southern US"), "soul": (US, "Southern US"),
    "southwestern united states": (US, "Southwestern US"), "northeastern united states": (US, "Northeastern US"),
    "midwestern": (US, "Midwestern US"), "californian": (US, "California"),
    "pacific northwest": (US, "Pacific Northwest"), "hawaiian": (US, "Hawaii"),
    "amish mennonite": (US, "Pennsylvania"), "pennsylvania dutch": (US, "Pennsylvania"),
    "canadian": (CA, None), "canada": (CA, None), "quebec": (CA, "Quebec"), "ontario": (CA, "Ontario"),
    "british columbian": (CA, "British Columbia"),
    "mexican": (MX, None), "mexico": (MX, None), "oaxacan": (MX, "Oaxaca"), "baja": (MX, "Baja California"),
    # Central and South America, Caribbean
    "guatemalan": ("Guatemala", None), "honduran": ("Honduras", None), "costa rican": ("Costa Rica", None),
    "costa rica": ("Costa Rica", None), "cuban": ("Cuba", None), "cuba": ("Cuba", None),
    "puerto rican": ("Puerto Rico", None), "jamaican": ("Jamaica", None), "dominica": ("Dominica", None),
    "barbados": ("Barbados", None), "aruba": ("Aruba", None), "cayman islands": ("Cayman Islands", None),
    "antigua and barbuda": ("Antigua and Barbuda", None),
    "brazilian": ("Brazil", None), "brazil": ("Brazil", None), "argentine": ("Argentina", None),
    "argentina": ("Argentina", None), "chilean": ("Chile", None), "chile": ("Chile", None),
    "peruvian": ("Peru", None), "colombian": ("Colombia", None), "colombia": ("Colombia", None),
    "venezuelan": ("Venezuela", None), "venezuela": ("Venezuela", None), "ecuadorean": ("Ecuador", None),
    "uruguayan": ("Uruguay", None),
    # Europe
    "italian": ("Italy", None), "italy": ("Italy", None), "french": ("France", None), "france": ("France", None),
    "spanish": ("Spain", None), "spain": ("Spain", None), "portuguese": ("Portugal", None),
    "misc.: portugal": ("Portugal", None), "greek": ("Greece", None), "greece": ("Greece", None),
    "german": ("Germany", None), "austrian": ("Austria", None), "austria": ("Austria", None),
    "swiss": ("Switzerland", None), "dutch": ("Netherlands", None), "misc.: dutch": ("Netherlands", None),
    "netherlands": ("Netherlands", None), "belgian": ("Belgium", None), "misc.: belgian": ("Belgium", None),
    "belgium": ("Belgium", None), "irish": ("Ireland", None), "british": (UK, None),
    "english": (UK, "England"), "scottish": (UK, "Scotland"), "welsh": (UK, "Wales"),
    "swedish": ("Sweden", None), "norwegian": ("Norway", None), "norway": ("Norway", None),
    "danish": ("Denmark", None), "denmark": ("Denmark", None), "finnish": ("Finland", None),
    "icelandic": ("Iceland", None), "polish": ("Poland", None), "russian": ("Russia", None),
    "ukrainian": ("Ukraine", None), "hungarian": ("Hungary", None), "czech": ("Czech Republic", None),
    "slovakia": ("Slovakia", None), "croatian": ("Croatia", None), "albania": ("Albania", None),
    "bulgaria": ("Bulgaria", None), "estonia": ("Estonia", None), "andorra": ("Andorra", None),
    # Middle East and North Africa
    "turkish": ("Turkey", None), "lebanese": ("Lebanon", None), "iranian persian": ("Iran", None),
    "iraqi": ("Iraq", None), "syrian": ("Syria", None), "palestinian": ("Palestine", None),
    "saudi arabian": ("Saudi Arabia", None), "persian": ("Iran", None), "iranian": ("Iran", None),
    "israeli": ("Israel", None), "yemeni": ("Yemen", None), "armenia": ("Armenia", None), "azerbaijan": ("Azerbaijan", None),
    "moroccan": ("Morocco", None), "egyptian": ("Egypt", None), "libyan": ("Libya", None),
    "tunisian": ("Tunisia", None), "algerian": ("Algeria", None),
    # Sub-Saharan Africa
    "ethiopian": ("Ethiopia", None), "nigerian": ("Nigeria", None), "south african": ("South Africa", None),
    "kenyan": ("Kenya", None), "sudanese": ("Sudan", None), "somalian": ("Somalia", None),
    "angolan": ("Angola", None), "angola": ("Angola", None), "congolese": ("Congo", None),
    "namibian": ("Namibia", None), "botswana": ("Botswana", None),
    # Asia and Oceania
    "chinese": (CN, None), "china": (CN, None), "szechuan": (CN, "Sichuan"), "cantonese": (CN, "Guangdong"),
    "hunan": (CN, "Hunan"), "beijing": (CN, "Beijing"), "mongolian": ("Mongolia", None),
    "taiwanese": ("Taiwan", None), "taiwan": ("Taiwan", None), "hong kong": (CN, "Hong Kong"),
    "japanese": ("Japan", None), "japan": ("Japan", None), "korean": ("South Korea", None),
    "south korean": ("South Korea", None), "singaporean": ("Singapore", None), "sri lankan": ("Sri Lanka", None),
    "korea": ("South Korea", None), "thai": ("Thailand", None), "thailand": ("Thailand", None),
    "vietnamese": ("Vietnam", None), "cambodian": ("Cambodia", None), "cambodia": ("Cambodia", None),
    "laotian": ("Laos", None), "laos": ("Laos", None), "malaysian": ("Malaysia", None),
    "indonesian": ("Indonesia", None), "filipino": ("Philippines", None),
    "indian": ("India", None), "india": ("India", None), "pakistani": ("Pakistan", None),
    "nepalese": ("Nepal", None), "bangladesh": ("Bangladesh", None), "afghanistan": ("Afghanistan", None),
    "australian": ("Australia", None), "new zealand": ("New Zealand", None),
}
# Regions that cover several states: a recipe that also names a state-level region (Louisiana with
# "southern united states") keeps the state-level one
BROAD_REGIONS = {"Southern US", "Southwestern US", "Northeastern US", "Midwestern US", "Pacific Northwest"}


def origin_from_labels(raw: object) -> tuple[str, str | None]:
    """Find the country (and region) a recipe comes from in its source labels.

    A label that names a region wins over a plain country label for the same
    recipe ("mexican" + "tex-mex" -> United States, Texas), and a state-level
    region over a broad one ("cajun" + "southern united states" -> Louisiana). Labels that point
    to different countries ("american" + "italian") are ambiguous.

    Args:
        raw: The source's labels: a single label, a list, or a list stored as text.

    Returns:
        (country, region), with region None when the source names none, or
        ("Unknown", None) when the labels name no single country.
    """
    matches = [ORIGIN_LABELS[label] for label in (l.replace("-", " ") for l in parse_label_list(raw))
               if label in ORIGIN_LABELS]
    regional = [m for m in matches if m[1] is not None]
    candidates = regional or matches
    countries = {country for country, _ in candidates}
    if len(countries) != 1:
        return ("Unknown", None)
    regions = {region for _, region in candidates if region is not None}
    if len(regions) > 1:
        regions -= BROAD_REGIONS
    return (countries.pop(), regions.pop() if len(regions) == 1 else None)


# ---------- broad areas (5.9): a label such as "caribbean" names no country, but it says where to look ----------
_CARIBBEAN = ("Cuba", "Jamaica", "Puerto Rico", "Dominica", "Barbados", "Aruba", "Cayman Islands",
              "Antigua and Barbuda", "Bahamas", "Dominican Republic", "Haiti", "Trinidad and Tobago")
_CENTRAL_AMERICA = ("Guatemala", "Honduras", "Costa Rica", "Belize", "El Salvador", "Nicaragua", "Panama")
_SOUTH_AMERICA = ("Brazil", "Argentina", "Chile", "Peru", "Colombia", "Venezuela", "Ecuador", "Uruguay",
                  "Bolivia", "Paraguay")
_SOUTHEAST_ASIA = ("Thailand", "Vietnam", "Philippines", "Indonesia", "Malaysia", "Cambodia", "Laos", "Singapore",
                   "Myanmar")
_SOUTH_ASIA = ("India", "Pakistan", "Nepal", "Bangladesh", "Sri Lanka", "Afghanistan", "Bhutan")
_EAST_ASIA = (CN, "Taiwan", "Japan", "South Korea", "Mongolia")
_MIDDLE_EAST = ("Lebanon", "Turkey", "Iran", "Iraq", "Syria", "Israel", "Palestine", "Jordan", "Saudi Arabia",
                "Yemen", "United Arab Emirates", "Egypt", "Armenia", "Azerbaijan")
_NORTH_AFRICA = ("Morocco", "Algeria", "Tunisia", "Libya", "Egypt")
_AFRICA = (*_NORTH_AFRICA, "Ethiopia", "Nigeria", "South Africa", "Kenya", "Sudan", "Somalia", "Angola", "Congo",
           "Namibia", "Botswana", "Ghana", "Senegal")
_BRITISH_ISLES = (UK, "Ireland")
_NORDIC = ("Sweden", "Norway", "Denmark", "Finland", "Iceland")
_CENTRAL_EUROPE = ("Germany", "Austria", "Switzerland", "Poland", "Czech Republic", "Slovakia", "Hungary")
_EASTERN_EUROPE = ("Russia", "Ukraine", "Poland", "Hungary", "Czech Republic", "Slovakia", "Bulgaria", "Croatia",
                   "Albania", "Estonia")
_MEDITERRANEAN = ("Italy", "Greece", "Spain", "France", "Portugal", "Turkey", "Lebanon", "Syria", "Israel",
                  "Palestine", "Egypt", "Morocco", "Algeria", "Tunisia", "Libya", "Croatia", "Albania")
_EUROPE = (*_BRITISH_ISLES, *_NORDIC, *_CENTRAL_EUROPE, *_EASTERN_EUROPE, "Italy", "Greece", "Spain", "France",
           "Portugal", "Netherlands", "Belgium", "Andorra")

# area -> the countries inside it (names as in ORIGIN_LABELS)
AREA_COUNTRIES: dict[str, frozenset[str]] = {
    "Caribbean": frozenset(_CARIBBEAN),
    "Central America": frozenset(_CENTRAL_AMERICA),
    "South America": frozenset(_SOUTH_AMERICA),
    "Latin America": frozenset((MX, *_CARIBBEAN, *_CENTRAL_AMERICA, *_SOUTH_AMERICA)),
    "Asia": frozenset((*_EAST_ASIA, *_SOUTHEAST_ASIA, *_SOUTH_ASIA)),
    "Southeast Asia": frozenset(_SOUTHEAST_ASIA),
    "Indian subcontinent": frozenset(_SOUTH_ASIA),
    "Middle East": frozenset(_MIDDLE_EAST),
    "North Africa": frozenset(_NORTH_AFRICA),
    "West Africa": frozenset(("Nigeria", "Ghana", "Senegal")),
    "Africa": frozenset(_AFRICA),
    "Mediterranean": frozenset(_MEDITERRANEAN),
    "Europe": frozenset(_EUROPE),
    "British Isles": frozenset(_BRITISH_ISLES),
    "Nordic": frozenset(_NORDIC),
    "Central Europe": frozenset(_CENTRAL_EUROPE),
    "DACH": frozenset(("Germany", "Austria", "Switzerland")),
    "Eastern Europe": frozenset(_EASTERN_EUROPE),
    "Australia and New Zealand": frozenset(("Australia", "New Zealand")),
}
# broad label (lowercase, hyphens as spaces) -> area. Labels such as "world" or "fusion" name no area.
AREA_LABELS = {
    "caribbean": "Caribbean", "central american": "Central America", "misc.: central america": "Central America",
    "south american": "South America", "south america": "South America", "latin american": "Latin America",
    "asian": "Asia", "south east asian": "Southeast Asia", "southeast asian": "Southeast Asia",
    "south east asia": "Southeast Asia", "indian subcontinent": "Indian subcontinent",
    "south asian": "Indian subcontinent", "middle eastern": "Middle East", "middle east": "Middle East",
    "north african": "North Africa", "west african": "West Africa", "african": "Africa", "africa": "Africa",
    "mediterranean": "Mediterranean", "european": "Europe", "british isles": "British Isles",
    "nordic": "Nordic", "scandinavian": "Nordic", "scandinavia": "Nordic", "central europe": "Central Europe",
    "dach countries": "DACH", "eastern europe": "Eastern Europe", "australia & nz": "Australia and New Zealand",
}


def origin_areas(raw: object) -> list[str]:
    """The broad areas named by a recipe's labels ("caribbean, central american" -> Caribbean, Central America).

    Takes a list, a list stored as text, or cuisine_raw's comma-joined labels.
    """
    labels = (part.strip().replace("-", " ") for label in parse_label_list(raw) for part in label.split(","))
    return sorted({AREA_LABELS[label] for label in labels if label in AREA_LABELS})


def area_countries(raw: object) -> frozenset[str] | None:
    """The countries a recipe may come from, by its broad labels: the union of its areas' countries.

    Returns None when the labels name no area (then any country is possible).
    """
    areas = origin_areas(raw)
    if not areas:
        return None
    return frozenset().union(*(AREA_COUNTRIES[area] for area in areas))


def area_mask(labels: Iterable[object], classes: Sequence[str]) -> np.ndarray:
    """True where a country (column) lies inside the recipe's (row's) broad area.

    Rows whose labels name no area allow every country. Rows whose area holds none of `classes` allow none, so the
    caller leaves those recipes Unknown instead of giving them the nearest big country (Caribbean -> Mexico).

    Args:
        labels: Each recipe's raw cuisine labels (cuisine_raw).
        classes: The countries the model knows, in its column order.

    Returns:
        A boolean array, one row per recipe and one column per country.
    """
    names = list(classes)
    cache: dict[str, list[bool]] = {}
    rows = []
    for raw in labels:
        key = str(raw)
        if key not in cache:
            allowed = area_countries(raw)
            cache[key] = [True] * len(names) if allowed is None else [c in allowed for c in names]
        rows.append(cache[key])
    return np.array(rows, dtype=bool).reshape(len(rows), len(names))


def best_in_area(proba: np.ndarray, classes: Sequence[str], mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The most likely allowed country of each recipe and its probability.

    The probability is not spread again over the allowed countries: a Caribbean recipe the model thinks is 80%
    Mexico and 15% Cuba gets Cuba at 0.15 (below the bar, so it stays Unknown), not Cuba at 1.0.

    Args:
        proba: The model's probabilities, one row per recipe, one column per country in `classes`.
        classes: The countries, in the model's column order.
        mask: From area_mask(), the same shape as proba.

    Returns:
        (countries, confidence); "Unknown" and 0.0 for rows where no country is allowed.
    """
    kept = np.where(mask, proba, 0.0)
    if len(kept) == 0:
        return np.zeros(0, dtype=object), np.zeros(0)
    best = kept.argmax(axis=1)
    any_allowed = mask.any(axis=1)
    countries = np.where(any_allowed, np.asarray(classes, dtype=object)[best], "Unknown")
    confidence = np.where(any_allowed, kept[np.arange(len(kept)), best], 0.0)
    return countries, confidence


# ---------- the recipe's own name (5.9.2): only words that are hard to misread ----------
# "jamaica" alone is left out: "agua de jamaica" is a Mexican hibiscus drink. "jerk" must be the whole word
# (not "jerky").
NAME_ORIGINS = [
    (re.compile(r"\bjamaican\b|\bjerk(?:ed)?\b", re.IGNORECASE), "Jamaica"),
    (re.compile(r"\btaiwan(?:ese)?\b", re.IGNORECASE), "Taiwan"),
]


def origin_from_name(name: object, labels: object = None) -> str:
    """The country a recipe's name says, or "Unknown".

    Used only for recipes whose source labels name no single country. When the labels name a broad area, the
    country must lie inside it ("jerk" on an "asian" recipe gives nothing). A name that matches two countries
    gives nothing.

    Args:
        name: The recipe's title (recipe_name).
        labels: Its raw cuisine labels (cuisine_raw), for the area check.

    Returns:
        A country from NAME_ORIGINS, or "Unknown".
    """
    text = str(name or "")
    found = {country for pattern, country in NAME_ORIGINS if pattern.search(text)}
    allowed = area_countries(labels)
    if allowed is not None:
        found &= allowed
    return found.pop() if len(found) == 1 else "Unknown"
