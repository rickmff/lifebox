# Contributing

Thanks for helping. lifebox is a Claude skill: most of it is markdown, plus one Python script that
uses only the standard library.

## Ways to help

- **Recipes** for common paperwork. See [docs/recipes.md](docs/recipes.md).
- **Storage adapters**: verify an experimental adapter with a real connector, or add a new one.
  See [docs/adapters.md](docs/adapters.md).
- **Document reading**: better cues in `references/analysis.md` for documents and languages you
  know.
- **Bugs** in `lifebox.py`, with a failing test.

## Setup

You need Python 3.10 or newer. Nothing else is installed.

```bash
python3 -m unittest discover -s tests
```

With Claude Code installed, also run:

```bash
claude plugin validate .
```

To try your changes in Claude Code, install the plugin from your clone:

```
/plugin marketplace add ./
/plugin install lifebox@lifebox
```

## Guidelines

- Keep `lifebox.py` on the Python standard library so it runs everywhere Claude runs code.
- Keep `SKILL.md` under 500 lines. Put details in `references/` and point to them from
  `SKILL.md`.
- Use only the portable frontmatter keys in `SKILL.md`: `name`, `description`, `license`,
  `compatibility`, `metadata`, `allowed-tools`.
- When you change a table that the script mirrors (document types, reminder offsets), change both.
  The tests catch mismatches.
- Never commit real documents or personal data, not even in tests. Use fake names and the ICAO
  specimen MRZ.
- Bump the version in `plugin.json`, `SKILL.md` and `lifebox.py` together.
