"""What's new: the notes the app's bell shows, newest first.

One entry per release, added at the top when the version changes (src/everflavor/__init__.py and CHANGELOG.md;
tests/test_version.py checks that the three agree). Write for the people who use the app: 1 to 3 short notes
starting "New:", "Changed:" or "Fixed:", plain words, no technical or security details (those go in CHANGELOG.md).
"""

UPDATES = [
    {"version": "0.5.1", "date": "2026-10-18", "notes": [
        ("New: the EverFlavor Kitchen. A pixel chef checks every recipe against what you can't eat, and the kitchen "
         "behind the page reacts when you tap it."),
        ("New: kitchens from around the world. Search Asian, European, Latin American or Middle Eastern recipes "
         "and the kitchen and its chef change with them (or pick a theme in Settings)."),
        "New: this bell. It rings when there is something new.",
    ]},
]
