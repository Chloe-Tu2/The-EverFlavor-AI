"""Cuisine families (5.4.1) and country / region of origin from source labels (5.4.6)."""
from __future__ import annotations

from .parsing import parse_label_list

__all__ = [
    "CUISINE_FAMILIES",
    "CUISINE_MAP",
    "FAMILY_PRIORITY",
    "ORIGIN_LABELS",
    "cuisine_names",
    "map_cuisine",
    "origin_from_labels",
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
    "saudi arabian": ("Saudi Arabia", None), "armenia": ("Armenia", None), "azerbaijan": ("Azerbaijan", None),
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
    "japanese": ("Japan", None), "japan": ("Japan", None), "korean": ("South Korea", None),
    "korea": ("South Korea", None), "thai": ("Thailand", None), "thailand": ("Thailand", None),
    "vietnamese": ("Vietnam", None), "cambodian": ("Cambodia", None), "cambodia": ("Cambodia", None),
    "laotian": ("Laos", None), "laos": ("Laos", None), "malaysian": ("Malaysia", None),
    "indonesian": ("Indonesia", None), "filipino": ("Philippines", None),
    "indian": ("India", None), "india": ("India", None), "pakistani": ("Pakistan", None),
    "nepalese": ("Nepal", None), "bangladesh": ("Bangladesh", None), "afghanistan": ("Afghanistan", None),
    "australian": ("Australia", None), "new zealand": ("New Zealand", None),
}


def origin_from_labels(raw: object) -> tuple[str, str | None]:
    """Find the country (and region) a recipe comes from in its source labels.

    A label that names a region wins over a plain country label for the same
    recipe ("mexican" + "tex-mex" -> United States, Texas). Labels that point
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
    return (countries.pop(), regions.pop() if len(regions) == 1 else None)
