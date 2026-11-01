# Recipes

A recipe is a generic template for a piece of paperwork: the steps, counted in days from a
deadline, and the documents usually needed. Claude localizes it for the user's country with
official sources before turning it into a plan.

Recipes live in [`skills/lifebox/references/recipes/`](../skills/lifebox/references/recipes).

## Format

````markdown
---
id: renew-driver-license
title: Renew a driver's license
anchor: expiry date of the driver's license
applies_to: [driver_license]
summary: Check medical requirements, apply and keep proof of renewal before the licence expires.
reviewed: 2026-11-01
---
# Renew a driver's license

One paragraph on what varies between countries.

## Steps

```lifebox-steps
-120 localize   Confirm the renewal rules, fee, and whether a medical certificate is needed
-90  apply      Book the appointment or submit the online renewal, and pay the fee
0    expiry     The licence expires
+14  collect    Collect the new card
```

## Documents

```lifebox-documents
driver_license  required  Current driver's license
medical         depends   Medical certificate (some countries, ages or categories)
```

## Localize

What to ask the user and what to look up on official sites.

## Tips

Short, practical, true everywhere.
````

- **Frontmatter** — `id` (same as the file name), `title`, `anchor` (what date the steps count
  from), `applies_to` (document types that trigger it), `summary`, `reviewed`.
- **Steps** — one per line: offset in days from the anchor (`-120`, `0`, `+14`), a unique id, a
  title. The earliest step must be `localize`.
- **Documents** — one per line: a type from the vocabulary in `vault-spec.md`, `required`,
  `optional` or `depends`, and a label.

## Rules

- Keep recipes generic. Facts that differ by country (fees, deadlines, offices, forms) belong in
  the localize step, which Claude researches each time with official sources.
- Lead times should be safe defaults. Saying "adjust to your notice period" is better than guessing.
- Write in plain English. Claude translates when it talks to the user.

## Check your recipe

```bash
python3 skills/lifebox/scripts/lifebox.py recipes
python3 skills/lifebox/scripts/lifebox.py plan --recipe your-recipe --anchor 2027-03-12 --format md
python3 -m unittest discover -s tests
```

The tests check the frontmatter, the blocks, the document types and that `localize` comes first.
