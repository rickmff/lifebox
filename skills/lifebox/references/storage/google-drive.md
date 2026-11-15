# Google Drive

Status: **verified** against the Google Drive connector tools. Works wherever the connector is on:
Claude.ai (web, desktop, mobile), Cowork and Claude Code.

## Before you start

- The user needs the Google Drive connector turned on (Settings → Connectors). If no Drive tools are
  available, explain how to enable it and stop.
- Two limits shape this adapter:
  1. **No in-place edits of file content.** Title, folder and description can change; to change a
     text file (README, plan, `.ics`), create the new version and trash the old one.
  2. **Chat attachments can't be put into Drive** (the bytes would have to pass through you). Ask
     the user to drop files into `Lifebox/Inbox`: Drive app → **+** → **Scan**, the phone's share
     sheet → Drive, or Gmail attachment → **Save to Drive**.

## Operations

| Operation | How |
|---|---|
| Find the vault | `search_files` with `title = 'Lifebox' and mimeType = 'application/vnd.google-apps.folder' and owner = 'me' and trashed = false`; then its subfolders with `parentId = '<Lifebox id>' and mimeType = 'application/vnd.google-apps.folder'` |
| Create a folder | `create_file` with `title`, mime type `application/vnd.google-apps.folder` and `parentId` for subfolders |
| List a folder | `search_files` with `parentId = '<folder id>' and trashed = false`, `excludeContentSnippets: true`, `pageSize: 100`; follow the page token |
| Read a document | `read_file_content` (PDF, PNG, JPEG, Google Docs, text) |
| Read a record | `get_file_metadata` with `excludeContentSnippets: true` → `description` |
| Write a record | `update_file` with `description` = output of `lifebox.py meta emit` |
| Rename | `update_file` with `title` (from `lifebox.py name format`) |
| Move | `update_file` with `parentId` |
| Create a text file | `create_file` with `title`, `textContent`, `contentMimeType` (`text/markdown`, `text/calendar`), `disableConversionToGoogleType: true`, `parentId` |
| Replace a text file | create the new version, then `trash_file` the old one |
| Search contents | `search_files` with `fullText contains '<words>' and parentId = '<Documents id>'` |
| Share | `share_file`, only when the user asks, with the exact recipient and the narrowest role |
| Link to a file | `https://drive.google.com/file/d/<id>/view` |

## Notes

- A folder listing is enough for the radar: canonical names carry expiry, label and holder. Fetch
  metadata only for the documents you need in detail.
- Keep descriptions under about 1,500 characters.
- If a `<name>.lifebox.md` sidecar exists next to a document (a synced local vault), it wins over
  the description. Update both when you change one.
- Scans saved as Google Docs or PDFs read the same way.
- Trashed files stay recoverable in Drive's trash for 30 days.
