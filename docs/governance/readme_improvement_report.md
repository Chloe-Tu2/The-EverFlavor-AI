# README improvement report (2026-11-22)

Can a newcomer answer seven questions about EverFlavor within 30 seconds of opening the main README? Checked by
Claude (AI) against the README of 2026-11-22.

| Question | Before | Now |
|---|---|---|
| What is EverFlavor? | Yes: the banner and the Overview | Also the first line of "At a glance" |
| How is it different? | Only implied (the safety rules are deep in "Restriction flag check") | "At a glance": rules, not a model, decide safety; facts are cited |
| How do I run it? | At line 477 of 740 ("The App") | Two commands near the top, on the demo data |
| How does the Food Graph work? | Not in the README (only `src/everflavor/README.md`) | One paragraph, with the file |
| How does the safety engine work? | Spread over "Restriction flag check" and "Known data gaps" | One paragraph, with the files and the policy sheet |
| How do I contribute? | Not linked from the README | Linked |
| What is the roadmap? | "Next" lists older items; the planner is not linked | The planner is linked |

Also added: links to the governance pages and the audits, and a line saying the MIT licence covers the code, not
the data.

## Not done yet (suggested, for the team)

1. **"Current Status" is dated:** "Done (Weeks 4–6)" and "Results so far" describe the autumn pipeline, not the
   graph, the atlas or the audits of November. Shorten it to a summary that links the planner and the CHANGELOG.
2. **Screenshots:** the README shows the banner and art but no screenshot of the kitchen, a recipe card or the map.
3. **Length:** 740 lines. "Data Sources" repeats `docs/sources.md`, and "Project Structure" repeats the folder
   READMEs; both could become short tables with links.
4. **A page for the safety engine** is still missing (no `safety/` folder exists: `flags.py`, `safety.py`,
   `recommend.py` sit in `src/everflavor/`). It should say purpose, inputs, outputs, dependencies, owner and
   future work, as `src/everflavor/domain/README.md` (added 2026-11-22) does.
5. **The badges** list CrewAI, scikit-learn and Kaggle; check that each is still used, so the top of the page is
   not out of date.
