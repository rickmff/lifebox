# Dropbox

Status: **experimental**. Through a Dropbox connector or MCP server. Abilities differ between
connectors, so check what is available before choosing a mode.

## Pick a mode

1. **Primary vault** — the connector can list folders, read files, move/rename files and upload
   small text files. Use the layout from `vault-spec.md` with sidecar records
   (`<name without extension>.lifebox.md`); Dropbox has no description field.
2. **Linked source** — the connector can only search and read. Keep each record as a **pointer
   record** in the user's primary vault (Google Drive, Notion or a local folder), with
   `source: linked` and `link` set to the Dropbox link.
3. **Local sync** — if the Dropbox desktop app syncs the folder, Claude Code and Cowork get full
   support through `local.md`.

## Operations (primary vault mode)

| Operation | Look for |
|---|---|
| Find / list | List folder contents of `/Lifebox/...` |
| Read | Download or read file content |
| Rename / move | Move file (rename = move within the same folder) |
| Records and text files | Upload a small text file, overwriting to update |
| Link | A shared link only if the user asks to share; otherwise the path |

If any of these is missing, fall back to linked-source mode and tell the user which operation the
connector lacks. When you verify this adapter with a real connector, record which tools worked.
