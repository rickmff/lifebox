# Local folder

Status: **verified**. Claude Code, and Claude Desktop/Cowork with access to a folder.

## Before you start

- Ask where the vault lives. Suggest `~/Lifebox`, or a folder synced by Google Drive, Dropbox or
  OneDrive desktop apps: then the same vault is also reachable from Claude.ai through that
  service's connector.
- You have the file tools: Read (shows you PDF pages and images), Write/Edit, Glob/Grep and the
  shell. Names contain spaces and `·`, so always quote paths.
- Run the helper from the skill folder: `python3 <skill folder>/scripts/lifebox.py …`.

## Operations

| Operation | How |
|---|---|
| Find the vault | Look for `Lifebox/README.md` in the folder the user named, the working directory, or `~/Lifebox` |
| Create the vault | `mkdir -p "Lifebox/Inbox" "Lifebox/Documents" "Lifebox/Archive" "Lifebox/Plans"`, then write `README.md` |
| List a folder | Glob `Lifebox/Documents/*`; skip `*.lifebox.md` when counting documents |
| Read a document | Read the file |
| Read / write a record | Sidecar `<name without extension>.lifebox.md` next to the document (`lifebox.py meta emit --frontmatter`) |
| Rename / move | `mv` the document and its sidecar together |
| Create / update text files | Write or Edit in place |
| Search contents | Grep over `Lifebox/Documents/*.lifebox.md` and text documents |
| Share | Not applicable: give the path |
| Link to a file | The absolute path |

## Notes

- In a synced folder, let the sync finish before reorganizing many files, and avoid editing the
  same file from two places at once.
- Never `rm` documents. Move them to `Archive/` instead.
