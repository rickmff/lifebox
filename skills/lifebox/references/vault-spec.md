# Vault spec (`lifebox: 1`)

The vault is a set of conventions, not a database. It works in any storage that has folders and
file names. Read this before creating, renaming or describing anything.

## Layout

```
Lifebox/
  README.md     vault settings (frontmatter) + a short human explanation
  Inbox/        new files land here (phone scanner, share sheet, "Save to Drive", Finder)
  Documents/    filed documents with canonical names
  Archive/      expired, replaced or duplicate documents, kept for history
  Plans/        one markdown file per process: documents checklist + dated steps
  lifebox.ics   optional calendar export
```

Folder names are always these English names so every adapter and agent can find them. File labels,
plan titles and the README text use the user's language.

## Settings — `Lifebox/README.md`

```markdown
---
lifebox: 1
holders: [Alex, Sam]
country: PT
language: pt-BR
reminders: calendar
calendar: Lifebox
full_numbers: false
created: 2026-11-01
---
# Lifebox

This folder is organized by the lifebox skill for Claude. Put new documents in `Inbox/` and ask
Claude to "process my lifebox inbox". Documents are renamed `expiry · type · person` and filed in
`Documents/`. Nothing here is uploaded anywhere else.
```

| Key | Meaning |
|---|---|
| `holders` | People whose documents live here; ask before adding a new one |
| `country` | Default country (ISO 3166-1 alpha-2) used to localize recipes |
| `language` | Language for labels, summaries and replies |
| `reminders` | `calendar` (connector), `ics` (file to import) or `none` |
| `calendar` | Calendar name to use when the connector lets you pick one |
| `full_numbers` | `true` lets records keep full document numbers; default `false` (last 4 only) |

Read the README once per session. Where files can't be edited in place (Google Drive), change a
setting by writing a new README and trashing the old one.

## Canonical file names

```
<expiry> · <label> · <holder>[ · <qualifier>].<ext>

expiry     YYYY-MM-DD, or no-expiry
label      what the document is, in the user's language ("Carta de Condução", "Passport")
holder     the person it belongs to, as listed in README holders
qualifier  optional: front, back, page 2, a plate number, a policy name, duplicate
```

- Separator: space, middle dot (U+00B7), space.
- Remove `\ / : * ? " < > |` and control characters; a `·` inside a part becomes `-`; at most 60
  characters per part; lowercase extension.
- Examples: `2027-03-12 · Carta de Condução · Alex.pdf`,
  `2026-12-31 · Car Insurance · Sam · AA-12-BB.pdf`, `no-expiry · Birth Certificate · Sam.jpg`.

Why: name order is expiry order, `title contains '2027-03'` finds a month, people can read it, and
a plain folder listing already gives the radar what it needs. Always build and read names with
`scripts/lifebox.py name format` and `name parse`.

## Records

A record is the full metadata for one document: a flat YAML subset, one `key: value` per line.
Values are strings, dates (`YYYY-MM-DD`), `true`/`false` or flow lists (`[a, b]`). Build records
with `lifebox.py meta emit` (it quotes and masks for you) and check them with `meta validate`.

```yaml
lifebox: 1
type: driver_license
title: Carta de Condução
holder: Alex
issuer: IMT
country: PT
number: "****1234"
issued: 2017-03-12
expires: 2027-03-12
renew_by: 2026-11-12
tags: [car]
summary: Category B driving licence.
link: https://drive.google.com/file/d/FILE_ID/view
source: inbox
confidence: high
confirmed: true
updated: 2026-11-01
```

| Field | Notes |
|---|---|
| `lifebox` | Format version, always `1` |
| `type` | A key from the type table below |
| `title` | Label as written on the document, in the user's language |
| `holder` | Person the document belongs to |
| `issuer` | Authority or company that issued it |
| `country` | Issuing country, ISO 3166-1 alpha-2 |
| `number` | Last 4 characters only (`****1234`) unless `full_numbers: true` |
| `issued`, `expires` | Dates printed on the document; omit `expires` if there is none |
| `renew_by` | When to start renewing; default = expiry minus the largest reminder offset |
| `tags` | Free list |
| `summary` | One or two sentences, no numbers or full addresses |
| `link` | URL or path of the file (for pointer records: where the document really lives) |
| `source` | `inbox`, `linked`, `email` or `manual` |
| `confidence` | `high`, `medium` or `low` — the lowest among type, holder and expires |
| `confirmed` | `true` once the user confirmed the fields |
| `updated` | Date of the last change |

Custom fields start with `x_` (for example `x_plate: AA-12-BB`).

### Where records live

| Storage | Record location |
|---|---|
| Google Drive | The file's **description** (`update_file`); sidecars are honored if present |
| Local folder, Dropbox, Box, OneDrive | Sidecar file next to the document: `<same name without extension>.lifebox.md` |
| Notion | Properties of the row in the Lifebox database |

A sidecar holds the record as `---` frontmatter, optionally followed by free notes
(`lifebox.py meta emit --frontmatter`).

### Pointer records (linked documents)

For a document that stays somewhere else (another drive, an email, a web portal), create only the
record: a sidecar named with the canonical name, `source: linked` and `link` pointing to it. On
Google Drive, a pointer is a small `.lifebox.md` text file in `Documents/`; on Notion, a row with
the link and no file.

## Document types

| Type | Default label | Covers |
|---|---|---|
| `passport` | Passport | Passports |
| `national_id` | ID Card | National identity and citizen cards |
| `residence_permit` | Residence Permit | Residence permits and cards, long-stay authorizations |
| `visa` | Visa | Visas and entry permits |
| `driver_license` | Driver's License | Driving licences of any category |
| `vehicle_registration` | Vehicle Registration | Registration certificates, titles, road-tax receipts |
| `vehicle_inspection` | Vehicle Inspection | Periodic roadworthiness inspection certificates |
| `vehicle_insurance` | Vehicle Insurance | Car and motorbike insurance policies, green cards |
| `insurance_policy` | Insurance Policy | Home, life, travel, liability and other policies |
| `health_insurance` | Health Insurance | Health insurance cards and policies |
| `lease` | Lease | Rental and lease contracts |
| `employment_contract` | Employment Contract | Employment and service contracts |
| `tax_id` | Tax ID | Tax identification cards and certificates |
| `social_security` | Social Security | Social security cards and certificates |
| `utility_bill` | Utility Bill | Electricity, water, gas, internet and phone bills |
| `proof_of_address` | Proof of Address | Address certificates and declarations |
| `bank_statement` | Bank Statement | Bank statements and account certificates |
| `payslip` | Payslip | Payslips and income statements |
| `tax_return` | Tax Return | Tax returns and assessments |
| `birth_certificate` | Birth Certificate | Birth certificates |
| `marriage_certificate` | Marriage Certificate | Marriage and partnership certificates |
| `diploma` | Diploma | Diplomas, transcripts, course certificates |
| `medical` | Medical Document | Prescriptions, vaccination records, medical certificates |
| `warranty` | Warranty | Product warranties (expires = end of warranty) |
| `receipt` | Receipt | Purchase receipts |
| `invoice` | Invoice | Invoices |
| `form` | Form | Filled-in forms and submission receipts |
| `other` | Document | Anything else |

## Plans

One file per process in `Plans/`, named like documents with the deadline first:
`2027-03-12 · Renovar Carta de Condução · Alex.md`.

```markdown
---
lifebox: 1
plan: Renovar carta de condução
recipe: renew-driver-license
anchor: 2027-03-12
holder: Alex
country: PT
status: active
created: 2026-11-01
updated: 2026-11-01
sources: [https://official.example/renewal]
---
# Renovar carta de condução — Alex

Deadline: 2027-03-12 (licence expiry)

## Documents
- [x] Carta de condução — [2027-03-12 · Carta de Condução · Alex.pdf](LINK)
- [ ] Atestado médico — missing · how to get: …

## Steps
- [ ] 2026-11-12 · Confirm the local rules, fees and processing time `localize`
- [ ] 2026-12-12 · Submit the renewal `apply`

## Notes
- Sources checked on 2026-11-01: …
```

`status` is `active`, `done` or `cancelled`. Tick items with `[x]`. Generate the Steps section with
`lifebox.py plan --format md`. Where files can't be edited in place, update a plan by writing the
new version and trashing the old one.

## Filing rules

- Never delete an original. Filing = rename + record + move. Trash only on explicit request.
- Front and back of one document: same name with qualifiers `front` and `back`, same record.
- Duplicates (same type, holder and expiry): keep the best copy, move the other to `Archive/` with
  qualifier `duplicate`.
- A newer document replaces an older one (new passport): move the old one to `Archive/` and add
  `replaced` to its tags.
- Files that are not documents (photos, screenshots) stay in `Inbox/`; tell the user.
