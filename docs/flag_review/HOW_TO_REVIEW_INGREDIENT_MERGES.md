# How to review the ingredient merges

About 20 minutes. No coding needed: a spreadsheet program (Excel, Google Sheets, Numbers) is enough.

## Why this review exists

EverFlavor is about to give each food one id that every table shares: the allergy rules, the may-contain list,
the specialty ingredients and the USDA nutrition. Names that are the same food get the same id, and then they get
the **same allergy flags**. If two different foods were merged by mistake, someone could be warned about the wrong
food, or not warned at all. So a person, not the code, says yes to every merge.

## The file

[ingredient_merge_review.csv](ingredient_merge_review.csv): 79 names in 36 groups. Each group is a set of names
that Wikidata gives as names of the same food (for example "powdered sugar" and "icing sugar").

| Column | What it is |
|---|---|
| `group_id` | The Wikidata item the names share (open `https://www.wikidata.org/wiki/<group_id>` to see it) |
| `name` | One name in the group |
| `recipes` | How many recipes in our data use this name (bigger means it matters more) |
| `flags_now` | The flags the app sets on this name today (contains_gluten, contains_soy...) |
| `flags_in_group` | The flags the whole group sets together |
| `would_gain` | The flags this name would **gain** if the group is merged |
| `same_food` | **You fill this in:** `yes`, `no` or `unsure` |
| `reviewed_by` | **You fill this in:** your name (as the team uses it) |
| `notes` | **You fill this in** when the answer is no or unsure: why |

The rows where `would_gain` is not empty come first. Those are the ones that change what the app says.

## What to do

1. For each group, read its names and ask: **is every name here the same food, for someone with an allergy?**
   - "soy sauce" and "soya sauce": the same food → `yes` on both rows.
   - "fennel" and "fennel seed": related but not the same (a vegetable and a spice) → `no`, note "bulb vs seed".
   - Not sure (a brand, a regional word you don't know) → `unsure`, with a note. Look it up on the group's Wikidata
     page or Wikipedia if you like.
2. For the rows with `would_gain` filled in, also check that the gained flag is **right** for that name. Example:
   "baking mix" would gain `contains_gluten` from "cake mix". Most baking mixes contain wheat flour, so `yes`.
3. Put your name in `reviewed_by` on every row you answered.
4. Send the file back (or commit it on a branch, if you use git). Do not change the other columns.

## What happens next

- `yes`: the names share one id and one set of flags.
- `no`: they stay separate foods; the note is kept as the reason.
- `unsure`: they stay separate until someone decides.

Before the merge is switched on, the safety engine check (notebook 12, 10,000 recipes) runs before and after, and
every recipe whose result changes is listed for a last look. The decision is recorded with your name, like the
other flag policies in [flag_policies.csv](flag_policies.csv).

The sheet is made by `scripts/ingredient_merge_review.py` from notebook 04's name matches.
