# Privacy

lifebox is a set of instructions and a small script that run inside your own Claude
conversations. It has no server, collects nothing and sends nothing to its maintainers.

## Where your data goes

| Data | Where it lives | Who can see it |
|---|---|---|
| Your documents | Your storage (Google Drive, Notion, OneDrive, Dropbox, Box or your computer) | You, and anyone you share them with |
| Records (type, holder, dates, last 4 characters of numbers) | Next to the documents, in the same storage | Same as the documents |
| Document content Claude reads | Your Claude conversation | Handled under your Claude account's privacy settings |
| Calendar reminders | Your calendar | Same as your other events |

Claude only reads a document when a workflow needs it (filing, answering a question about its
content), through the connectors you turned on.

## What lifebox does to protect you

- Records keep only the last four characters of document numbers, unless you set
  `full_numbers: true` in the vault README.
- Records never store MRZ text, photos, signatures or other biometric data.
- Nothing is deleted: filing renames and moves files; old versions go to `Archive/`.
- Claude asks before sharing a file, trashing anything, overwriting a confirmed record or writing
  to your calendar, and never shares the whole vault.

## What you can do

- Keep the `Lifebox` folder private, and turn on two-factor authentication for your storage
  account.
- For the most control, keep the vault in a local folder and use Claude Code or Cowork.
- Review your Claude data settings and the connectors that are turned on.
- To remove lifebox, uninstall the skill and delete the `Lifebox` folder if you no longer want it.
  There is nothing else to delete.

Process guidance (recipes and plans) is general information, not legal advice. Check the official
source before acting.
