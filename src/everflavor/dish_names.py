"""The dish's own name, from a recipe title someone posted as their own.

Many titles carry the poster's words around the dish: a person's possessive ("Kittencal's Famous Lasagna"),
praise ("Best Ever"), diet and appliance tags ("Low Fat", "Crock Pot"), copycat notes ("Copycat Olive Garden"),
numbering ("#2") and "recipe". clean_title() takes them off and keeps the dish ("Lasagna"), with any alternate name
in parentheses as a gloss ("Bulgogi (Korean BBQ Beef)" -> "Bulgogi", "Korean BBQ Beef"). Real dish names with a
possessive stay ("Shepherd's Pie", "General Tso's Chicken", "Devil's Food Cake").

Rules only, measured in docs/plans/DISH_NAMES.md: on 150 hand-checked titles it did not see while being written,
84% exact and 92% acceptable (about 90% and 97% over all titles).

The dish name is for showing. The allergy and diet flags keep reading the original title (flags.name_text): a
removed "Gluten Free" or "(With Peanuts)" must never change a flag.
"""
from __future__ import annotations

import re

__all__ = ["clean_title"]

# Possessives that are part of real dish names; never removed.
KEEP_POSSESSIVE = {
    "shepherd", "shepherds", "tso", "tsos", "general tso", "devil", "devils", "angel", "angels",
    "hunter", "hunters", "fisherman", "fishermans", "baker", "bakers", "farmer", "farmers",
    "ploughman", "ploughmans", "cottage", "smith", "smiths", "granny", "pig", "pigs",
    "monkey", "monkeys", "children", "childrens", "king", "kings", "queen", "queens",
    "bishop", "bishops", "nun", "nuns", "poor man", "beggar", "beggars", "gypsy",
    "cowboy", "cowboys", "philly", "baker's", "miller", "millers", "lady", "ladys",
    "st", "saint", "president", "presidents", "pope", "popes", "sailor", "sailors",
    "mother-in-law", "boston", "carpenter", "carpenters", "dragon", "dragons",
    "robin", "kaiser", "emperor", "emperors", "fool", "fools", "cardinal",
}
KEEP_POSSESSIVE_PHRASES = [
    r"shepherd'?s pie", r"general tso'?s", r"devil'?s food", r"angel'?s food", r"hunter'?s",
    r"ploughman'?s", r"fisherman'?s", r"granny smith", r"pig'?s in (a )?blanket", r"st\.? patrick'?s",
    r"valentine'?s", r"new year'?s", r"mother'?s day", r"father'?s day", r"president'?s day",
    r"reese'?s", r"hershey'?s", r"m&m'?s", r"kellogg'?s", r"hellmann'?s", r"campbell'?s",
    r"lawry'?s", r"french'?s", r"bush'?s", r"dunkin'?s?", r"wendy'?s", r"arby'?s", r"chili'?s",
    r"denny'?s", r"mcdonald'?s", r"applebee'?s", r"carrabba'?s", r"bj'?s", r"famous dave'?s",
    r"kraft", r"smucker'?s", r"welch'?s", r"baker'?s chocolate", r"nestle'?s", r"land o'? lakes",
    r"mrs\.? dash", r"poor man'?s", r"beggar'?s purse", r"bishop'?s bread", r"nun'?s puffs",
    r"pope'?s nose", r"lady'?s? fingers?", r"lion'?s head", r"ants climbing", r"cat'?s tongue",
    r"bird'?s nest", r"devil'?s", r"angel'?s", r"monkey'?s", r"children'?s",
    r"\w+'s mores?\b", r"s'?mores?\b",
]
# Restaurants and brands seen after "copycat"/"like" (cleaned off the copycat phrase).
RESTAURANTS = (
    r"olive garden|red lobster|outback( steakhouse)?|cheesecake factory|p\.? ?f\.? chang'?s|"
    r"pf chang'?s|chick[- ]fil[- ]a|kfc|taco bell|panera( bread)?|starbucks|cracker barrel|"
    r"applebee'?s|chili'?s|tgi friday'?s|t\.?g\.?i\.? friday'?s|ruby tuesday|red robin|"
    r"texas roadhouse|longhorn( steakhouse)?|ihop|denny'?s|bob evans|boston market|"
    r"mcdonald'?s|wendy'?s|arby'?s|burger king|subway|chipotle|panda express|cinnabon|"
    r"auntie anne'?s|carrabba'?s|macaroni grill|romano'?s|bertucci'?s|houlihan'?s|"
    r"kentucky fried chicken|popeyes|long john silver'?s|white castle|sonic|dairy queen|"
    r"krispy kreme|dunkin'?( donuts)?|pizza hut|domino'?s|hard rock( cafe)?|rainforest cafe|"
    r"bahama breeze|claim jumper|marie callender'?s|mimi'?s cafe|black angus|benihana|"
    r"famous dave'?s|el torito|on the border|chi chi'?s|old spaghetti factory|"
    r"cheddar'?s|logan'?s( roadhouse)?|ruth'?s chris|disney( world| land)?|"
    r"jason'?s deli|zupa'?s|zoe'?s kitchen|pei wei|benihana|in[- ]n[- ]out|five guys"
)
FAMILY = (
    r"mom|moms|mommy|mama|mamma|mother|grandma|grandmas|granny|grammy|gramma|nana|nanna|"
    r"grandmother|grandpa|grandpas|grandfather|papa|pop|dad|daddy|aunt|auntie|aunty|"
    r"uncle|sister|brother|nonna|nonno|oma|opa|abuela|abuelita|bubbe|bubby|baba|yiayia|"
    r"mother-in-law|mil|hubby|husband|wife|son|daughter|kid|kids|family|"
    r"my|our|your|his|her|their"
)
PRAISE = (
    r"best|the best|best ever|world'?s best|famous|world famous|yummy|yummiest|easy|easiest|"
    r"super easy|very easy|amazing|ultimate|perfect|perfectly|awesome|delicious|deliciously|"
    r"tasty|scrumptious|wonderful|fabulous|fantastic|incredible|excellent|outstanding|"
    r"terrific|heavenly|divine|addictive|killer|to die for|out of this world|"
    r"simple(?! syrup)|simply|quick(?! ?breads?)|quick and easy|quick n easy|quick & easy|easy peasy|"
    r"super fast|really fast|"
    r"favorite|favourite|fav|famous|secret|award[- ]winning|prize[- ]winning|"
    r"blue ribbon|legendary|signature|classic|original|authentic|traditional|homemade|home made|"
    r"really good|so good|very good|incredibly|insanely|seriously|sinfully|"
    r"mouth[- ]watering|melt in your mouth|kicked[- ]up|kicked up|knock your socks off|"
    r"fool[- ]?proof|no[- ]fail|never fail|can'?t fail|unbelievable|yum|yum yum|wow|"
    r"crazy good|"
    r"lazy|lazy man'?s|lazy day|kid[- ]friendly|family[- ]friendly|company|everyday|weeknight|"
    r"5[- ]star|five[- ]star|restaurant[- ]style|restaurant[- ]quality|gourmet|fancy|"
    r"healthy|healthier|healthy-ish|guilt[- ]free|skinny|lighter|lite"
)
DIET = (
    r"ww|weight watchers|weight watcher'?s|ww friendly|ww points?|[0-9]+ points?|"
    r"low[- ]fat|lowfat|fat[- ]free|nonfat|non[- ]fat|reduced[- ]fat|low[- ]cal(orie)?|"
    r"low[- ]carb|lowcarb|no[- ]carb|keto|ketogenic|paleo|whole ?30|atkins|south beach|"
    r"gluten[- ]free|gf|dairy[- ]free|df|sugar[- ]free|sugarless|no sugar( added)?|"
    r"diabetic|diabetic[- ]friendly|low[- ]sodium|low salt|heart[- ]healthy|"
    r"clean eating|nut[- ]free|egg[- ]free|"
    r"oamc|once a month cooking|freezer[- ]friendly|"
    r"high[- ]protein|low[- ]gi|low[- ]glycemic|low fodmap|fodmap[- ]friendly"
)
# Appliance tags only; cooking techniques (grilled, fried, baked) are part of the dish.
METHOD = (
    r"crock[- ]?pot|crockpot|slow[- ]cooker|slowcooker|instant[- ]pot|instapot|"
    r"pressure[- ]cooker|air[- ]fryer|airfryer|microwave|microwaved|bread machine|abm|"
    r"bread maker|rice cooker|thermomix|"
    r"5[- ]ingredients?|3[- ]ingredients?|4[- ]ingredients?|"
    r"30[- ]minutes?|20[- ]minutes?|15[- ]minutes?|10[- ]minutes?"
)
# Only removed at the end of the title.
SUFFIX_JUNK = (
    r"recipes?!*|ii+|iii|iv|vi*|#\s*\d+|no\.?\s*\d+|\d+|version \d+|ver\.? \d+|take \d+|"
    r"revisited|redux|remix|my way|my version|my style|made easy|made healthy|"
    r"for two|for 2|for one|for 1|for a crowd|for a group|for kids|"
    r"makeover|lightened( up)?|light version|for the freezer|(?:serves|makes) \d+|"
    r"\w+ version|version|\w+'s way|\w+'s style"
)
SERIES = (
    r"meatless monday|dinner tonight|the food lab|cook the book|bake the book|seriously asian|"
    r"serious eats|sunday supper|a sandwich a day|the nasty bits|sugar rush|grilling|"
    r"healthy & delicious|recipe of the day|weeknight dinner|the vegan dish|"
    r"time to make the doughnuts|snacktime|staff picks?|seriously italian|"
    r"latin american cuisine|dinner tonight|sweet technique|gluten-free tuesday|"
    r"sunday brunch|cook the book|bread baking|french in a flash|the crisper whisperer|"
    r"in season|market scan|potluck|essentials"
)

_W = r"(?:^|(?<=[\s(\[\-,/]))"
_E = r"(?=$|[\s)\]\-,/!.:;])"


def normalise(title: str) -> str:
    """Straight apostrophes, single spaces, and Food.com's lost apostrophes put back ("garten s" -> "garten's")."""
    t = str(title).strip()
    t = t.replace("’", "'").replace("`", "'")
    t = re.sub(r"\s+", " ", t)
    # food.com lost apostrophes: "ina garten s chicken" -> "ina garten's chicken"
    t = re.sub(r"\b([A-Za-z]{2,}) s\b(?! ?$)", r"\1's", t)
    return t


AMBIG_RESTAURANTS = (
    r"chipotle|subway|sonic|disney( world| land)?|longhorn( steakhouse)?|outback( steakhouse)?|"
    r"black angus|on the border|romano'?s|cheddar'?s|logan'?s( roadhouse)?|hard rock( cafe)?|"
    r"five guys|white castle|boston market|kfc"
)
INTENS = r"(?:(?:fairly|very|really|super|pretty|so|truly|absolutely|amazingly|ridiculously|incredibly|simply|just) )?"
POINTS = r"(?:only )?\d+(?:[ .]\d+)? (?:ww |weight watchers? )?(?:pts?|points?(?:\+| plus)?)"
FREE = r"\w+[- ]free"


def _split_top(pattern: str) -> list[str]:
    """Split a regex alternation at the top level only (so groups stay whole)."""
    out: list[str] = []
    depth, cur, esc = 0, "", False
    for ch in pattern:
        if esc:
            cur += ch
            esc = False
            continue
        if ch == "\\":
            cur += ch
            esc = True
            continue
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "|" and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    return out


def _longest_first(pattern: str) -> str:
    return "|".join(sorted(set(_split_top(pattern)), key=len, reverse=True))


PRAISE_L = _longest_first(PRAISE + "|amazingly|deluxe|fun")
DIET_L = _longest_first(DIET)
METHOD_L = _longest_first(METHOD)
SUFFIX_L = _longest_first(SUFFIX_JUNK)
KEEP_RE = re.compile(r"\b(?:" + "|".join(KEEP_POSSESSIVE_PHRASES) + r")", re.IGNORECASE)


def _kept_at(work: str, pos: int) -> bool:
    """True when a protected phrase (Shepherd's Pie, New Year's, Reese's) covers position pos."""
    return any(m.start() <= pos < max(m.end(), m.start() + 1) for m in KEEP_RE.finditer(work))


POSS_RE = re.compile(r"\b((?:[A-Za-z][\w.\-]*\s){0,4}[A-Za-z][\w.\-]*)'s?\b(?=\s|$)", re.IGNORECASE)
POSS_S_RE = re.compile(r"\b([A-Za-z][\w.\-]*)s'\s", re.IGNORECASE)  # "the Smiths' stew"
TRAIL_WORDS = r"(?:way|style|version|recipe|favorite|favourite|special|best|own|take|twist|original|creation|specialty)"


def split_gloss(t: str) -> tuple[str, list[str]]:
    """Pull parenthesised alternate names out of the title."""
    parts = re.findall(r"\(([^()]*)\)|\[([^\[\]]*)\]", t)
    inner = [a or b for a, b in parts]
    rest = re.sub(r"\([^()]*\)|\[[^\[\]]*\]", " ", t)
    rest = re.sub(r"[()\[\]]", " ", rest)
    return rest, inner


def _strip(t: str, pattern: str) -> str:
    return re.sub(_W + INTENS + r"(?:" + pattern + r")" + _E, " ", t, flags=re.IGNORECASE)


def tidy(t: str) -> str:
    """Spaces, stray punctuation and dangling joining words (and, with, the) off both ends."""
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\s+([,.!?:;])", r"\1", t)
    t = re.sub(r"^[\s\-,:;/&!.*~|]+|[\s\-,:;/&!.*~|]+$", "", t)
    for _ in range(2):
        t = re.sub(r"^(?:and|or|with|w/|the|a|an|n|&|in|style|made|from|of|for|aka)\b\s*", "", t, flags=re.IGNORECASE)
        t = re.sub(r"\s*\b(?:and|or|with|w/|the|a|an|n|&|in|from|of|for|by|ala|a la|like|aka|no)$", "", t, flags=re.IGNORECASE)
        t = re.sub(r"^[\s\-,:;/&!.*~|]+|[\s\-,:;/&!.*~|]+$", "", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip(" -,:;/&!.|")


# A part in parentheses or after a dash that is a tag, not another name for the dish
GLOSS_WORDS = (r"copycat|copy cat|clone|.*\bversion\b.*|"
               r".*\bstyle\b.*|.*\bmethod\b.*|.*\brecipe\b.*|.*\bpoints?\b.*|"
               r"or .*|and .*|with .*|.*\bfriendly\b.*|.*\bfree\b.*|.*\bless\b.*|"
               r".*\bpot\b.*|.*\bcooker\b.*|.*\bmachine\b.*|.*\bminutes?\b.*|"
               r".*\bserv(es|ings?)\b.*|.*\bmakes?\b.*|.*\bpan\b.*|.*\bdough\b.*|"
               r"low .*|no .*|non.*|reduced.*|.*\bonly\b.*|.*\bvariation\b.*|.*\boptional\b.*")
GLOSS_JUNK = re.compile(f"^(?:{METHOD}|{DIET}|{PRAISE}|{SUFFIX_JUNK}|{POINTS}|{FREE}|{GLOSS_WORDS})$", re.IGNORECASE)


def clean_title(title: str) -> dict[str, object]:
    """Return dish_name, name_gloss, posted_title and the kinds of parts removed."""
    t = normalise(title)
    tags: list[str] = []
    rest, inner = split_gloss(t)
    gloss = [g.strip() for g in inner if g.strip() and not GLOSS_JUNK.match(g.strip())]
    if len(inner) > len(gloss):
        tags.append("paren")
    # "X aka Y": X is the dish, Y an alternate or a person's name
    m = re.match(r"^(.*?\S),?\s+(?:aka|a\.k\.a\.?|also known as)\s+(.+)$", rest, re.IGNORECASE)
    if m:
        rest = m.group(1)
        g0 = m.group(2)
        g = re.sub(r"\b\w+'s\b", lambda mm: mm.group(0) if _kept_at(g0, mm.start()) else " ", g0)
        g = tidy(_strip(g, PRAISE_L))
        if g and not GLOSS_JUNK.match(g):
            gloss.append(g)
        tags.append("aka")
    sm = re.match(r"^\s*(?:" + SERIES + r")\b[^:]*:\s*(.+)$", rest, re.IGNORECASE)
    if sm:
        rest = sm.group(1)
        tags.append("series")
    # dash, colon or bar suffix: "Bulgogi - Ww Friendly", "Raw Banana Fry | Vazhakkai Varuval"
    m = re.match(r"^(.*?\S)\s*(?:\s[-–—]+\s|:\s|\s\|\s)\s*(.*)$", rest)
    if m:
        right = m.group(2).strip()
        if GLOSS_JUNK.match(right) or re.search(r"\b(?:" + DIET + r"|" + METHOD + r")\b", right, re.IGNORECASE):
            rest = m.group(1)
            tags.append("dash_tag")
        elif "|" in rest[len(m.group(1)):len(m.group(1)) + 4]:
            rest = m.group(1)
            gloss.append(tidy(re.sub(r"\brecipes?\b", " ", right, flags=re.IGNORECASE)))
            tags.append("bar_gloss")
    work = rest
    personal = False
    # "Better Than Sex Cake" is a named dish; keep it. Otherwise "Better Than X's Y" -> Y
    if re.search(r"\bbetter than\b", work, re.IGNORECASE) and not re.search(
            r"better than (sex|anything|everything|s.x)\b", work, re.IGNORECASE):
        work = re.sub(r"\bbetter than (?:\w+'s|\w+ \w+'s|the restaurant'?s?|restaurant|takeout|(?:" + RESTAURANTS
                      + r")(?:'s)?|take[- ]out|store[- ]bought|the original|boxed|mom'?s|grandma'?s)",
                      " ", work, flags=re.IGNORECASE)
        tags.append("better_than")
    # copycat / restaurant
    copy = bool(re.search(r"\b(?:copy ?cat|clone|knock[- ]?off|imitation)\b", work, re.IGNORECASE))
    work = re.sub(r"\b(?:copy ?cat|clone|knock[- ]?off)\b", " ", work, flags=re.IGNORECASE)
    rest_pat = r"(?:" + RESTAURANTS + r")"
    ctx = r"(?:'s\b|\s+(?:style|inspired|version)\b)"
    found = False
    for pat in ([rest_pat] if copy else []) + [r"(?!(?:" + AMBIG_RESTAURANTS + r")\b)" + rest_pat,
                                                r"(?:" + AMBIG_RESTAURANTS + r")(?=" + ctx + r")"]:
        new = re.sub(r"\b(?:just |almost |tastes |taste )?(?:like |inspired by )?(?:the )?" + pat
                     + r"(?:'s)?(?: restaurant)?(?:'s)?(?: (?:style|inspired|version))?\b", " ", work, flags=re.IGNORECASE)
        if new != work:
            found = True
            work = new
    if copy or found:
        tags.append("copycat")
    # "Not Your Mama's", "Like Mom Used to Make"
    if re.search(r"\bnot (?:your|ur|yo)\b", work, re.IGNORECASE):
        work = re.sub(r"\bnot (?:your|ur|yo) (?:mama|mom|momma|mother|grandma|granny|nana|average|"
                      r"ordinary|typical|usual|regular|everyday|basic|run of the mill|plain|traditional)(?:'s|s)?\b",
                      " ", work, flags=re.IGNORECASE)
        tags.append("not_your")
        personal = True
    work = re.sub(r"\b(?:like|just like|the way) (?:mom|mother|mama|grandma|granny|nana|my mom|my mother|"
                  r"my grandma)(?:'s)? (?:used to make|made|makes|use to make)\b", " ", work, flags=re.IGNORECASE)
    work = re.sub(r"\b(?:that|which) (?:my|our) \w+ (?:loves?|likes?|adores?|requests?)\b", " ", work, flags=re.IGNORECASE)
    work = re.sub(r"\bby [A-Z]?\w+(?: [A-Z]\w+)?$", " ", work, flags=re.IGNORECASE)
    # possessives
    while True:
        changed = False
        for mo in POSS_RE.finditer(work):
            words = mo.group(1).split()
            last = words[-1]
            wstart = mo.start() + mo.group(0).rfind(last)
            if last.lower() in KEEP_POSSESSIVE or last.lower() in {"let", "it", "that", "what", "here", "there", "who", "he", "she"} \
                    or _kept_at(work, wstart):
                continue
            after = work[mo.end():]
            trailing = not tidy(re.sub(r"^\s*" + TRAIL_WORDS + r"\b", " ", after, flags=re.IGNORECASE))
            if trailing or work[:mo.start()].strip():
                # owner after the dish ("pumpkin pie kittencal's way"): drop the owner (and "X and")
                pre = work[:wstart]
                pre = re.sub(r"(?:\b\w+\s+(?:and|&)\s+)?(?:" + FAMILY + r")?\s*$", "", pre, flags=re.IGNORECASE)
                after = re.sub(r"^\s*" + TRAIL_WORDS + r"\b", " ", after, flags=re.IGNORECASE) if trailing else after
                work = pre + " " + after
            else:
                work = " " + after
            tags.append("possessive")
            personal = True
            changed = True
            break
        if not changed:
            break
    if POSS_S_RE.search(work):
        work = POSS_S_RE.sub(" ", work)
        tags.append("possessive")
        personal = True
    # family / "my" words without possessive
    if re.search(_W + r"(?:my|our|mom|moms|grandma|grandmas|granny|nana|aunt|auntie|mama|"
                 r"mother|grandmother|dad|uncle|nonna|abuela|hubby|family)" + _E, work, re.IGNORECASE):
        personal = True
        tags.append("family")
        work = re.sub(_W + r"(?:my|our|mom|moms|mommy|mama|mamma|grandma|grandmas|granny|grammy|nana|"
                      r"grandmother|aunt|auntie|aunty|uncle|nonna|abuela|abuelita|hubby|my husband|my wife|"
                      r"family)(?:'s)?" + _E + r"(?: (?:own|very own|old|favorite|favourite|special|secret|famous))?",
                      " ", work, flags=re.IGNORECASE)
    # suffix junk at the end only (numbering, "recipe", "for two", "version 2")
    for _ in range(4):
        new = re.sub(r"[\s,\-:!]+(?:" + SUFFIX_L + r")[\s!.]*$", " ", " " + work, flags=re.IGNORECASE)
        if new.strip() == work.strip() or not tidy(new):
            break
        work = new
        tags.append("suffix")
    for pat, tag in ((POINTS, "diet"), (PRAISE_L, "praise"), (DIET_L, "diet"), (FREE, "diet"), (METHOD_L, "method")):
        new = re.sub(POINTS, " ", work, flags=re.IGNORECASE) if pat is POINTS else _strip(work, pat)
        if new != work:
            tags.append(tag)
            if not tidy(new):
                continue  # keep the tag word when it is all there is ("Crock Pot")
            work = new
    work = re.sub(r"#\s*\d+", " ", work)
    work = re.sub(r"\b(?:recipes?)\b!*", " ", work, flags=re.IGNORECASE)
    dish = tidy(work)
    if not dish:
        dish = tidy(rest) or tidy(t)
        tags.append("fallback")
    if not any(c.isupper() for c in t):
        dish = dish.lower()
    return {"dish_name": dish, "name_gloss": "; ".join(g for g in gloss if g),
            "posted_title": personal, "tags": sorted(set(tags))}
