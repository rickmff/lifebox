# Weekly review (optional)

A scheduled task that looks at the vault once a week and tells the user what needs attention.
Calendar reminders already cover expiry dates; the review adds plan steps and the Inbox.

## Prompt

Give the user this prompt with the storage filled in:

```
Use the lifebox skill to review my vault in <Google Drive | Notion | ~/Lifebox>.
Do not move, rename, create or delete anything.
1. Run the expiry radar for the next 90 days.
2. List plan steps that are overdue or due in the next 14 days.
3. Count the files waiting in Lifebox/Inbox.
Reply in at most 10 short lines. If nothing needs attention, reply "lifebox: all clear".
```

## Where to schedule it

- **Claude Desktop (Cowork)** — create a scheduled task with the prompt. It runs on the user's
  computer while the app is open, so it can use a local folder or the connectors.
- **Claude Code** — `/schedule` creates a cloud task. It can only reach storage that is connected
  as a connector on the user's Claude account, not a local folder.
- **Claude.ai** — if the user's plan offers scheduled tasks, the same prompt works there.

Scheduled tasks are a newer feature and availability depends on the plan; describe the steps but
let the user create the task. The review is read-only by design: anything it finds is fixed in a
normal conversation.
