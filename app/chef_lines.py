"""What the pixel chef says: greetings, small talk and quotes for each kitchen.

The chef only reads out what the back end decided (src/everflavor). These lines are small talk around that:
a welcome in the region's language, a few well-known dishes, common cooking tips and real quotes. None of them
is safety, health or medical advice, and none of them judges a recipe; that stays with the back end.

Every native phrase and every quote has its source in SOURCES (checked 2026-10-24). Add a line only with a
source; leave a quote out when its wording or speaker cannot be checked.

    greeting("Chinese")   # '欢迎 (huānyíng) — "welcome"! I'm your Chinese kitchen chef.'
    line("Mexican", 7)    # one general, regional or quote line; the same seed always gives the same line
"""
import zlib
from typing import NamedTuple


class Phrase(NamedTuple):
    """A phrase in the region's language: as written, how to say it, what it means, and the language."""
    native: str
    say: str
    meaning: str
    language: str


class Quote(NamedTuple):
    """A real quote: the words, who said them and where (the URL is in SOURCES)."""
    text: str
    speaker: str
    where: str


# The kitchens in app/app.py (THEMES); a kitchen not listed here gets Classic's lines
KITCHENS = ["Classic", "Chinese", "Japanese", "Mediterranean", "Mexican", "Middle Eastern", "Moroccan"]

# Lines any chef can say while idle or welcoming: common kitchen know-how, no health or safety claims
GENERAL = [
    "Taste as you go: a pinch at a time is easier to fix than a spoonful.",
    "Let meat rest a few minutes before slicing, so the juices stay inside.",
    "Read the whole recipe before you start. No surprises halfway through!",
    "Chop and measure everything first. Chefs call it mise en place: everything in its place.",
    "Pat meat or tofu dry before searing for a better golden crust.",
    "Don't crowd the pan: food browns better with a little room.",
    "Toast whole spices in a dry pan for a minute to wake up their smell.",
    "A squeeze of lemon or a splash of vinegar at the end can brighten a whole dish.",
    "Save a cup of pasta water: its starch helps the sauce cling.",
    "Clean as you go, and the kitchen is ready when the food is.",
]

# Per kitchen: greetings (the first is the main one), meal phrases and dishes the region is known for.
# Dishes are well-documented regional classics, said as facts about food, not about people.
REGIONAL: dict[str, dict[str, list[Phrase] | list[str]]] = {
    "Classic": {
        "greetings": [],
        "meal": [],
        "dishes": [
            "Barbecue in the American South comes in many styles: Carolina, Memphis, Kansas City and Texas.",
            "Louisiana gumbo starts with a roux and the 'holy trinity' of onion, celery and bell pepper.",
            "Tex-Mex grew up in Texas, where Mexican and American cooking met: think chili con carne and fajitas.",
            "New England clam chowder is the creamy one; Manhattan clam chowder is the red, tomato one.",
            "Apple pie is a classic American dessert, often served with a scoop of ice cream.",
        ],
    },
    "Chinese": {
        "greetings": [
            Phrase("欢迎", "huānyíng", "welcome", "Mandarin Chinese"),
            Phrase("你好", "nǐ hǎo", "hello", "Mandarin Chinese"),
        ],
        "meal": [Phrase("请慢用", "qǐng mànyòng", "please enjoy your meal", "Mandarin Chinese")],
        "dishes": [
            "Mapo tofu comes from Sichuan: soft tofu in a spicy sauce with numbing Sichuan pepper.",
            "Dim sum is a Cantonese tradition of small dishes shared over tea, called yum cha.",
            "Peking duck, from Beijing, is served with thin pancakes, scallions and sweet bean sauce.",
            "Xiaolongbao, the soup dumplings, are a classic of Shanghai and the nearby Jiangnan region.",
            "In northern China, families often fold jiaozi dumplings together for the Lunar New Year.",
        ],
    },
    "Japanese": {
        "greetings": [Phrase("いらっしゃいませ", "irasshaimase", "welcome (what shops and restaurants say)",
                             "Japanese")],
        "meal": [Phrase("いただきます", "itadakimasu", "I humbly receive (said before eating)", "Japanese")],
        "dishes": [
            "Sushi is about the rice: seasoned with vinegar, then topped or rolled with fish or vegetables.",
            "Ramen changes by region: rich tonkotsu pork broth in Fukuoka, miso ramen in Sapporo.",
            "Tempura is seafood and vegetables in a very light, crisp batter.",
            "Dashi, a broth of kombu seaweed and bonito flakes, is the base of miso soup.",
            "Okonomiyaki, a savory pancake, has two famous styles: Osaka and Hiroshima.",
        ],
    },
    "Mediterranean": {
        "greetings": [
            Phrase("Benvenuti!", "ben-veh-NOO-tee", "welcome (to a group)", "Italian"),
            Phrase("Καλώς ήρθατε", "kalós írthate", "welcome (polite or to a group)", "Greek"),
            Phrase("¡Bienvenidos!", "bee-en-veh-NEE-dohs", "welcome (to a group)", "Spanish"),
        ],
        "meal": [
            Phrase("Buon appetito!", "bwon ap-peh-TEE-toh", "enjoy your meal (literally 'good appetite')",
                   "Italian"),
            Phrase("Καλή όρεξη!", "kalí órexi", "enjoy your meal", "Greek"),
            Phrase("¡Que aproveche!", "keh ah-proh-VEH-cheh", "enjoy your meal", "Spanish"),
            Phrase("Bon appétit !", "bon ah-pay-TEE", "enjoy your meal (literally 'good appetite')", "French"),
        ],
        "dishes": [
            "Italy's pasta is regional: carbonara and cacio e pepe in Rome, pesto in Genoa, ragù in Bologna.",
            "The art of the Neapolitan pizza maker is on UNESCO's list of intangible cultural heritage.",
            "Greek moussaka layers eggplant, a spiced meat sauce and a creamy béchamel on top.",
            "Paella comes from Valencia in Spain and is cooked in a wide, shallow pan.",
            "Gazpacho, from Andalusia in southern Spain, is a tomato soup served cold.",
        ],
    },
    "Mexican": {
        "greetings": [Phrase("¡Bienvenidos!", "bee-en-veh-NEE-dohs", "welcome (to a group)", "Spanish")],
        "meal": [Phrase("¡Buen provecho!", "bwen proh-VEH-choh", "enjoy your meal", "Spanish")],
        "dishes": [
            "Mole is a slow-cooked sauce of chilies and spices; Oaxaca and Puebla are its most famous homes.",
            "Tacos al pastor grew from the spit-roasted shawarma that Lebanese immigrants brought to Mexico.",
            "Corn for tortillas is cooked with lime first (nixtamalization), an old Mesoamerican technique.",
            "Tamales are steamed in corn husks or banana leaves.",
            "Chiles en nogada, from Puebla, wear the green, white and red of the Mexican flag.",
            "Traditional Mexican cuisine is on UNESCO's list of intangible cultural heritage.",
        ],
    },
    "Middle Eastern": {
        "greetings": [Phrase("أهلاً وسهلاً", "ahlan wa sahlan", "welcome", "Arabic")],
        "meal": [Phrase("بالهنا والشفا", "bil-hana wish-shifa", "enjoy your meal", "Egyptian Arabic")],
        "dishes": [
            "Hummus is chickpeas blended with tahini, lemon and garlic.",
            "Tabbouleh, from the Levant, is mostly parsley, with bulgur, tomato, lemon and olive oil.",
            "Kibbeh is bulgur and minced meat, shaped and then fried or baked.",
            "Mansaf, Jordan's national dish, is lamb cooked in a sauce of jameed (dried yogurt) over rice.",
            "Mezze are many small dishes put on the table to share.",
            "Koshari, a favorite in Egypt, mixes rice, lentils and pasta with a tomato sauce and crispy onions.",
        ],
    },
    "Moroccan": {
        "greetings": [
            Phrase("مرحبا", "marhba", "welcome", "Moroccan Arabic (Darija)"),
            Phrase("أهلاً وسهلاً", "ahlan wa sahlan", "welcome", "Arabic"),
        ],
        "meal": [],
        "dishes": [
            "A tagine is named after the clay pot it cooks in, with its tall, cone-shaped lid.",
            "In many Moroccan homes, couscous is the big family meal on Friday.",
            "Couscous traditions of the Maghreb are on UNESCO's list of intangible cultural heritage.",
            "Harira, a tomato, lentil and chickpea soup, is a favorite to break the fast in Ramadan.",
            "Pastilla (bastilla) is a flaky pie that mixes savory and sweet, dusted with cinnamon and sugar.",
            "Mint tea is poured from high above the glass to give it a little foam.",
        ],
    },
}

# Real quotes by chefs and food writers, each checked in SOURCES (Wikiquote with its citation, or the interview)
QUOTES = [
    Quote("No one is born a great cook, one learns by doing.", "Julia Child", "My Life in France (2006), ch. 3"),
    Quote("One of the secrets, and pleasures, of cooking is to learn to correct something if it goes awry; and one "
          "of the lessons is to grin and bear it if it cannot be fixed.", "Julia Child",
          "My Life in France (2006), ch. 6"),
    Quote("Learn how to cook -- try new recipes, learn from your mistakes, be fearless, and above all have fun!",
          "Julia Child", "My Life in France (2006), ch. 9"),
    Quote("Usually one's cooking is better than one thinks it is.", "Julia Child", "My Life in France (2006), ch. 2"),
    Quote("A cookbook is only as good as its worst recipe.", "Julia Child",
          "quoted in her New York Times obituary (2004)"),
    Quote("Find out how other people live and eat and cook. Learn from them – wherever you go.", "Anthony Bourdain",
          "Medium Raw (2010)"),
    Quote("Meals make the society, hold the fabric together in lots of ways that were charming and interesting "
          "and intoxicating to me.", "Anthony Bourdain", "interview with BookPage"),
    Quote("The discovery of a new dish does more for the happiness of mankind, than the discovery of a new planet.",
          "Jean Anthelme Brillat-Savarin", "The Physiology of Taste (1825), aphorism 9, tr. L. F. Simpson"),
    Quote("The family meal is the nursery of democracy.", "Michael Pollan", "The Guardian (25 May 2013)"),
    Quote("Cooking is an act of love.", "Massimo Bottura",
          "NUVO Magazine Q&A (2016), on the lesson his mother taught him"),
]

# Where each phrase and quote was checked
SOURCES = {
    "欢迎": "https://en.wiktionary.org/wiki/歡迎",
    "你好": "https://en.wiktionary.org/wiki/你好",
    "请慢用": "https://en.wiktionary.org/wiki/慢用",
    "いらっしゃいませ": "https://en.wiktionary.org/wiki/いらっしゃいませ",
    "いただきます": "https://en.wiktionary.org/wiki/いただきます",
    "Benvenuti!": "https://en.wiktionary.org/wiki/benvenuto",
    "Buon appetito!": "https://en.wiktionary.org/wiki/buon_appetito",
    "Καλώς ήρθατε": "https://en.wiktionary.org/wiki/καλώς_ήρθατε",
    "Καλή όρεξη!": "https://en.wiktionary.org/wiki/καλή_όρεξη",
    "¡Bienvenidos!": "https://en.wiktionary.org/wiki/bienvenido",
    "¡Buen provecho!": "https://en.wiktionary.org/wiki/buen_provecho",
    "¡Que aproveche!": "https://en.wiktionary.org/wiki/buen_provecho",   # listed there as a synonym
    "Bon appétit !": "https://en.wiktionary.org/wiki/bon_appétit",
    "أهلاً وسهلاً": "https://en.wiktionary.org/wiki/أهلا_وسهلا",
    "بالهنا والشفا": "https://en.wiktionary.org/wiki/بالهنا_والشفا",
    "مرحبا": "https://en.wiktionary.org/wiki/مرحبا",   # the Moroccan Arabic section: marḥba, "welcome"
    "Julia Child": "https://en.wikiquote.org/wiki/Julia_Child",
    "Anthony Bourdain": "https://en.wikiquote.org/wiki/Anthony_Bourdain",
    "Jean Anthelme Brillat-Savarin": "https://en.wikiquote.org/wiki/Jean_Anthelme_Brillat-Savarin",
    "Michael Pollan": "https://en.wikiquote.org/wiki/Michael_Pollan",
    "Massimo Bottura": "https://nuvomagazine.com/palate/qa-chef-massimo-bottura",
}


def _lines(kitchen: str, key: str) -> list:
    """One part ("greetings", "meal" or "dishes") of a kitchen's lines; unknown kitchens use Classic's."""
    return list(REGIONAL.get(kitchen, REGIONAL["Classic"])[key])


def greeting(kitchen: str) -> str:
    """The chef's hello: the region's welcome with how to say it and what it means, then who the chef is."""
    name = kitchen if kitchen in REGIONAL else "Classic"
    greetings: list[Phrase] = _lines(name, "greetings")
    if not greetings:
        return f"Welcome to the kitchen! I'm your {name} kitchen chef."
    first = greetings[0]
    return f'{first.native} ({first.say}) — "{first.meaning}"! I\'m your {name} kitchen chef.'


def _say(phrase: Phrase) -> str:
    """A phrase as a sentence the chef can say."""
    return f'In {phrase.language}, {phrase.native} ({phrase.say}) means "{phrase.meaning}".'


def line(kitchen: str, seed: int | str) -> str:
    """One general, regional or quote line, picked by the seed: the same seed always gives the same line, so a
    Streamlit rerun does not make the chef change what he says. A text seed is hashed with crc32 (stable across
    runs, unlike hash())."""
    pool = (GENERAL + _lines(kitchen, "dishes")
            + [_say(phrase) for phrase in _lines(kitchen, "greetings")[1:] + _lines(kitchen, "meal")]
            + [f'"{quote.text}" — {quote.speaker}, {quote.where}' for quote in QUOTES])
    number = zlib.crc32(seed.encode("utf-8")) if isinstance(seed, str) else seed
    return pool[number % len(pool)]
