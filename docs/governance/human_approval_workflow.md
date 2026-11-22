# Human approval workflow

Who may decide what, for people and for AI assistants working on the repository. Proposed 2026-11-22 by Claude
(AI); the team confirms it. A standing permission a person gives an AI in writing (for example "merge when the
checks are green") is recorded in the planner and applies only to what it names.

## An AI may do on its own (and a person can review afterwards)

- Run audits and write reports: coverage, taxonomy and graph validation, recipe, map, image, dish completeness
  and waiter coverage, secret and PII scans.
- Fix its own code and reports, and improve documentation, as long as numbers come from the latest run.
- Open branches and pull requests.
- Merge a pull request only when a person has said so in writing for that work, and only after every check
  passes.

## A person must approve first

| Decision | Why |
|---|---|
| Publishing a new dish or recipe in the app | What people see must be checked by a person |
| Downloading images, and showing a downloaded photo | Licence, credit and a check by eye ([public_data_policy.md](public_data_policy.md)) |
| Adding an external dataset, or a new use of one | Its licence and terms |
| Licence decisions (whether a source may be used, and how) | A legal judgment |
| Map tagging additions (a new cuisine tag, a new place source) | What the map claims about real businesses |
| Releases and version numbers (`/release`) | A public promise |
| Deployments | Public |
| Pull request merges, unless a standing permission covers them | Final say on `main` |

## Two people must approve (and the second is not the author)

- Changes to the safety engine (`src/everflavor/flags.py`, `safety.py`, `recommend.py`), allergen words and
  their exceptions, diet and medical screens: a missed caution can hurt someone. Flags only ever add cautions.
- Removing a recipe or dish from the data.
- Legal questions and licence overrides.

Each such decision is written down with who made it: a policy row in `docs/flag_review/flag_policies.csv` for
safety rules, a row in a review sheet for data (`docs/audits/dish_link_review.csv`,
`data/reference/dish_photo_review.csv`), or the pull request's approvals.

## When an AI must stop and write it down instead

An AI stops and adds the question to [needs_human_review.md](needs_human_review.md) instead of guessing when:
a licence or attribution is unclear; a dish's origin, country or cuisine is disputed; an allergen mapping is
ambiguous; an image's source is unclear; the taxonomy conflicts with a source; a recipe matches several dishes
equally; or it finds what may be personal data or a secret. Unknown is acceptable; incorrect is not. Nothing is
deleted automatically.
