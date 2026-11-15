# OneDrive and SharePoint

Status: **experimental**. Through Claude's Microsoft 365 connector (offered on some plans) or
another OneDrive/SharePoint MCP server. Tool names and abilities differ between connectors, so
check what is available before choosing a mode.

## Pick a mode

1. **Primary vault** — the connector can list folders, read files, rename/move files and create
   text files. Use the layout from `vault-spec.md` with sidecar records
   (`<name without extension>.lifebox.md`), exactly like the local adapter but through the
   connector's tools.
2. **Linked source** — the connector can only search and read (common for read-only connectors).
   Leave the files where they are: read them in OneDrive/SharePoint and keep each record as a
   **pointer record** in the user's primary vault (Google Drive, Notion or a local folder), with
   `source: linked` and `link` set to the OneDrive/SharePoint URL.
3. **Local sync** — if the OneDrive desktop app syncs the folder, Claude Code and Cowork get full
   support through `local.md`.

## Operations (primary vault mode)

| Operation | Look for |
|---|---|
| Find / list | Folder listing or search scoped to the `Lifebox` folder |
| Read | File content or text extraction |
| Rename / move | Update item name / parent folder |
| Records and text files | Create or upload a small text file; replace it to update |
| Link | The item's web URL |

If any of these is missing, fall back to linked-source mode and tell the user which operation the
connector lacks.

When you verify this adapter with a real connector, record which tools worked so the project can
mark it verified.
