#!/usr/bin/env python3
"""Deterministic helpers for the lifebox skill.

Standard library only, so it runs unchanged in Claude.ai code execution, Claude
Desktop/Cowork and Claude Code. Commands read JSON or text on stdin (or take
arguments) and print JSON or text on stdout.

  name format               record JSON -> canonical file name
  name parse NAME...        file names -> JSON
  meta parse                record text (bare or ---frontmatter---) -> JSON
  meta emit                 record JSON -> record text (numbers masked)
  meta validate             record text or JSON -> problems
  radar                     documents -> expiry report
  reminders                 documents -> calendar events JSON
  recipes                   list the bundled recipes
  plan                      recipe + anchor date -> dated steps (json | md | events)
  ics                       events JSON -> iCalendar text
  mrz                       passport/ID machine-readable zone -> fields (ICAO 9303)

Run `lifebox.py <command> --help` for options.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

VERSION = "0.1.0"

SEP = " · "
NO_EXPIRY = "no-expiry"
SIDECAR_SUFFIX = ".lifebox.md"

# type -> (default label, reminder offsets in days before expiry)
# Keep in sync with references/vault-spec.md and references/reminders.md
# (tests/test_skill.py checks both).
TYPES: dict[str, tuple[str, list[int]]] = {
    "passport": ("Passport", [270, 180, 90]),
    "national_id": ("ID Card", [180, 90, 30]),
    "residence_permit": ("Residence Permit", [120, 60, 30, 7]),
    "visa": ("Visa", [90, 30, 7]),
    "driver_license": ("Driver's License", [120, 60, 14]),
    "vehicle_registration": ("Vehicle Registration", [60, 14]),
    "vehicle_inspection": ("Vehicle Inspection", [60, 21, 7]),
    "vehicle_insurance": ("Vehicle Insurance", [45, 14]),
    "insurance_policy": ("Insurance Policy", [45, 14]),
    "health_insurance": ("Health Insurance", [45, 14]),
    "lease": ("Lease", [120, 90, 30]),
    "employment_contract": ("Employment Contract", [60, 14]),
    "utility_bill": ("Utility Bill", []),
    "proof_of_address": ("Proof of Address", []),
    "bank_statement": ("Bank Statement", []),
    "payslip": ("Payslip", []),
    "tax_return": ("Tax Return", []),
    "birth_certificate": ("Birth Certificate", []),
    "marriage_certificate": ("Marriage Certificate", []),
    "diploma": ("Diploma", []),
    "medical": ("Medical Document", [30]),
    "warranty": ("Warranty", [30]),
    "receipt": ("Receipt", []),
    "invoice": ("Invoice", []),
    "form": ("Form", []),
    "other": ("Document", [30]),
}

# Record keys in canonical order (see references/vault-spec.md).
FIELDS = [
    "lifebox", "type", "title", "holder", "issuer", "country", "number",
    "issued", "expires", "renew_by", "tags", "summary", "link", "source",
    "confidence", "confirmed", "updated",
]
DATE_FIELDS = ("issued", "expires", "renew_by", "updated")
CONFIDENCE = ("high", "medium", "low")
NEEDS = ("required", "optional", "depends")

ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FORBIDDEN = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
ALARM_HOUR = 9  # reminders fire at 09:00 local time


class LifeboxError(Exception):
    pass


# ---------------------------------------------------------------- dates

def parse_date(value, field: str = "date") -> date:
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not ISO_DATE.match(value.strip()):
        raise LifeboxError(f"{field}: expected YYYY-MM-DD, got {value!r}")
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise LifeboxError(f"{field}: {exc}") from None


def is_date(value) -> bool:
    try:
        parse_date(value)
        return True
    except LifeboxError:
        return False


# ---------------------------------------------------------------- names

def clean_part(text: str, limit: int = 60) -> str:
    text = FORBIDDEN.sub("", str(text)).replace("·", "-")
    text = re.sub(r"\s+", " ", text).strip(" .")
    return text[:limit].rstrip()


def split_ext(name: str) -> tuple[str, str, bool]:
    """Return (stem, ext, is_sidecar)."""
    if name.endswith(SIDECAR_SUFFIX):
        return name[: -len(SIDECAR_SUFFIX)], "", True
    m = re.search(r"(\.[A-Za-z0-9]{1,5})$", name)
    if m and m.start() > 0:
        return name[: m.start()], m.group(1), False
    return name, "", False


def format_name(rec: dict, ext: str | None = None) -> str:
    expires = rec.get("expires")
    prefix = parse_date(expires, "expires").isoformat() if expires else NO_EXPIRY
    label = rec.get("title") or TYPES.get(rec.get("type", ""), ("Document", []))[0]
    parts = [prefix, clean_part(label)]
    for key in ("holder", "qualifier"):
        if rec.get(key):
            parts.append(clean_part(rec[key]))
    ext = ext if ext is not None else rec.get("ext", "")
    if ext and not ext.startswith("."):
        ext = "." + ext
    return SEP.join(p for p in parts if p) + (ext or "").lower()


def parse_name(name: str) -> dict:
    stem, ext, sidecar = split_ext(name)
    parts = [p.strip() for p in stem.split(SEP)]
    out = {"name": name, "ext": ext, "sidecar": sidecar, "canonical": False,
           "expires": None, "label": stem.strip(), "holder": None, "qualifier": None}
    if len(parts) >= 2 and (parts[0] == NO_EXPIRY or is_date(parts[0])):
        out.update(canonical=True,
                   expires=None if parts[0] == NO_EXPIRY else parts[0],
                   label=parts[1],
                   holder=parts[2] if len(parts) > 2 else None,
                   qualifier=SEP.join(parts[3:]) if len(parts) > 3 else None)
    return out


# ---------------------------------------------------------------- records

FRONTMATTER = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)(.*)\Z", re.S)


def _split_flow(inner: str) -> list[str]:
    items, buf, quote = [], [], None
    for ch in inner:
        if quote:
            buf.append(ch)
            if ch == quote and (len(buf) < 2 or buf[-2] != "\\"):
                quote = None
        elif ch in "\"'":
            quote = ch
            buf.append(ch)
        elif ch == ",":
            items.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    if "".join(buf).strip():
        items.append("".join(buf))
    return [i.strip() for i in items if i.strip()]


def _scalar(raw: str, numeric: bool = False):
    raw = raw.strip()
    if raw in ("", "~", "null", "Null", "NULL"):
        return None
    if len(raw) >= 2 and raw[0] == raw[-1] == '"':
        return json.loads(raw)
    if len(raw) >= 2 and raw[0] == raw[-1] == "'":
        return raw[1:-1].replace("''", "'")
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False
    if numeric and re.fullmatch(r"-?\d+", raw):
        return int(raw)
    return raw


def _value(raw: str, numeric: bool = False):
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        return [_scalar(i) for i in _split_flow(raw[1:-1])]
    # drop trailing comments on unquoted values
    if not raw.startswith(("\"", "'")):
        raw = re.split(r"\s+#", raw, maxsplit=1)[0]
    return _scalar(raw, numeric)


def parse_record(text: str) -> tuple[dict, str]:
    """Parse a flat YAML-subset record. Returns (record, body)."""
    body = ""
    m = FRONTMATTER.match(text.lstrip("\ufeff"))
    if m:
        text, body = m.group(1), m.group(2)
    rec = {}
    for lineno, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, raw = line.partition(":")
        if not sep or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key.strip()):
            raise LifeboxError(f"line {lineno}: expected 'key: value', got {line!r}")
        key = key.strip()
        rec[key] = _value(raw, numeric=key == "lifebox")
    return rec, body.strip()


_PLAIN = re.compile(r"^[^\s\[\]{}#&*!|>'\"%@`,:?-][^#]*$")


def _emit_scalar(v, in_list: bool = False) -> str:
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, int):
        return str(v)
    s = str(v)
    needs_quotes = (
        not s or not _PLAIN.match(s) or s != s.strip() or ": " in s or s.endswith(":")
        or s.lower() in ("true", "false", "yes", "no", "null", "~")
        or re.fullmatch(r"-?\d+(\.\d+)?", s) is not None
        or (in_list and any(c in s for c in ",[]"))
    )
    return json.dumps(s, ensure_ascii=False) if needs_quotes else s


def mask_number(number) -> str:
    s = str(number)
    visible = re.sub(r"[^A-Za-z0-9]", "", s)
    if len(visible) <= 4 or set(s[:-4]) <= {"*"}:
        return s
    return "*" * (len(visible) - 4) + visible[-4:]


def emit_record(rec: dict, mask: bool = True, frontmatter: bool = False, body: str = "") -> str:
    rec = dict(rec)
    rec.setdefault("lifebox", 1)
    if mask and rec.get("number"):
        rec["number"] = mask_number(rec["number"])
    keys = [k for k in FIELDS if k in rec] + sorted(k for k in rec if k not in FIELDS)
    lines = []
    for k in keys:
        v = rec[k]
        if v is None or v == "" or v == []:
            continue
        if isinstance(v, list):
            lines.append(f"{k}: [" + ", ".join(_emit_scalar(i, True) for i in v) + "]")
        else:
            lines.append(f"{k}: {_emit_scalar(v)}")
    text = "\n".join(lines)
    if frontmatter:
        text = f"---\n{text}\n---\n"
        if body:
            text += "\n" + body.strip() + "\n"
    return text


def validate_record(rec: dict, allow_full_numbers: bool = False) -> list[str]:
    problems = []
    if rec.get("lifebox") not in (1, None):
        problems.append(f"lifebox: unsupported version {rec.get('lifebox')!r}")
    if not rec.get("type"):
        problems.append("type: missing")
    elif rec["type"] not in TYPES:
        problems.append(f"type: {rec['type']!r} is not in the vocabulary")
    for f in DATE_FIELDS:
        if rec.get(f) is not None and not is_date(rec[f]):
            problems.append(f"{f}: expected YYYY-MM-DD, got {rec[f]!r}")
    if is_date(rec.get("issued")) and is_date(rec.get("expires")) \
            and parse_date(rec["expires"]) < parse_date(rec["issued"]):
        problems.append("expires: earlier than issued")
    if rec.get("confidence") is not None and rec["confidence"] not in CONFIDENCE:
        problems.append(f"confidence: expected one of {', '.join(CONFIDENCE)}")
    if rec.get("confirmed") not in (None, True, False):
        problems.append("confirmed: expected true or false")
    if rec.get("tags") is not None and not isinstance(rec["tags"], list):
        problems.append("tags: expected a list like [a, b]")
    if rec.get("number") and not allow_full_numbers and mask_number(rec["number"]) != str(rec["number"]):
        problems.append("number: store only the last 4 characters (e.g. ****1234)")
    for k in rec:
        if k not in FIELDS and not k.startswith("x_"):
            problems.append(f"{k}: unknown field (use an x_ prefix for custom fields)")
    return problems


# ---------------------------------------------------------------- documents

def type_from_label(label) -> str | None:
    if not label:
        return None
    wanted = label.strip().lower()
    for key, (default, _) in TYPES.items():
        if wanted in (default.lower(), key.replace("_", " ")):
            return key
    return None


def load_items(data) -> list[dict]:
    if isinstance(data, dict):
        data = data.get("items") or data.get("documents") or data.get("files") or []
    items = []
    for x in data:
        if isinstance(x, str):
            x = {"name": x}
        if not isinstance(x, dict):
            raise LifeboxError(f"unsupported item: {x!r}")
        rec = x.get("record")
        if rec is None and isinstance(x.get("description"), str) and "lifebox:" in x["description"]:
            rec = parse_record(x["description"])[0]
        if rec is None:
            rec = {k: v for k, v in x.items() if k in FIELDS}
        parsed = parse_name(x["name"]) if x.get("name") else {}
        typ = rec.get("type") or type_from_label(parsed.get("label")) or "other"
        items.append({
            "name": x.get("name"),
            "id": x.get("id"),
            "link": x.get("link") or x.get("url") or rec.get("link"),
            "type": typ,
            "title": rec.get("title") or parsed.get("label") or TYPES.get(typ, ("Document",))[0],
            "holder": rec.get("holder") or parsed.get("holder"),
            "expires": rec.get("expires") or parsed.get("expires"),
            "renew_by": rec.get("renew_by"),
        })
    return items


def radar(items: list[dict], today: date, window: int = 90, include_all: bool = False) -> dict:
    out, counts = [], {"expired": 0, "urgent": 0, "soon": 0, "ok": 0, "no_expiry": 0}
    for it in items:
        if not it["expires"]:
            counts["no_expiry"] += 1
            if include_all:
                out.append({**it, "days_left": None, "status": "no_expiry"})
            continue
        exp = parse_date(it["expires"], f"{it['title']} expires")
        left = (exp - today).days
        status = "expired" if left < 0 else "urgent" if left <= 30 else "soon" if left <= window else "ok"
        counts[status] += 1
        renew_by = it.get("renew_by")
        if not renew_by:
            offsets = TYPES.get(it["type"], ("", []))[1]
            renew_by = (exp - timedelta(days=max(offsets))).isoformat() if offsets else None
        if status != "ok" or include_all:
            out.append({**it, "days_left": left, "status": status, "renew_by": renew_by})
    order = {"expired": 0, "urgent": 1, "soon": 2, "ok": 3, "no_expiry": 4}
    out.sort(key=lambda r: (order[r["status"]], r["days_left"] if r["days_left"] is not None else 10**9))
    return {"today": today.isoformat(), "window_days": window, "counts": counts, "items": out}


def radar_markdown(report: dict) -> str:
    if not report["items"]:
        return f"Nothing expires in the next {report['window_days']} days."
    lines = []
    for r in report["items"]:
        who = f" ({r['holder']})" if r.get("holder") else ""
        if r["status"] == "expired":
            when = f"expired {-r['days_left']} days ago"
        elif r["status"] == "no_expiry":
            when = "no expiry date"
        else:
            when = f"{r['days_left']} days left ({r['expires']})"
        title = f"[{r['title']}{who}]({r['link']})" if r.get("link") else f"{r['title']}{who}"
        lines.append(f"- **{r['status']}** · {title} — {when}")
    return "\n".join(lines)


def uid_for(*parts) -> str:
    digest = hashlib.sha1("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:20]
    return f"{digest}@lifebox"


def reminders(items: list[dict], today: date, offsets_override: list[int] | None = None) -> dict:
    events = []
    for it in items:
        if not it["expires"]:
            continue
        exp = parse_date(it["expires"], f"{it['title']} expires")
        who = f" ({it['holder']})" if it.get("holder") else ""
        offsets = offsets_override if offsets_override is not None else TYPES.get(it["type"], ("", [30]))[1]
        base = (it["type"], it.get("holder") or "", it["expires"], it["title"])
        for d in sorted(set(offsets), reverse=True):
            when = exp - timedelta(days=d)
            if when < today:
                continue
            events.append({
                "uid": uid_for(*base, d), "date": when.isoformat(),
                "title": f"{it['title']}{who} expires in {d} days",
                "description": f"{it['title']}{who} expires on {it['expires']}.",
                "url": it.get("link"), "alarms": [0],
            })
        if exp >= today:
            events.append({
                "uid": uid_for(*base, "expiry"), "date": exp.isoformat(),
                "title": f"{it['title']}{who} expires today",
                "description": f"{it['title']}{who} expires on {it['expires']}.",
                "url": it.get("link"), "alarms": [0],
            })
    events.sort(key=lambda e: (e["date"], e["title"]))
    return {"events": events}


# ---------------------------------------------------------------- recipes

def recipes_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "references" / "recipes"


def _block(text: str, name: str) -> list[str]:
    m = re.search(r"^```" + re.escape(name) + r"[ \t]*\n(.*?)^```", text, re.S | re.M)
    if not m:
        return []
    return [ln.rstrip() for ln in m.group(1).splitlines() if ln.strip() and not ln.lstrip().startswith("#")]


def load_recipe(ref: str) -> dict:
    path = Path(ref)
    if not path.suffix:
        path = recipes_dir() / f"{ref}.md"
    if not path.is_file():
        raise LifeboxError(f"recipe not found: {ref}")
    text = path.read_text(encoding="utf-8")
    meta, body = parse_record(text)
    steps = []
    for ln in _block(body, "lifebox-steps"):
        parts = ln.split(None, 2)
        if len(parts) < 3 or not re.fullmatch(r"[+-]?\d+", parts[0]):
            raise LifeboxError(f"{path.name}: bad step line {ln!r} (expected 'OFFSET id title')")
        steps.append({"offset": int(parts[0]), "id": parts[1], "title": parts[2]})
    documents = []
    for ln in _block(body, "lifebox-documents"):
        parts = ln.split(None, 2)
        if len(parts) < 3 or parts[1] not in NEEDS:
            raise LifeboxError(f"{path.name}: bad document line {ln!r} (expected 'type need label')")
        documents.append({"type": parts[0], "need": parts[1], "label": parts[2]})
    return {**meta, "path": str(path), "steps": steps, "documents": documents}


def list_recipes() -> list[dict]:
    out = []
    for p in sorted(recipes_dir().glob("*.md")):
        r = load_recipe(str(p))
        out.append({k: r.get(k) for k in ("id", "title", "anchor", "applies_to", "summary")})
    return out


def plan(recipe: dict, anchor: date, today: date) -> dict:
    steps = []
    for s in sorted(recipe["steps"], key=lambda s: s["offset"]):
        due = anchor + timedelta(days=s["offset"])
        steps.append({**s, "date": due.isoformat(), "late": due < today})
    return {"recipe": recipe.get("id"), "title": recipe.get("title"), "anchor": anchor.isoformat(),
            "today": today.isoformat(), "steps": steps, "documents": recipe["documents"]}


def plan_markdown(p: dict) -> str:
    lines = ["## Steps"]
    for s in p["steps"]:
        when = f"ASAP (was {s['date']})" if s["late"] else s["date"]
        lines.append(f"- [ ] {when} · {s['title']} `{s['id']}`")
    return "\n".join(lines)


def plan_events(p: dict, holder: str | None = None) -> dict:
    who = f" ({holder})" if holder else ""
    events = []
    for s in p["steps"]:
        if s["late"]:
            continue
        events.append({
            "uid": uid_for(p["recipe"], p["anchor"], holder or "", s["id"]),
            "date": s["date"], "title": f"{s['title']}{who}",
            "description": f"{p['title']}{who} — step '{s['id']}'. Deadline {p['anchor']}.",
            "alarms": [0],
        })
    return {"events": events}


# ---------------------------------------------------------------- iCalendar

def _ics_text(s: str) -> str:
    return (s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
             .replace("\r\n", "\\n").replace("\n", "\\n"))


def _fold(line: str) -> str:
    out, cur, size = [], "", 0
    limit = 75
    for ch in line:
        n = len(ch.encode("utf-8"))
        if size + n > limit:
            out.append(cur)
            cur, size, limit = " ", 1, 75
        cur += ch
        size += n
    out.append(cur)
    return "\r\n".join(out)


def _trigger(days_before: int) -> str:
    if days_before <= 0:
        return f"PT{ALARM_HOUR}H"
    return f"-PT{days_before * 24 - ALARM_HOUR}H"


def to_ics(events: list[dict], calname: str = "Lifebox", dtstamp: datetime | None = None) -> str:
    stamp = (dtstamp or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:-//lifebox//lifebox {VERSION}//EN",
             "CALSCALE:GREGORIAN", "METHOD:PUBLISH", f"X-WR-CALNAME:{_ics_text(calname)}"]
    for e in events:
        start = parse_date(e["date"], "event date")
        end = start + timedelta(days=1)
        uid = e.get("uid") or uid_for(e["date"], e["title"])
        lines += ["BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{stamp}",
                  f"DTSTART;VALUE=DATE:{start:%Y%m%d}", f"DTEND;VALUE=DATE:{end:%Y%m%d}",
                  f"SUMMARY:{_ics_text(e['title'])}"]
        desc = e.get("description") or ""
        if e.get("url"):
            desc = (desc + "\n" if desc else "") + e["url"]
            lines.append(f"URL:{e['url']}")
        if desc:
            lines.append(f"DESCRIPTION:{_ics_text(desc)}")
        lines.append("TRANSP:TRANSPARENT")
        for d in e.get("alarms", [0]):
            lines += ["BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:{_ics_text(e['title'])}",
                      f"TRIGGER:{_trigger(int(d))}", "END:VALARM"]
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold(ln) for ln in lines) + "\r\n"


# ---------------------------------------------------------------- MRZ (ICAO 9303)

def mrz_check_digit(field: str) -> int:
    total = 0
    for i, ch in enumerate(field):
        if ch.isdigit():
            v = int(ch)
        elif "A" <= ch <= "Z":
            v = ord(ch) - 55
        else:
            v = 0
        total += v * (7, 3, 1)[i % 3]
    return total % 10


def _check(field: str, digit: str) -> bool:
    return digit.isdigit() and mrz_check_digit(field) == int(digit)


def _mrz_date(yymmdd: str, kind: str, today: date) -> str | None:
    if not re.fullmatch(r"\d{6}", yymmdd):
        return None
    yy, mm, dd = int(yymmdd[:2]), int(yymmdd[2:4]), int(yymmdd[4:])
    if kind == "birth":
        year = 1900 + yy if yy > today.year % 100 else 2000 + yy
    else:
        year = 2000 + yy
    try:
        return date(year, mm, dd).isoformat()
    except ValueError:
        return None


def _names(field: str) -> tuple[str, str]:
    surname, _, given = field.partition("<<")
    clean = lambda s: re.sub(r"<+", " ", s).strip()  # noqa: E731
    return clean(surname), clean(given)


def parse_mrz(text: str, today: date | None = None, full_number: bool = False) -> dict:
    today = today or date.today()
    lines = [re.sub(r"\s+", "", ln).upper() for ln in text.splitlines()]
    lines = [ln for ln in lines if re.fullmatch(r"[A-Z0-9<]{30,44}", ln)]
    res: dict = {}
    for i in range(len(lines)):
        a = lines[i]
        b = lines[i + 1] if i + 1 < len(lines) else ""
        c = lines[i + 2] if i + 2 < len(lines) else ""
        if "<" not in a + b:
            continue
        if len(a) == 44 and len(b) == 44:  # TD3 (passport)
            number, nchk = b[0:9], b[9]
            surname, given = _names(a[5:44])
            res = {"format": "TD3", "document_code": a[0:2].replace("<", ""), "issuing_state": a[2:5],
                   "number": number.replace("<", ""), "nationality": b[10:13],
                   "birth_date": _mrz_date(b[13:19], "birth", today), "sex": b[20],
                   "expiry_date": _mrz_date(b[21:27], "expiry", today),
                   "surname": surname, "given_names": given,
                   "checks": {"number": _check(number, nchk), "birth": _check(b[13:19], b[19]),
                              "expiry": _check(b[21:27], b[27]),
                              "optional": b[42] == "<" and set(b[28:42]) <= {"<"} or _check(b[28:42], b[42]),
                              "composite": _check(b[0:10] + b[13:20] + b[21:43], b[43])}}
            break
        if len(a) == 36 and len(b) == 36:  # TD2
            number, nchk = b[0:9], b[9]
            surname, given = _names(a[5:36])
            res = {"format": "TD2", "document_code": a[0:2].replace("<", ""), "issuing_state": a[2:5],
                   "number": number.replace("<", ""), "nationality": b[10:13],
                   "birth_date": _mrz_date(b[13:19], "birth", today), "sex": b[20],
                   "expiry_date": _mrz_date(b[21:27], "expiry", today),
                   "surname": surname, "given_names": given,
                   "checks": {"number": _check(number, nchk), "birth": _check(b[13:19], b[19]),
                              "expiry": _check(b[21:27], b[27]),
                              "composite": _check(b[0:10] + b[13:20] + b[21:35], b[35])}}
            break
        if len(a) == 30 and len(b) == 30 and len(c) == 30:  # TD1 (ID card)
            number, nchk, opt1 = a[5:14], a[14], a[15:30]
            if nchk == "<" and opt1.strip("<"):  # long document number continues in optional data
                tail = opt1.split("<", 1)[0]
                number, nchk = number + tail[:-1], tail[-1]
            surname, given = _names(c)
            res = {"format": "TD1", "document_code": a[0:2].replace("<", ""), "issuing_state": a[2:5],
                   "number": number.replace("<", ""), "nationality": b[15:18],
                   "birth_date": _mrz_date(b[0:6], "birth", today), "sex": b[7],
                   "expiry_date": _mrz_date(b[8:14], "expiry", today),
                   "surname": surname, "given_names": given,
                   "checks": {"number": _check(number, nchk), "birth": _check(b[0:6], b[6]),
                              "expiry": _check(b[8:14], b[14]),
                              "composite": _check(a[5:30] + b[0:7] + b[8:15] + b[18:29], b[29])}}
            break
    if not res:
        raise LifeboxError("no machine-readable zone found (expected 2x44, 2x36 or 3x30 characters)")
    res["valid"] = all(res["checks"].values())
    if not full_number:
        res["number"] = mask_number(res["number"])
    return res


# ---------------------------------------------------------------- CLI

def _read_stdin_json():
    raw = sys.stdin.read()
    if not raw.strip():
        raise LifeboxError("expected JSON on stdin")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LifeboxError(f"stdin is not valid JSON: {exc}") from None


def _print_json(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def _today(args) -> date:
    return parse_date(args.today, "--today") if args.today else date.today()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="lifebox.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"lifebox {VERSION}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_name = sub.add_parser("name", help="format or parse canonical file names")
    name_sub = p_name.add_subparsers(dest="action", required=True)
    p_nf = name_sub.add_parser("format", help="record JSON on stdin -> file name")
    p_nf.add_argument("--ext", help="file extension, e.g. .pdf")
    p_np = name_sub.add_parser("parse", help="parse file names")
    p_np.add_argument("names", nargs="+")

    p_meta = sub.add_parser("meta", help="parse, emit or validate records")
    meta_sub = p_meta.add_subparsers(dest="action", required=True)
    meta_sub.add_parser("parse", help="record text on stdin -> JSON")
    p_me = meta_sub.add_parser("emit", help="record JSON on stdin -> record text")
    p_me.add_argument("--frontmatter", action="store_true", help="wrap in --- for a sidecar file")
    p_me.add_argument("--full-numbers", action="store_true", help="do not mask the number field")
    p_mv = meta_sub.add_parser("validate", help="record text or JSON on stdin -> problems")
    p_mv.add_argument("--full-numbers", action="store_true", help="allow unmasked numbers")

    p_radar = sub.add_parser("radar", help="expiry report for documents (JSON on stdin)")
    p_radar.add_argument("--today")
    p_radar.add_argument("--days", type=int, default=90, help="look-ahead window (default 90)")
    p_radar.add_argument("--all", action="store_true", help="include documents that are fine")
    p_radar.add_argument("--format", choices=("json", "md"), default="json")

    p_rem = sub.add_parser("reminders", help="calendar events for expiring documents (JSON on stdin)")
    p_rem.add_argument("--today")
    p_rem.add_argument("--offsets", help="comma-separated days before expiry, overrides type defaults")

    sub.add_parser("recipes", help="list bundled recipes")

    p_plan = sub.add_parser("plan", help="dated steps for a recipe")
    p_plan.add_argument("--recipe", required=True, help="recipe id or path")
    p_plan.add_argument("--anchor", required=True, help="deadline the recipe counts from (YYYY-MM-DD)")
    p_plan.add_argument("--today")
    p_plan.add_argument("--holder")
    p_plan.add_argument("--format", choices=("json", "md", "events"), default="json")

    p_ics = sub.add_parser("ics", help="events JSON on stdin -> iCalendar")
    p_ics.add_argument("--name", default="Lifebox", help="calendar name")
    p_ics.add_argument("--dtstamp", help="fixed DTSTAMP (YYYY-MM-DDTHH:MM:SSZ), for reproducible output")
    p_ics.add_argument("-o", "--output", help="write to this file instead of stdout")

    p_mrz = sub.add_parser("mrz", help="MRZ text on stdin -> passport/ID fields")
    p_mrz.add_argument("--today")
    p_mrz.add_argument("--full-number", action="store_true", help="do not mask the document number")

    args = ap.parse_args(argv)
    try:
        if args.cmd == "name":
            if args.action == "format":
                data = _read_stdin_json()
                recs = data if isinstance(data, list) else [data]
                names = [format_name(r, args.ext) for r in recs]
                _print_json(names if isinstance(data, list) else names[0])
            else:
                _print_json([parse_name(n) for n in args.names])
        elif args.cmd == "meta":
            if args.action == "parse":
                rec, body = parse_record(sys.stdin.read())
                _print_json({"record": rec, "body": body})
            elif args.action == "emit":
                data = _read_stdin_json()
                rec = data.get("record", data) if isinstance(data, dict) else data
                print(emit_record(rec, mask=not args.full_numbers, frontmatter=args.frontmatter,
                                  body=data.get("body", "") if isinstance(data, dict) else ""))
            else:
                raw = sys.stdin.read()
                try:
                    rec = json.loads(raw)
                    rec = rec.get("record", rec)
                except json.JSONDecodeError:
                    rec = parse_record(raw)[0]
                problems = validate_record(rec, allow_full_numbers=args.full_numbers)
                _print_json({"valid": not problems, "problems": problems})
                return 0 if not problems else 1
        elif args.cmd == "radar":
            report = radar(load_items(_read_stdin_json()), _today(args), args.days, args.all)
            if args.format == "md":
                print(radar_markdown(report))
            else:
                _print_json(report)
        elif args.cmd == "reminders":
            offsets = [int(x) for x in args.offsets.split(",")] if args.offsets else None
            _print_json(reminders(load_items(_read_stdin_json()), _today(args), offsets))
        elif args.cmd == "recipes":
            _print_json(list_recipes())
        elif args.cmd == "plan":
            p = plan(load_recipe(args.recipe), parse_date(args.anchor, "--anchor"), _today(args))
            if args.format == "md":
                print(plan_markdown(p))
            elif args.format == "events":
                _print_json(plan_events(p, args.holder))
            else:
                _print_json(p)
        elif args.cmd == "ics":
            data = _read_stdin_json()
            events = data.get("events", []) if isinstance(data, dict) else data
            stamp = None
            if args.dtstamp:
                stamp = datetime.strptime(args.dtstamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            text = to_ics(events, args.name, stamp)
            if args.output:
                Path(args.output).write_text(text, encoding="utf-8", newline="")
                print(f"wrote {len(events)} events to {args.output}")
            else:
                sys.stdout.write(text)
        elif args.cmd == "mrz":
            _print_json(parse_mrz(sys.stdin.read(), _today(args), args.full_number))
    except LifeboxError as exc:
        print(f"lifebox: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
