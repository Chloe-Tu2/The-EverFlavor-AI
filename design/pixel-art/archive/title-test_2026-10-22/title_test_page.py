"""Test page: where should the title go on the traced kitchens? (design work only, not part of the app)

Three layouts, on any kitchen, on a computer and on a phone:
  - On the painted sign: the title is written onto the sign in the picture and moves and scales with it.
  - Separate board: the title is its own wooden board at the top of the page, as in the app today.
  - Auto: the painted sign on wide screens, the separate board on narrow ones (phones crop the picture's sides).
  - Sign centred on phones: the painted sign everywhere; on narrow screens the picture slides sideways so the sign
    is in the middle (the rest of the kitchen moves off screen instead).

    python -m streamlit run design/pixel-art/title_test_page.py --server.port 8502
    (on a phone on the same Wi-Fi: open the Network URL Streamlit prints)

The kitchen is drawn like the app's background (cover, anchored at the bottom centre), so the crop is the same.
"""
from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

TRACED = Path(__file__).resolve().parent / "drafts" / "traced-kitchens"
ORIGINAL = (1672, 941)                       # the team's originals; the sign boxes below are measured on them
SIGNS = {                                    # the empty part of each kitchen's sign: (x0, y0, x1, y1)
    "chinese": (700, 195, 1165, 295),
    "mediterranean": (700, 205, 1050, 280),
    "mexican": (620, 140, 1010, 218),
    "middle_eastern": (610, 72, 1010, 175),
}
LAYOUTS = ["On the painted sign", "Separate board", "Auto (sign on wide screens, board on phones)",
           "Sign centred on phones"]


def picture(kitchen: str) -> str:
    return "data:image/png;base64," + base64.b64encode((TRACED / kitchen / f"{kitchen}.png").read_bytes()).decode()


st.set_page_config(page_title="Title test", layout="wide")
params = st.query_params
with st.sidebar:
    st.subheader("Title test")
    kitchens = list(SIGNS)
    kitchen = st.selectbox("Kitchen", kitchens, index=kitchens.index(params.get("kitchen", "chinese")),
                           format_func=lambda k: k.replace("_", " ").title())
    layout = st.radio("Title layout", LAYOUTS, index=int(params.get("layout", 0)))
    outline = st.checkbox("Outline the sign's box", value=params.get("outline") == "1")
    st.caption("Resize the window, or open the page on a phone, to see how the crop changes.")

x0, y0, x1, y1 = SIGNS[kitchen]
W, H = ORIGINAL
mode = LAYOUTS.index(layout)
on_sign = "none" if mode == 1 else "block"
board = "inline-block" if mode == 1 else "none"
box_w = f"max(100vw, calc(100vh * {W / H:.5f}))"
narrow = ""                                  # what changes on narrow screens (phones held upright)
if mode == 2:
    narrow = ".sign { display: none; } .board { display: inline-block; }"
elif mode == 3:                              # slide the picture so the sign's centre is the middle of the screen
    narrow = f".kitchen {{ transform: none; left: calc(50vw - {box_w} * {(x0 + x1) / 2 / W:.4f}); }}"
st.html(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Jersey+10&display=swap');
.stApp {{ background: #3B2A20; }}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stMain"] {{ position: relative; z-index: 1; }}
/* the kitchen: covers the window, anchored at the bottom centre, like the app's background */
.kitchen {{ position: fixed; left: 50%; bottom: 0; transform: translateX(-50%); z-index: 0; pointer-events: none;
  width: {box_w}; height: max(100vh, calc(100vw / {W / H:.5f})); }}
.kitchen img {{ width: 100%; height: 100%; image-rendering: pixelated; display: block; }}
.sign {{ position: absolute; left: {x0 / W * 100:.3f}%; top: {y0 / H * 100:.3f}%; width: {(x1 - x0) / W * 100:.3f}%;
  height: {(y1 - y0) / H * 100:.3f}%; container-type: size; display: {on_sign};
  outline: {'2px dashed #00E5FF' if outline else 'none'}; }}
.sign span {{ position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  font-family: 'Jersey 10', monospace; font-size: min(62cqh, 13cqw, 9vw); color: #4A2511; white-space: nowrap;
  text-shadow: 1px 1px 0 #F7E3B5; }}
.board {{ display: {board}; position: relative; z-index: 1; font-family: 'Jersey 10', monospace; font-size: 2.6rem; color: #4A2511;
  background: #FBF3E4; border: 4px solid #6B4A2F; box-shadow: 6px 6px 0 rgba(0,0,0,.35); padding: .2rem 1.1rem;
  margin: 0 0 .5rem; }}
@media (max-aspect-ratio: 1/1) {{ {narrow} }}
.spacer {{ height: 30vh; }}
</style>
<div class="kitchen"><img src="{picture(kitchen)}" alt=""><div class="sign"><span>EverFlavor Kitchen</span></div></div>
<div class="board">EverFlavor Kitchen</div>
<div class="spacer"></div>
""")
st.markdown("""<style>                     /* page-wide styles (st.html keeps its styles to its own block) */
[data-testid="stHeader"] { background: transparent; }
.st-key-tools { background: rgba(251,243,228,.96); border: 4px solid #6B4A2F; box-shadow: 8px 8px 0 rgba(0,0,0,.35);
  padding: .75rem 1.5rem 1.5rem; max-width: 760px; position: relative; z-index: 1; }
</style>""", unsafe_allow_html=True)

tools = st.container(key="tools")
find, check = tools.tabs(["Find recipes", "Check my recipe"])
with find:
    st.text_input("Ingredients you have", "chicken, rice, peppers")
    st.multiselect("Avoid", ["Peanuts", "Shellfish", "Pork", "Gluten"], ["Peanuts"])
    st.button("Find recipes")
with check:
    st.text_area("Paste a recipe", "2 cups flour\n1 egg\n...")
