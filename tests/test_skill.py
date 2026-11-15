"""Consistency checks for the skill files: frontmatter, references, recipes and tables."""

import importlib.util
import json
import re
import unittest
from pathlib import Path

try:
    import yaml
except ImportError:  # PyYAML is optional; the checks that need it are skipped
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "lifebox"
REFS = SKILL / "references"

spec = importlib.util.spec_from_file_location("lifebox", SKILL / "scripts" / "lifebox.py")
lb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lb)

# Frontmatter keys accepted everywhere skills load (Claude.ai upload, API, Claude Code).
PORTABLE_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}


def frontmatter(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", text, re.S)
    if not m:
        raise AssertionError(f"{path} has no frontmatter")
    return m.group(1), m.group(2)


def section(text: str, heading: str) -> str:
    m = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    if not m:
        raise AssertionError(f"missing section '## {heading}'")
    return m.group(1)


def table_rows(text: str, first_cell: str) -> list[list[str]]:
    rows = []
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and re.fullmatch(first_cell, cells[0]):
            rows.append(cells)
    return rows


class SkillFileTests(unittest.TestCase):
    def setUp(self):
        self.fm, self.body = frontmatter(SKILL / "SKILL.md")

    def test_frontmatter_keys_are_portable(self):
        keys = set(re.findall(r"^([A-Za-z_-]+):", self.fm, re.M))
        self.assertLessEqual(keys, PORTABLE_KEYS)
        self.assertIn("name", keys)
        self.assertIn("description", keys)

    @unittest.skipIf(yaml is None, "PyYAML not installed")
    def test_frontmatter_is_valid_yaml(self):
        data = yaml.safe_load(self.fm)
        self.assertEqual(data["name"], "lifebox")
        self.assertEqual(data["name"], SKILL.name)
        self.assertRegex(data["name"], r"^[a-z0-9-]{1,64}$")
        self.assertLessEqual(len(data["description"]), 1024)
        self.assertTrue(all(isinstance(v, str) for v in data["metadata"].values()))

    def test_description_length_without_yaml(self):
        m = re.search(r"^description: (.*)$", self.fm, re.M)
        self.assertLessEqual(len(m.group(1)), 1024)
        self.assertNotIn(": ", m.group(1))
        self.assertNotIn(" #", m.group(1))

    def test_size(self):
        lines = (SKILL / "SKILL.md").read_text(encoding="utf-8").count("\n")
        self.assertLess(lines, 500)

    def test_referenced_files_exist(self):
        for ref in sorted(set(re.findall(r"`(references/[^`*<\s]+|scripts/[^`\s]+\.py)", self.body))):
            path = SKILL / ref.rstrip("/")
            self.assertTrue(path.exists(), f"SKILL.md mentions missing {ref}")

    def test_every_adapter_is_listed(self):
        for adapter in sorted((REFS / "storage").glob("*.md")):
            self.assertIn(f"references/storage/{adapter.name}", self.body)


class RecipeTests(unittest.TestCase):
    def test_recipes(self):
        files = sorted((REFS / "recipes").glob("*.md"))
        self.assertGreaterEqual(len(files), 5)
        for path in files:
            with self.subTest(recipe=path.name):
                r = lb.load_recipe(str(path))
                self.assertEqual(r["id"], path.stem)
                for key in ("title", "anchor", "applies_to", "summary", "reviewed"):
                    self.assertTrue(r.get(key), f"missing {key}")
                self.assertLessEqual(set(r["applies_to"]), set(lb.TYPES))
                self.assertTrue(r["steps"] and r["documents"])
                first = min(r["steps"], key=lambda s: s["offset"])
                self.assertEqual(first["id"], "localize", "the earliest step must be 'localize'")
                ids = [s["id"] for s in r["steps"]]
                self.assertEqual(len(ids), len(set(ids)), "step ids must be unique")
                for d in r["documents"]:
                    self.assertIn(d["type"], lb.TYPES)

    def test_recipe_list_command(self):
        listed = {r["id"] for r in lb.list_recipes()}
        self.assertEqual(listed, {p.stem for p in (REFS / "recipes").glob("*.md")})


class TableTests(unittest.TestCase):
    def test_vault_spec_types_match_script(self):
        text = section((REFS / "vault-spec.md").read_text(encoding="utf-8"), "Document types")
        rows = table_rows(text, r"`[a-z_]+`")
        spec_types = {r[0].strip("`"): r[1] for r in rows}
        self.assertEqual(set(spec_types), set(lb.TYPES))
        for key, label in spec_types.items():
            self.assertEqual(label, lb.TYPES[key][0], key)

    def test_reminder_offsets_match_script(self):
        rows = table_rows((REFS / "reminders.md").read_text(encoding="utf-8"), r"`[a-z_]+`")
        table = {r[0].strip("`"): [int(x) for x in r[1].split(",")] for r in rows}
        expected = {k: v[1] for k, v in lb.TYPES.items() if v[1]}
        self.assertEqual(table, expected)

    def test_record_fields_documented(self):
        text = section((REFS / "vault-spec.md").read_text(encoding="utf-8"), "Records")
        rows = table_rows(text, r"`[a-z_]+`(, `[a-z_]+`)*")
        documented = {f.strip("` ") for r in rows for f in r[0].split(",")}
        self.assertLessEqual(set(lb.FIELDS), documented)


class PackagingTests(unittest.TestCase):
    def test_manifests(self):
        plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(plugin["name"], "lifebox")
        self.assertEqual(market["plugins"][0]["name"], plugin["name"])
        self.assertEqual(market["plugins"][0]["source"], "./")
        self.assertEqual(plugin["version"], lb.VERSION)
        self.assertFalse((ROOT / "bin").exists(), "a top-level bin/ blocks installs on Claude.ai")

    def test_skill_version_matches(self):
        fm, _ = frontmatter(SKILL / "SKILL.md")
        self.assertIn(f'version: "{lb.VERSION}"', fm)

    def test_dashboard_data_is_json(self):
        html = (REFS / "dashboard.html").read_text(encoding="utf-8")
        m = re.search(r'<script id="lifebox-data" type="application/json">(.*?)</script>', html, re.S)
        data = json.loads(m.group(1))
        self.assertIn("documents", data)
        self.assertNotRegex(html, r'(src|href)="https?://', "the dashboard must not load external resources")


if __name__ == "__main__":
    unittest.main()
