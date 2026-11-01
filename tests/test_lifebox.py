import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "lifebox" / "scripts" / "lifebox.py"

spec = importlib.util.spec_from_file_location("lifebox", SCRIPT)
lb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lb)

TODAY = date(2026, 11, 1)

TD3 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<\nL898902C36UTO7408122F1204159ZE184226B<<<<<10\n"
TD1 = "I<UTOD231458907<<<<<<<<<<<<<<<\n7408122F1204159UTO<<<<<<<<<<<6\nERIKSSON<<ANNA<MARIA<<<<<<<<<<\n"


def run_cli(*args, stdin=""):
    return subprocess.run([sys.executable, str(SCRIPT), *args], input=stdin,
                          capture_output=True, text=True, check=False)


class NameTests(unittest.TestCase):
    def test_format_full(self):
        rec = {"type": "driver_license", "holder": "Rick", "expires": "2027-03-12"}
        self.assertEqual(lb.format_name(rec, ".PDF"), "2027-03-12 · Driver's License · Rick.pdf")

    def test_format_title_qualifier_and_no_expiry(self):
        rec = {"type": "birth_certificate", "title": "Certidão de Nascimento", "holder": "Ana",
               "qualifier": "copy"}
        self.assertEqual(lb.format_name(rec, "jpg"), "no-expiry · Certidão de Nascimento · Ana · copy.jpg")

    def test_format_sanitizes(self):
        rec = {"title": 'Lease: Rua A/B · "2nd" *floor*', "holder": "Rick?", "expires": "2026-12-31"}
        name = lb.format_name(rec, ".pdf")
        self.assertEqual(name, "2026-12-31 · Lease Rua AB - 2nd floor · Rick.pdf")
        self.assertEqual(name.count(lb.SEP), 2)

    def test_format_rejects_bad_date(self):
        with self.assertRaises(lb.LifeboxError):
            lb.format_name({"type": "passport", "expires": "12/03/2027"})

    def test_parse_canonical(self):
        p = lb.parse_name("2027-03-12 · Driver's License · Rick · front.pdf")
        self.assertTrue(p["canonical"])
        self.assertEqual((p["expires"], p["label"], p["holder"], p["qualifier"], p["ext"]),
                         ("2027-03-12", "Driver's License", "Rick", "front", ".pdf"))

    def test_parse_no_expiry_and_sidecar(self):
        p = lb.parse_name("no-expiry · Diploma · Rick.lifebox.md")
        self.assertTrue(p["canonical"] and p["sidecar"])
        self.assertIsNone(p["expires"])
        self.assertEqual(p["label"], "Diploma")

    def test_parse_non_canonical(self):
        p = lb.parse_name("IMG_2023.jpeg")
        self.assertFalse(p["canonical"])
        self.assertEqual((p["label"], p["ext"]), ("IMG_2023", ".jpeg"))

    def test_round_trip(self):
        rec = {"type": "passport", "holder": "Rick", "expires": "2030-03-11", "qualifier": "BR"}
        p = lb.parse_name(lb.format_name(rec, ".pdf"))
        self.assertEqual((p["expires"], p["holder"], p["qualifier"]), ("2030-03-11", "Rick", "BR"))


class RecordTests(unittest.TestCase):
    RECORD = {
        "lifebox": 1, "type": "driver_license", "title": "Driver's License", "holder": "Rick",
        "issuer": "IMT", "country": "PT", "number": "****1234", "issued": "2017-03-12",
        "expires": "2027-03-12", "tags": ["car", "id, main"], "summary": "Category B: cars only",
        "link": "https://drive.google.com/file/d/abc/view", "confidence": "high", "confirmed": True,
    }

    def test_round_trip(self):
        text = lb.emit_record(self.RECORD)
        rec, body = lb.parse_record(text)
        self.assertEqual(rec, self.RECORD)
        self.assertEqual(body, "")

    def test_frontmatter_with_body(self):
        text = lb.emit_record(self.RECORD, frontmatter=True, body="Renewed at the IMT office.")
        self.assertTrue(text.startswith("---\nlifebox: 1\n"))
        rec, body = lb.parse_record(text)
        self.assertEqual(rec["expires"], "2027-03-12")
        self.assertEqual(body, "Renewed at the IMT office.")

    def test_emit_quotes_when_needed(self):
        text = lb.emit_record({"type": "other", "title": "- dash", "summary": "a # b", "holder": "true",
                               "issuer": "", "tags": []})
        self.assertIn('title: "- dash"', text)
        self.assertIn('summary: "a # b"', text)
        self.assertIn('holder: "true"', text)
        self.assertNotIn("issuer", text)
        self.assertNotIn("tags", text)

    def test_emit_masks_numbers(self):
        self.assertIn("number: \"*****4567\"", lb.emit_record({"type": "passport", "number": "AB1234567"}))
        self.assertIn("number: AB1234567",
                      lb.emit_record({"type": "passport", "number": "AB1234567"}, mask=False))

    def test_values_stay_strings(self):
        rec, _ = lb.parse_record("lifebox: 1\nnumber: 0042\nholder: yes\nconfirmed: false\nissuer:\n")
        self.assertEqual(rec, {"lifebox": 1, "number": "0042", "holder": "yes", "confirmed": False,
                               "issuer": None})

    def test_flow_lists(self):
        rec, _ = lb.parse_record('tags: [a, "b, c", \'d\']\n')
        self.assertEqual(rec["tags"], ["a", "b, c", "d"])

    def test_bad_line(self):
        with self.assertRaises(lb.LifeboxError):
            lb.parse_record("just text")

    def test_validate_ok(self):
        self.assertEqual(lb.validate_record(self.RECORD), [])

    def test_validate_problems(self):
        problems = lb.validate_record({"type": "spaceship", "issued": "2027-01-01", "expires": "2026-01-01",
                                       "number": "AB1234567", "colour": "red", "x_note": "ok",
                                       "confidence": "sure"})
        joined = "\n".join(problems)
        for needle in ("type:", "earlier than issued", "number:", "colour:", "confidence:"):
            self.assertIn(needle, joined)
        self.assertNotIn("x_note", joined)

    def test_mask_number(self):
        self.assertEqual(lb.mask_number("AB 123 456"), "****3456")
        self.assertEqual(lb.mask_number("1234"), "1234")
        self.assertEqual(lb.mask_number("****1234"), "****1234")


class RadarTests(unittest.TestCase):
    ITEMS = [
        {"name": "2026-10-20 · ID Card · Rick.pdf", "type": "national_id"},
        {"name": "2026-11-20 · Vehicle Insurance · Rick.pdf", "type": "vehicle_insurance"},
        {"name": "2027-01-15 · Lease · Rick.pdf", "type": "lease", "link": "https://x/lease"},
        {"name": "2030-03-11 · Passport · Rick.pdf", "type": "passport"},
        {"name": "no-expiry · Diploma · Rick.pdf", "type": "diploma"},
    ]

    def test_statuses_and_order(self):
        report = lb.radar(lb.load_items(self.ITEMS), TODAY)
        self.assertEqual([i["status"] for i in report["items"]], ["expired", "urgent", "soon"])
        self.assertEqual(report["counts"], {"expired": 1, "urgent": 1, "soon": 1, "ok": 1, "no_expiry": 1})
        self.assertEqual(report["items"][0]["days_left"], -12)

    def test_window_and_all(self):
        report = lb.radar(lb.load_items(self.ITEMS), TODAY, window=30, include_all=True)
        self.assertEqual(len(report["items"]), 5)
        self.assertEqual(report["items"][2]["status"], "ok")

    def test_names_only_infers_type(self):
        items = lb.load_items(["2027-03-12 · Driver's License · Rick.pdf", "scan.pdf"])
        self.assertEqual([i["type"] for i in items], ["driver_license", "other"])
        self.assertEqual(items[1]["title"], "scan")

    def test_renew_by_from_type_offsets(self):
        report = lb.radar(lb.load_items([{"name": "2027-01-15 · Lease · Rick.pdf"}]), TODAY)
        self.assertEqual(report["items"][0]["renew_by"], "2026-09-17")

    def test_record_in_description(self):
        items = lb.load_items([{"name": "scan.pdf", "description": "lifebox: 1\ntype: visa\nexpires: 2026-12-01"}])
        self.assertEqual((items[0]["type"], items[0]["expires"]), ("visa", "2026-12-01"))

    def test_markdown(self):
        text = lb.radar_markdown(lb.radar(lb.load_items(self.ITEMS), TODAY))
        self.assertIn("[Lease (Rick)](https://x/lease)", text)
        self.assertIn("expired 12 days ago", text)


class ReminderTests(unittest.TestCase):
    def test_passport_offsets(self):
        items = lb.load_items([{"name": "2027-09-30 · Passport · Rick.pdf", "type": "passport"}])
        events = lb.reminders(items, TODAY)["events"]
        self.assertEqual([e["date"] for e in events], ["2027-01-03", "2027-04-03", "2027-07-02", "2027-09-30"])
        self.assertEqual(events[-1]["title"], "Passport (Rick) expires today")
        self.assertEqual(events[0]["title"], "Passport (Rick) expires in 270 days")

    def test_past_offsets_skipped_and_stable_uids(self):
        items = lb.load_items([{"name": "2026-11-20 · Vehicle Insurance · Rick.pdf"}])
        first = lb.reminders(items, TODAY)["events"]
        self.assertEqual([e["date"] for e in first], ["2026-11-06", "2026-11-20"])
        self.assertEqual(first, lb.reminders(items, TODAY)["events"])

    def test_override(self):
        items = lb.load_items([{"name": "2027-01-15 · Lease · Rick.pdf"}])
        dates = [e["date"] for e in lb.reminders(items, TODAY, [10])["events"]]
        self.assertEqual(dates, ["2027-01-05", "2027-01-15"])


RECIPE = """---
id: test-recipe
title: Test recipe
anchor: driver_license.expires
applies_to: [driver_license]
summary: Testing.
---
# Test

```lifebox-steps
-120 localize  Confirm the local rules
-30  apply     Submit the application
0    expiry    Deadline
+14  collect   Collect the new document
```

```lifebox-documents
driver_license  required  Current license
photo_id        depends   ID photo
```
"""


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "test-recipe.md"
        self.path.write_text(RECIPE, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_dates_and_late(self):
        p = lb.plan(lb.load_recipe(str(self.path)), date(2027, 1, 15), TODAY)
        self.assertEqual([(s["id"], s["date"], s["late"]) for s in p["steps"]], [
            ("localize", "2026-09-17", True), ("apply", "2026-12-16", False),
            ("expiry", "2027-01-15", False), ("collect", "2027-01-29", False)])
        self.assertEqual(p["documents"][1], {"type": "photo_id", "need": "depends", "label": "ID photo"})
        self.assertEqual(p["recipe"], "test-recipe")

    def test_markdown_and_events(self):
        p = lb.plan(lb.load_recipe(str(self.path)), date(2027, 1, 15), TODAY)
        md = lb.plan_markdown(p)
        self.assertIn("- [ ] ASAP (was 2026-09-17) · Confirm the local rules `localize`", md)
        events = lb.plan_events(p, "Rick")["events"]
        self.assertEqual(len(events), 3)
        self.assertEqual(events[0]["title"], "Submit the application (Rick)")

    def test_month_end_and_leap_year(self):
        p = lb.plan(lb.load_recipe(str(self.path)), date(2028, 3, 30), date(2027, 1, 1))
        self.assertEqual(p["steps"][1]["date"], "2028-02-29")

    def test_bad_step(self):
        self.path.write_text(RECIPE.replace("-30  apply", "soon apply"), encoding="utf-8")
        with self.assertRaises(lb.LifeboxError):
            lb.load_recipe(str(self.path))


def unfold(text):
    return text.replace("\r\n ", "")


class IcsTests(unittest.TestCase):
    STAMP = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)

    def test_structure(self):
        ics = lb.to_ics([{"uid": "a@lifebox", "date": "2027-03-12", "title": "Passport, Rick; renew",
                          "description": "Line 1\nLine 2", "url": "https://x/y", "alarms": [0, 7]}],
                         dtstamp=self.STAMP)
        self.assertNotIn("\n", ics.replace("\r\n", ""))
        lines = unfold(ics).split("\r\n")
        for expected in ("BEGIN:VCALENDAR", "UID:a@lifebox", "DTSTAMP:20261101T120000Z",
                         "DTSTART;VALUE=DATE:20270312", "DTEND;VALUE=DATE:20270313",
                         "SUMMARY:Passport\\, Rick\\; renew", "URL:https://x/y",
                         "DESCRIPTION:Line 1\\nLine 2\\nhttps://x/y", "TRIGGER:PT9H", "TRIGGER:-PT159H",
                         "END:VCALENDAR"):
            self.assertIn(expected, lines)
        self.assertEqual(lines.count("BEGIN:VALARM"), 2)

    def test_folding_multibyte(self):
        title = "Renovação da autorização de residência — " * 4
        ics = lb.to_ics([{"date": "2027-01-01", "title": title}], dtstamp=self.STAMP)
        for line in ics.split("\r\n"):
            self.assertLessEqual(len(line.encode("utf-8")), 75)
        self.assertIn("SUMMARY:" + title, unfold(ics))

    def test_deterministic(self):
        events = [{"date": "2027-01-01", "title": "X"}]
        self.assertEqual(lb.to_ics(events, dtstamp=self.STAMP), lb.to_ics(events, dtstamp=self.STAMP))


class MrzTests(unittest.TestCase):
    def test_td3_specimen(self):
        r = lb.parse_mrz(TD3, TODAY)
        self.assertTrue(r["valid"])
        self.assertEqual((r["format"], r["issuing_state"], r["birth_date"], r["expiry_date"]),
                         ("TD3", "UTO", "1974-08-12", "2012-04-15"))
        self.assertEqual((r["surname"], r["given_names"]), ("ERIKSSON", "ANNA MARIA"))
        self.assertEqual(r["number"], "*****02C3")
        self.assertEqual(lb.parse_mrz(TD3, TODAY, full_number=True)["number"], "L898902C3")

    def test_td1_specimen(self):
        r = lb.parse_mrz("some OCR noise\n" + TD1, TODAY, full_number=True)
        self.assertTrue(r["valid"])
        self.assertEqual((r["format"], r["number"], r["nationality"]), ("TD1", "D23145890", "UTO"))

    def test_bad_check_digit(self):
        r = lb.parse_mrz(TD3.replace("1204159", "1204169"), TODAY)
        self.assertFalse(r["valid"])
        self.assertFalse(r["checks"]["expiry"])

    def test_no_mrz(self):
        with self.assertRaises(lb.LifeboxError):
            lb.parse_mrz("REPUBLICA FEDERATIVA DO BRASIL", TODAY)

    def test_check_digit(self):
        self.assertEqual(lb.mrz_check_digit("L898902C3"), 6)
        self.assertEqual(lb.mrz_check_digit("740812"), 2)


class CliTests(unittest.TestCase):
    def test_name_parse(self):
        out = run_cli("name", "parse", "2027-03-12 · Passport · Rick.pdf")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(json.loads(out.stdout)[0]["holder"], "Rick")

    def test_radar_md(self):
        out = run_cli("radar", "--today", "2026-11-01", "--format", "md",
                      stdin=json.dumps(["2026-11-20 · Vehicle Insurance · Rick.pdf"]))
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("urgent", out.stdout)

    def test_meta_validate_exit_code(self):
        self.assertEqual(run_cli("meta", "validate", stdin="type: passport\n").returncode, 0)
        self.assertEqual(run_cli("meta", "validate", stdin="type: nope\n").returncode, 1)

    def test_error_message(self):
        out = run_cli("radar", stdin="not json")
        self.assertEqual(out.returncode, 2)
        self.assertIn("lifebox:", out.stderr)

    def test_ics_pipeline(self):
        reminders = run_cli("reminders", "--today", "2026-11-01",
                            stdin=json.dumps(["2027-03-12 · Driver's License · Rick.pdf"]))
        ics = run_cli("ics", "--dtstamp", "2026-11-01T00:00:00Z", stdin=reminders.stdout)
        self.assertEqual(ics.returncode, 0, ics.stderr)
        self.assertEqual(ics.stdout.count("BEGIN:VEVENT"), 4)


if __name__ == "__main__":
    unittest.main()
