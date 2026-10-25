# Landing Page: Plan

What people see first when they open the app's link. A plan for the team to read and sign off; nothing is built
yet. Written 2026-10-24 (Claude, with med27-coder) on branch `release/0.5.2`. Planner entry:
[README.md](README.md) ("Later": hosting and a landing page).

## The goal

In five seconds a visitor should know three things: what EverFlavor does, that it is safe to try, and where to
click. One promise, one main button, no sign-up.

Today the first screen is the app itself (screenshots taken 2026-10-24 at 1366 x 768 and 400 x 860):

| What happens today | Why it matters |
|---|---|
| The sign says the promise ("Recipes that fit what you can eat, checked ingredient by ingredient.") | Good: keep it |
| The first thing to do is a form (profile in the sidebar, search box, "How many ideas?") | A form before any value loses people |
| On a phone the sidebar is hidden, but the chef says "Tell me what you can't eat in the sidebar" | Phone visitors never find the profile |
| The disclaimer is only in the footer, far below | Trust comes too late |
| The first visitor after a server start waits while about 290,000 recipes load | A blank wait on the very first visit |

## Who lands there

| Visitor | Arrives from | What they need to see first |
|---|---|---|
| **Students and home cooks** | A shared link, often on a phone | Something tasty and a button; no account |
| **People with allergies, or cooking for someone who has them** | A friend, a class, a search | That every recipe is checked against what they can't eat, and what the check cannot do |
| **People who follow a religious or ethical diet** (halal, kosher, Jain, vegetarian, vegan) | The same | "Halal-friendly ingredients", never "halal"; that the diet is respected |
| **Capstone reviewers** (ITAI 2277) | The project link in the report or slides | What it does, how it works, who built it, where the code and data are |

## Research in short

Common advice for a first screen, from landing-page guides and food apps (sources at the end):

| Practice | How we use it |
|---|---|
| One clear promise in the headline (offer, audience, outcome) | The headline and the one-line promise below |
| One primary action, worded like the promise (not "Submit") | "Find a safe recipe"; "How we check" is a quiet second link |
| Trust early, close to the button | The checking line and the "not medical advice" line sit right under the button |
| Show the real product, not stock photos | The pixel kitchen and the chef are the picture; one real catch from the checker |
| A short "how it works" (three steps) | Tell us, we check, you cook |
| Try it without sign-up | The app has no accounts; nothing is saved (`docs/ethics_privacy.md`) |
| Mobile first (design at about 375-400 px) | One column; the button visible without scrolling on a phone |
| The three-second test: show a stranger the page for three seconds, ask what it offers | Our check before sign-off (open question 6) |

## The sections, in order

Draft wording, for the team to change and sign off. Short lines, plain words; the chef's lines in the pixel font,
everything else in the body font.

### 1. Top: the sign and the promise (first screen)

| Part | Draft wording |
|---|---|
| Sign (headline) | **EverFlavor Kitchen** |
| One-line promise | Recipes that fit what you can eat, checked ingredient by ingredient. |
| Supporting line | Allergies, religious and ethical diets, calorie goals: tell the chef once, and every recipe is checked for you. |
| Primary button | **Find a safe recipe** (opens the app) |
| Secondary link | How we check |
| Trust line (under the button) | Free · No sign-up · Nothing you enter is saved · Not medical advice |

### 2. The chef's greeting (in the kitchen's own language)

The chef stands in the kitchen with a speech bubble, as in the app. The greeting comes from
`app/chef_lines.greeting()`, so the landing and the app say the same thing.

| Kitchen | Draft bubble |
|---|---|
| American base kitchen (0.5.3) | Welcome to the kitchen! I'm your American kitchen chef. Did you know Worcestershire sauce has fish in it? I check every recipe for catches like that. |
| Classic (until the American kitchen is ready) | Welcome to the kitchen! I'm your Classic kitchen chef. Did you know satay sauce is usually made with peanuts? Paste any recipe and I'll check it. |

The "catch" is a real hidden allergen the checker knows (README: hidden allergens review). One fixed line per
visit, not a random fact that could be wrong; the list of catches is reviewed by a team member like the chef's
other lines.

### 3. How it works (three steps)

| Step | Title | Draft wording |
|---|---|---|
| 1 | Tell the chef | Pick what you can't eat, the diet you follow and your calories per meal. It takes a few taps. |
| 2 | We check every ingredient | Each recipe is checked for allergens, hidden ones too (Worcestershire sauce has fish), and for your diet's rules. |
| 3 | Cook with confidence | You see only recipes that pass, with why each one fits you. Or paste your own recipe and we check it line by line. |

### 4. Trust and the disclaimer ("How we check")

The secondary link scrolls here. Same facts as the app's footer, said first instead of last.

| Line | Draft wording |
|---|---|
| What we check | About 290,000 recipes from open datasets, each checked ingredient by ingredient against allergen lists from the US, the EU and UK, Canada, Australia and New Zealand, Japan and South Korea. |
| Hidden ingredients | Ready-made ingredients like ranch dressing or chocolate chips are checked for what their labels declare. |
| Safety is decided in the code, not by the AI | The rules decide what is safe. The AI chef only explains; it can't change your rules. |
| Not medical advice | The checks read ingredient names and can miss things: a brand's recipe, cross-contact in a factory, an unusual spelling. With a serious allergy or a health condition, read the label and ask your doctor or dietitian. |
| Diet labels | "Halal-friendly ingredients" means nothing in the ingredients is forbidden. It is not a certification. |
| Your data | Nothing you enter is saved. No accounts, no cookies, no tracking. |

Numbers on this page come from the README of the latest full run and are re-checked at each release (the
CLAUDE.md rule). A fuller "How we check" page is planner item 0.6.0 #6; this section links to it once it exists.

### 5. The team

| Part | Draft wording |
|---|---|
| Title | Made by Team EverGlow |
| Line | A student capstone project (ITAI 2277). |
| People | The contributors' GitHub names, from the same `CONTRIBUTORS` list as the app's footer (Chloe-Tu2, Evaabou20, med27-coder); whether to show real names and roles is the team's call |

### 6. Footer

| Part | Draft wording |
|---|---|
| Sources | Recipe data: Food.com, Hugging Face recipes-with-nutrition, CulinaryDB, RecipeDB and others (open or research-use licenses, full list in the README). Nutrition: USDA FoodData Central. Products: Open Food Facts (ODbL). Recipe photos belong to their sources. |
| Versions | Version 0.x (beta) · What's new (links to `CHANGELOG.md`) |
| Links | Project on GitHub · MIT License |

## What the pixel art shows

| Part | Plan |
|---|---|
| Kitchen | The 0.5.3 **American base kitchen** once it is ready; **Classic** until then. No cuisine kitchens on the landing (the visitor has not searched yet). |
| Chef | The default chef in front, with the speech bubble; on a phone the chef smaller, above the button |
| Time of day | **Afternoon** by default. The visitor's clock only with their permission, as in the app's Settings ("Use my clock for the kitchen's light"); the clock is read in the browser and never sent anywhere |
| Motion | Taps work as in the app (lamps, plants, steam), but nothing moves on its own when the device asks for reduced motion (`prefers-reduced-motion`) |
| Social preview | One still picture of the kitchen with the sign (`og:image`), so a shared link shows the kitchen, not a gray box (static page only; Streamlit cannot set it) |

## Build options

| | A. Landing view inside the Streamlit app | B. Separate static page (GitHub Pages) that links into the app |
|---|---|---|
| How | At the top of `app/app.py`, before `load_recipes()`: if `st.session_state["started"]` is not set and the URL has no `?start=1`, draw the landing and `st.stop()`. "Find a safe recipe" sets the flag (and `?start=1`) and reruns | A plain HTML page (one file, CSS, the kitchen PNG) in a `site/` or `docs/` folder, published with GitHub Pages; the button links to the app's URL with `?start=1` |
| First-load speed | Fast if the landing runs before the data loads; the recipes can start loading in the background after the landing is drawn | Instant: a few KB, no server. Hides the hosted app's wake-up wait (Streamlit Community Cloud apps sleep when unused) |
| Same look as the app | Yes, reuses the CSS, themes, `kitchen_scene.html` and `chef_lines` | A copy of the look; must be kept in step by hand |
| Search engines and link previews | Poor: Streamlit pages are drawn by JavaScript; no `og:image` | Good: plain HTML, a title, a description and a preview image |
| No tracking or cookies | Streamlit itself sets no tracking cookies; the app's usage statistics must stay off (`gatherUsageStats = false`) | Easy: no scripts, no fonts from a third party (fonts self-hosted), no analytics |
| Works in Colab, VS Code, Antigravity | Yes, nothing new to run; `?start=1` lets tests and the team skip it | Not needed there (the page is only for the hosted link) |
| Cost | Small: one function and a test | Small to medium: a page, a deploy setting, keeping the wording in sync |
| Risk | Returning visitors see it again in a new session (fixed by the `?start=1` link and a "Skip" link); one more rerun path to test | Two places to update; the app's URL must be stable before the page goes live |

**Recommended: A now, B when the app is hosted.** Build the landing view inside the app first (it is what users
see first in 0.5.3, it shares the art, and it gets the landing on screen before the data loads). When the team
picks hosting for the final presentation, add the static page with the same wording and a preview image, so the
shared link opens instantly and looks right in chats; its button then opens the app with `?start=1`, which skips
the in-app landing.

### Notes for whoever builds A

- The landing must be drawn before `recipes = load_recipes()` (today line 468 of `app/app.py`); the sidebar
  profile and the Settings popover are not drawn on the landing.
- Mobile first: one column at 400 px wide, the button above the fold, touch targets at least 44 px.
- Contrast: check the button and the body text against the panel in every kitchen and hour (WCAG AA, 4.5:1).
- Keyboard: the button is a real button with a visible focus; the chef's bubble is plain text a screen reader reads.
- Safety: the landing shows no recipe verdicts of its own. Any "safe" wording comes from the back end's rules
  (CLAUDE.md: safety decisions come from `src/everflavor`); the catch in the bubble is a fixed, reviewed fact.
- Version notes: the landing is a new feature, so `__version__`, `CHANGELOG.md` and `app/updates.py` change
  together (`/release`).
- Test: a Streamlit test that the landing shows without loading the data, that the button and `?start=1` open
  the app, and a real-browser check on desktop and phone (planner handoff notes).

## What it needs from the team

| Need | Who | Notes |
|---|---|---|
| The American base kitchen art (0.5.3), and a phone crop of it | team (art), Claude (scene) | Classic is used until then |
| Sign-off on every line of wording above, the chef's "catch" lines, and the team section | team | The disclaimer lines especially |
| Names or GitHub accounts for the team section | each member | Only what each person agrees to show |
| Hosting choice (Streamlit Community Cloud or Hugging Face Spaces) and the app's final URL | team | Needed before B |
| The demo data's photo licenses confirmed before going public | team | Open item in `design/PLAN.md` ("Getting found") |
| GitHub Pages turned on for the repository (for B) | repository owner (Chloe-Tu2) | Settings > Pages |

## Rough effort

| Piece | Effort |
|---|---|
| A: the landing view in the app, with tests and the browser check | about one day |
| Wording sign-off and the chef's catch lines | one team meeting |
| B: the static page, preview image and Pages setup | about one day, after hosting is chosen |
| Swapping Classic for the American kitchen when it lands | an hour (one setting) |

## Open questions

1. Does the landing show on every new visit, or only the first (a "Skip" link and `?start=1` for returning
   visitors)? Nothing can be remembered between visits without storing something, which the privacy rules avoid.
2. Should the landing include three "Today's safe picks" (planner 0.6.0 #6), or stay a pure intro? Picks need
   the data loaded, which slows the first screen.
3. Is "Find a safe recipe" the right button wording, given the checks are not medical advice? An alternative:
   "Find recipes for me".
4. Which hidden-allergen facts may the chef use as the "catch" (one per kitchen, checked by a team member)?
5. Real names, roles or only GitHub accounts in the team section?
6. Who runs the three-second test (five people who have not seen the app), and before which milestone?
7. Does the landing ship in 0.5.3 with the American kitchen, or in 0.6.0 with the onboarding?

## Sources

- Apexure, above-the-fold landing page design: <https://www.apexure.com/blog/2026-03-27-above-the-fold-landing-page-design>
- UForocks, landing page design best practices: <https://www.uforocks.com/blog/landing-page-design-best-practices/>
- Eseospace, landing page best practices: <https://eseospace.com/blog/landing-page-best-practices-15-tips-that-actually-convert/>
- Streamlit docs, `st.query_params` and session state: <https://docs.streamlit.io/develop/api-reference/caching-and-state>
- The project's own front-end plan: [design/PLAN.md](../../design/PLAN.md) (sections 1, 5, 6, 7, 8 and 9)
