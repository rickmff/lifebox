---
name: lifebox
description: Organizes personal life documents (passports, ID cards, residence permits, driver's licenses, insurance, leases, vehicle papers, bills, warranties) in the user's own Google Drive, Notion, OneDrive/SharePoint, Dropbox, Box or local folder. Files scans from an Inbox with clear names and metadata, answers questions about documents and expiry dates, builds dated checklists and schedules for renewals, moves and other paperwork, and creates calendar reminders. Use when the user talks about their documents or paperwork, expiry dates or renewals, asks what they need for a bureaucratic process, mentions lifebox, or writes things like "meus documentos", "quando vence", "renovar", "mis documentos", "papelada".
license: Apache-2.0
compatibility: Claude.ai, Claude Desktop (Cowork) and Claude Code. Needs a storage connector (Google Drive, Notion, Microsoft 365, Dropbox or Box) or access to a local folder. Code execution recommended.
metadata:
  version: "0.1.0"
  homepage: https://github.com/rickmff/lifebox
---

# lifebox

lifebox turns the place where the user already keeps files into an organized vault of life
documents. There is no lifebox server or database: you do the work through the user's connectors
or local files, following the conventions in `references/vault-spec.md`, and
`scripts/lifebox.py` handles names, records, dates and calendar files.

## Every time this skill starts

1. **Find the storage.** Use the one the user names. Otherwise use what you can reach: local file
   tools (Claude Code, Cowork) or a storage connector (Google Drive, Notion, Microsoft 365,
   Dropbox, Box). If there are several, ask once. Read the matching
   `references/storage/<adapter>.md` before the first operation. If you can reach none, tell the
   user to turn on a connector in Settings → Connectors (or open a folder in Claude Code or Cowork)
   and stop.
2. **Find the vault**: the folder (or Notion page) named `Lifebox`. Read `README.md` for the
   settings (holders, country, language, reminders). No vault yet → offer the setup below.
3. **Radar.** List `Documents/` (file names are enough), run
   `lifebox.py radar --format md --today <user's date>` on the names, and when anything is
   expired or due in the next 90 days, lead with that list (at most 5 lines). Mention how many
   files are waiting in `Inbox/`. Then do what the user asked. Don't repeat the radar later in the
   same conversation.

## Setup

1. Confirm the storage and where the vault goes (Drive: top of My Drive; local: a path the user
   chooses; Notion: a page they pick).
2. Ask whose documents will live there (holders), the country of residence, and how they want
   reminders: calendar events, an `.ics` file, or none.
3. Create `Lifebox/` with `Inbox/`, `Documents/`, `Archive/`, `Plans/` and a `README.md` from the
   template in `references/vault-spec.md`, in the user's language.
4. Explain how to add documents in that storage (Drive: the Drive app's **Scan** into
   `Lifebox/Inbox`, or **Save to Drive** from Gmail; local: copy files into `Inbox/`; Notion: a new
   row with the file attached) and offer to process the Inbox.
5. Ask whether some documents stay somewhere else (another drive, email, a portal): those become
   linked documents.

## Workflows

### Process the Inbox

For each file in `Inbox/`, oldest first, at most 10 per batch (then ask to continue):

1. Read it following `references/analysis.md`. Machine-readable zones go through
   `lifebox.py mrz`.
2. Build the record (`lifebox.py meta emit`), check it (`meta validate`) and build the canonical
   name (`lifebox.py name format --ext .pdf`).
3. Show one compact block per file: proposed name, type, holder, expiry, confidence. Ask one
   batched question for missing or `low` fields. If the user said to just file everything, ask
   only about `low` fields.
4. File it: rename, store the record the way the adapter says, move it to `Documents/` (or
   `Archive/` for expired, replaced or duplicate documents). Never delete anything.
5. Summarize what was filed and offer reminders for the new documents that expire.

### Link a document stored elsewhere

When a document lives in another drive, an email or a website, read it through that connector (or
ask the user for its details) and create a pointer record in `Documents/` with `source: linked`
and the link (see "Pointer records" in `references/vault-spec.md`). Don't copy the file.

### Answer questions

- "What do I have / when does X expire": answer from the listing and records, and link every
  document you mention.
- Questions about content ("which categories does my licence cover?"): read the document.
- Numbers: records keep only the last 4 characters. When the user asks for a full number, read it
  from the document and show it once; don't save it.
- When a document isn't in the vault, say so plainly. Never assume it exists.

### Plan a process (checklist and schedule)

For "what do I need to…", "make me a schedule to…", "help me renew…":

1. **Recipe.** Run `lifebox.py recipes` and read the one that fits. If none fits, build an ad-hoc
   plan with the same structure (steps as days before or after a deadline, documents with types)
   and say it is ad hoc.
2. **Localize, always.** Take the country and city from the README or ask. Search the web for the
   official rules (government or issuer sites), adjust steps, lead times and the documents list,
   and keep the sources with today's date. Mark anything you could not verify as "to confirm".
3. **Anchor.** Find the deadline: a document's expiry in the vault, or ask (moving day, lease end).
4. **Match documents.** For each document in the plan, look for a vault document with that type
   and holder that is still valid on the deadline: have it (link), expires before the deadline
   (renew it first), or missing (how to get it, from your research).
5. **Dates.** `lifebox.py plan --recipe <id> --anchor <date> --today <date> --format md`. Late
   steps show as ASAP.
6. Show the plan. When the user is happy with it, save it in `Plans/` (format in
   `references/vault-spec.md`).
7. Offer to put the steps in the calendar (below).

### Update a plan

Tick steps and documents, add notes, move dates. Local and Notion: edit in place. Google Drive:
write the new version, then trash the old one. When everything is done set `status: done`.

### Reminders and calendar

Follow `references/reminders.md`: build events with `lifebox.py reminders` (documents) or
`lifebox.py plan --format events` (plans), show them, and only after the user agrees deliver them
through a calendar connector, an `.ics` file or a list in the chat.

### Weekly review

If the user wants a regular check, give them the prompt in `references/weekly-review.md` and
explain where to schedule it. Never say a schedule exists unless the user created it.

### Dashboard

For "show me my vault" or an overview: copy `references/dashboard.html`, replace only the JSON in
`#lifebox-data` (today; documents with title, holder, type, expires, link; plans with title,
holder, deadline, done, total, link) and show it as an artifact in Claude.ai, or save it as a file
and give the path in Claude Code.

### Share a document

Only when the user asks, with an explicit recipient. Use the narrowest option the adapter offers
(view-only, one file), confirm before sharing, and never share the whole vault.

## Rules

- Never invent documents, numbers, dates or requirements. Unknown means ask or leave it empty.
- Link every document you mention.
- Ask before trashing, sharing, overwriting a confirmed record or writing to a calendar. Never
  delete originals.
- Keep sensitive data out of records: last 4 characters of numbers, no MRZ text, photos or
  signatures.
- Process guidance is general information, not legal advice: cite official sources and the date
  you checked them.
- Reply in the user's language and write file labels in it; type keys stay in English.
- Keep tool output small: list folders without content snippets, read documents one at a time.

## Helper script

Run `python3 scripts/lifebox.py <command>` from this skill's folder. Commands read JSON or text on
stdin and print JSON or text. Pass `--today` with the user's local date when you know it.

| Command | Use |
|---|---|
| `name format --ext .pdf` / `name parse NAME…` | Build or read canonical file names |
| `meta emit [--frontmatter]` / `meta parse` / `meta validate` | Build, read and check records (numbers get masked) |
| `radar [--days 90] [--format md]` | Expiry report from file names or records |
| `reminders [--offsets 60,7]` | Calendar events for expiring documents |
| `recipes` | List the bundled recipes |
| `plan --recipe ID --anchor DATE [--format md\|events] [--holder NAME]` | Dated steps for a process |
| `ics [-o lifebox.ics]` | Turn events into an iCalendar file |
| `mrz` | Read a passport or ID machine-readable zone, with check digits |

Without code execution, follow the same formats by hand, do date math carefully and tell the user
to double-check the dates.

## References

- `references/vault-spec.md` — layout, file names, records, plans, filing rules. Read before
  creating, renaming or describing anything.
- `references/analysis.md` — how to read a document and judge confidence. Read before filing.
- `references/storage/google-drive.md`, `references/storage/local.md`,
  `references/storage/notion.md`, `references/storage/onedrive-sharepoint.md`,
  `references/storage/dropbox.md`, `references/storage/box.md` — read the one for the active
  storage before its first operation.
- `references/reminders.md` — before building reminders or writing to a calendar.
- `references/recipes/` — process templates; list them with `lifebox.py recipes`.
- `references/weekly-review.md` — when the user wants a regular check.
- `references/dashboard.html` — when the user wants a visual overview.
