# Storage adapters

An adapter is a markdown file in
[`skills/lifebox/references/storage/`](../skills/lifebox/references/storage) that tells Claude how
to perform the vault operations with one storage service's tools.

| Adapter | Status | Records |
|---|---|---|
| [Google Drive](../skills/lifebox/references/storage/google-drive.md) | Verified | File description |
| [Local folder](../skills/lifebox/references/storage/local.md) | Verified | `.lifebox.md` sidecar files |
| [Notion](../skills/lifebox/references/storage/notion.md) | To verify | Database properties |
| [OneDrive / SharePoint](../skills/lifebox/references/storage/onedrive-sharepoint.md) | Experimental | Sidecars, or linked documents |
| [Dropbox](../skills/lifebox/references/storage/dropbox.md) | Experimental | Sidecars, or linked documents |
| [Box](../skills/lifebox/references/storage/box.md) | Experimental | File description or sidecars |

- **Verified:** the operations were exercised with the real connector tools.
- **To verify:** written against the connector's documented tools, not yet exercised end to end.
- **Experimental:** connectors differ; the adapter tells Claude to check what is available and to
  fall back to linked documents when it can't write.

## Operations every adapter covers

| Operation | Needed for |
|---|---|
| Find or create the vault | Setup |
| List a folder | Radar, inbox |
| Read a document | Filing, questions |
| Read and write a record | Filing, radar details |
| Rename and move | Filing |
| Create and replace a text file | README, plans, `.ics` |
| Search contents | Questions |
| Share | Only on explicit request |
| Link to a file | Every answer |

If a storage can only be read, it can still be a **linked source**: the documents stay there and
the records live as pointer records in a writable vault.

## Add or verify an adapter

1. Copy an existing adapter and fill in the operations table with the connector's tool names.
2. Try every operation with a throwaway `Lifebox (test)` folder and fake documents (never real
   ones).
3. Note which tools worked and any limits (file size, read-only fields, rate limits).
4. Open a pull request that updates the adapter, its status here and in the README.
