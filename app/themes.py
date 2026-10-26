"""The kitchens' page colors (app/app.py). Kept apart from the page so tests/test_app_contrast.py can check
every pair of colors is readable (WCAG AA) without starting Streamlit."""

# The kitchens. "Classic" is Eva's cooking-game palette and the default. Each has its own kitchen picture (scene)
# and the colors of the page drawn over it. The time of day (Settings) is the kitchen's light, not a kitchen of its
# own: Classic's morning and night are the former Morning and Night themes (design/pixel-art/build_classic_scene.py).
THEMES = {
    "Classic": {"scene": "classic_hours", "panel": "#FFF8E7", "sidebar": "#FFF1E6", "border": "#8B4513",
                "text": "#4A2C2A", "heading": "#8B4513", "button": "#FFB6C1", "button_hover": "#FF8FAB",
                "shadow": "#D9A679", "bubble": "#FFFFFF"},
    # The cuisine kitchens, each with its own chef. Chinese, Mediterranean, Mexican and Middle Eastern are the v5
    # kitchens (traced from the team's art, four hours, design/pixel-art/build_scenes.py); Japanese and Moroccan the
    # code-drawn drafts (design/pixel-art/cuisine_kitchens.py)
    "Japanese": {"scene": "japanese", "chef": "ref_japanese_", "panel": "#FBF3E2", "sidebar": "#F3E6CC",
                 "border": "#5B3A29", "text": "#3A2A20", "heading": "#8E2C2C", "button": "#E9C46A",
                 "button_hover": "#D9AE4A", "shadow": "#C9A57A", "bubble": "#FFFDF7"},
    "Chinese": {"scene": "v5_chinese", "chef": "ref_chinese_", "panel": "#FBF5EA", "sidebar": "#F4E9D8",
                "border": "#7A2A22", "text": "#3A2420", "heading": "#B22D2D", "button": "#E9B44C",
                "button_hover": "#D99E30", "shadow": "#CDBFA6", "bubble": "#FFFDF7"},
    "Moroccan": {"scene": "moroccan", "chef": "moroccan_", "panel": "#FCF3E8", "sidebar": "#F6E2D2",
                 "border": "#7A4B22", "text": "#3B2418", "heading": "#1F6F5C", "button": "#E2B33C",
                 "button_hover": "#CF9E25", "shadow": "#D69068", "bubble": "#FFFDF6"},
    "Mediterranean": {"scene": "v5_mediterranean", "panel": "#FBF6EC", "sidebar": "#EFE6D6", "border": "#6B4A2F",
                      "text": "#3B2E22", "heading": "#4F6B2A", "button": "#D9A441", "button_hover": "#C48F2C",
                      "shadow": "#CDBDA3", "bubble": "#FFFFFF"},
    "Mexican": {"scene": "v5_mexican", "chef": "mexican_", "panel": "#FFF6E5", "sidebar": "#FCE8C8",
                "border": "#8C3B1F", "text": "#3B2218", "heading": "#1F5FA8", "button": "#F2A541",
                "button_hover": "#E08E22", "shadow": "#D88A3A", "bubble": "#FFFDF5"},
    "Middle Eastern": {"scene": "v5_middle_eastern", "chef": "ref_middle_eastern_", "panel": "#FBF3E4",
                       "sidebar": "#F3E2C2", "border": "#7A4B22", "text": "#3B2A1A", "heading": "#1E6F80",
                       "button": "#D9A830", "button_hover": "#C49420", "shadow": "#C9A46B", "bubble": "#FFFDF6"},
}
# The page's colors for the Classic kitchen at night (the former Night theme): easier on the eyes in the dark
NIGHT_COLORS = {"panel": "#2A2138", "sidebar": "#241C31", "border": "#FF8FAB", "text": "#F3E9F5", "heading": "#FFD98A",
                "button": "#FF8FAB", "button_hover": "#FF6F95", "shadow": "#120D1A", "bubble": "#3A2E4A"}
