# Box

Status: **experimental**. Through the Box connector or Box MCP server. Abilities differ between
versions, so check what is available before choosing a mode.

## Pick a mode

1. **Primary vault** — the connector can list folders, read files, rename/move files and either
   set a file's description or upload small text files.
   - Box files have a description field: if the connector can update it, store the record there,
     exactly like `google-drive.md`.
   - Otherwise use sidecar records (`<name without extension>.lifebox.md`).
2. **Linked source** — the connector can only search and read. Keep each record as a **pointer
   record** in the user's primary vault (Google Drive, Notion or a local folder), with
   `source: linked` and `link` set to the Box URL.
3. **Local sync** — Box Drive syncs folders locally; Claude Code and Cowork can then use
   `local.md`.

## Operations (primary vault mode)

| Operation | Look for |
|---|---|
| Find / list | Search or list items in the `Lifebox` folder |
| Read | File text extraction (Box AI or content download) |
| Rename / move | Update file name / parent folder |
| Records | Update file description, or upload a sidecar text file |
| Link | The file's web URL |

If any of these is missing, fall back to linked-source mode and tell the user which operation the
connector lacks. When you verify this adapter with a real connector, record which tools worked.
