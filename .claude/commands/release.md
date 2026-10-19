---
description: Release a new version of EverFlavor AI (version bump, changelog, What's new notes, checks, tag)
argument-hint: "[patch|minor|major] [what changed, in a few words]"
---

Release a new version, following the convention at the top of `CHANGELOG.md`. Arguments: $ARGUMENTS
(the kind of release, then what changed). Semantic versions: **patch** for fixes (0.5.1 -> 0.5.2), **minor**
for a new feature (0.5.2 -> 0.6.0), **major** only for 1.0.0 (the first finished release) or a breaking change.

1. Read `__version__` in `src/everflavor/__init__.py` and the top of `CHANGELOG.md`; work out the new version.
2. Look at the commits since the last tag (`git log $(git describe --tags --abbrev=0)..HEAD --oneline`, or all
   commits since the last CHANGELOG date if there is no tag yet) and summarise what changed.
3. Set `__version__` to the new version.
4. Add `## [X.Y.Z] - <today>` at the top of `CHANGELOG.md` (Added / Changed / Fixed, for the team) and its link
   at the bottom.
5. Add the version at the top of `UPDATES` in `app/updates.py`: today's date and 1 to 3 notes for the people who
   use the app, starting "New:", "Changed:" or "Fixed:", plain words, no technical or security details. The
   bell shows a dot until each visitor has read them.
6. Run every CI check (see CLAUDE.md), including `tests/test_version.py`. If anything fails, stop and fix it.
7. Commit on the release branch (`release/X.Y.Z`) with a message starting `vX.Y.Z`, push, and wait for CI.
8. When the team approves: merge into `main`, tag `git tag -a vX.Y.Z -m "EverFlavor AI vX.Y.Z"`, push the tag,
   and publish the GitHub Release with the CHANGELOG entry as its notes (on GitHub: Releases > Draft a new release).
9. Report the version, what the bell now announces, and the release link.
