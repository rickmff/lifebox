# Install lifebox

lifebox is a Claude skill packaged as a plugin. Install it once, connect the place where your
documents live, and ask Claude to set up the vault.

## 1. Add the skill

### Claude.ai and Claude Desktop

- **As a plugin:** in Claude, open the Customize menu, go to plugins and add this repository
  (`rickmff/lifebox`). Plugins added there also appear in Claude Desktop (Cowork) and Claude Code.
- **As a skill file:** download `lifebox-skill.zip` from the
  [latest release](https://github.com/rickmff/lifebox/releases) and upload it in the skills
  section of the Customize menu.

Skills need code execution to be turned on in your settings. Menu names can differ slightly
between plans.

### Claude Code

From a terminal:

```bash
claude plugin install lifebox --marketplace rickmff/lifebox
```

Or inside a session:

```
/plugin marketplace add rickmff/lifebox
/plugin install lifebox@lifebox
```

## 2. Connect your storage

| Where your documents live | What to do |
|---|---|
| Google Drive | Turn on the Google Drive connector (Settings → Connectors) |
| Notion | Turn on the Notion connector |
| OneDrive / SharePoint | Turn on the Microsoft 365 connector, where your plan offers it |
| Dropbox, Box | Turn on their connectors |
| A folder on your computer | Open it in Claude Code, or give Cowork access to it |

A folder synced by the Google Drive, Dropbox or OneDrive desktop apps works both ways: locally in
Claude Code or Cowork, and through the connector in Claude.ai on the web or your phone.

## 3. Set up the vault

Ask Claude: **"Set up lifebox in my Google Drive"** (or Notion, or this folder). Claude creates:

```
Lifebox/
  README.md   settings: who the documents belong to, country, reminders
  Inbox/      put new documents here
  Documents/  filed documents
  Archive/    expired or replaced documents
  Plans/      checklists and schedules
```

## 4. Add documents

- **Google Drive on your phone:** Drive app → **+** → **Scan**, save into `Lifebox/Inbox`.
- **Gmail:** open the attachment → **Save to Drive** → `Lifebox/Inbox`.
- **Computer:** copy files into `Lifebox/Inbox`.
- **Notion:** add a row to the Lifebox database and attach the file.

Then ask: **"Process my lifebox inbox."**

Files you attach directly in a chat can't be moved into your storage by Claude. Put them in the
Inbox instead.

## Troubleshooting

| Problem | Fix |
|---|---|
| Claude says it can't reach your storage | Check that the connector is on for this conversation |
| The skill does not kick in | Mention it: "use lifebox to…" |
| Dates or calendar files are not generated | Turn on code execution; without it Claude works by hand and asks you to double-check dates |
| A connector is read-only | Use it as a linked source: documents stay there, the vault keeps the records |
