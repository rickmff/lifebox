# Notion

Status: **to verify**. Written against the Notion connector's tools (search, fetch, create and
update pages, create databases, query data sources, file uploads). On the first run, check each
step and tell the user if something behaves differently.

Notion has no folders, so the vault is a page holding a database:

- Page **Lifebox** — the README text, with the settings frontmatter in a code block.
- Database **Lifebox Documents** inside it, one row per document:

| Property | Notion type | Record field |
|---|---|---|
| Name | Title | canonical name without extension |
| Type | Select | `type` |
| Holder | Select | `holder` |
| Issuer | Text | `issuer` |
| Country | Text | `country` |
| Number | Text | `number` (masked) |
| Issued | Date | `issued` |
| Expires | Date | `expires` |
| Renew by | Date | `renew_by` |
| Tags | Multi-select | `tags` |
| Summary | Text | `summary` |
| Status | Select: Inbox, Filed, Archived | folder |
| Confidence | Select: high, medium, low | `confidence` |
| Confirmed | Checkbox | `confirmed` |
| File | Files & media | the document |
| Link | URL | `link` for linked documents |

- Plans — child pages of **Lifebox**, titled like plan files, with the steps as to-do blocks.

## Operations

| Operation | How |
|---|---|
| Find the vault | Search for the page "Lifebox", fetch it, find the "Lifebox Documents" database |
| Create the vault | Create the page, then the database with the properties above |
| Inbox | Rows with Status = Inbox. The user adds a row in the Notion app and attaches the file |
| List | Query the database: Status = Filed, sorted by Expires |
| Read a document | Fetch the row and read the attachment if the connector returns its content; otherwise ask the user for the key fields or to attach the file in the chat |
| Write a record | Update the row's properties |
| Rename | Update the Name property |
| Move / archive | Change Status |
| Plans and settings | Edit the pages in place (Notion allows it) |
| Share | Not through lifebox: point the user to Notion's Share menu |
| Link to a document | The row's URL |

## Notes

- Expiry queries can filter on the Expires property directly, so the radar can ask Notion for
  "Expires on or before today + 90 days".
- The Notion connector may also expose Notion Calendar tools that create events in calendars the
  user connected there. That counts as a calendar connector in `reminders.md`.
