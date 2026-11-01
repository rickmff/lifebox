# Reminders and schedules

Reminders are ordinary calendar events, so they reach the user's phone without any lifebox
service running. Always show the list of events (date + title) and where they will go, and wait
for the user's OK before writing to a calendar.

## Default offsets

Days before expiry when a reminder event is created. `lifebox.py reminders` uses this table; keep
the two in sync.

| Type | Offsets (days) | Why |
|---|---|---|
| `passport` | 270, 180, 90 | Many destinations require 3–6 months of remaining validity; renewals can take months |
| `national_id` | 180, 90, 30 | Appointments can be scarce |
| `residence_permit` | 120, 60, 30, 7 | Renewal windows are strict in most countries |
| `visa` | 90, 30, 7 | Extensions must be requested before expiry |
| `driver_license` | 120, 60, 14 | Some countries need a medical certificate first |
| `vehicle_registration` | 60, 14 | |
| `vehicle_inspection` | 60, 21, 7 | Leave time for repairs and a re-test |
| `vehicle_insurance` | 45, 14 | Time to compare quotes before automatic renewal |
| `insurance_policy` | 45, 14 | Cancellation notice periods often apply |
| `health_insurance` | 45, 14 | |
| `lease` | 120, 90, 30 | Notice periods are often 1–3 months |
| `employment_contract` | 60, 14 | |
| `medical` | 30 | |
| `warranty` | 30 | Claim before it ends |
| `other` | 30 | |

Types not listed get only an event on the expiry day. The user can ask for other offsets
(`lifebox.py reminders --offsets 60,7`).

## Build the events

- Documents: `lifebox.py reminders --today YYYY-MM-DD` with the documents on stdin (records, or just
  canonical file names).
- Plans: `lifebox.py plan --recipe ID --anchor YYYY-MM-DD --holder NAME --format events`.

Both give events with a stable `uid`, an all-day `date`, a `title` and the document `url`.

## Deliver them (first option that works)

1. **Calendar connector.** If a tool that creates calendar events is available (Google Calendar,
   Microsoft 365/Outlook, Notion Calendar, …): first list the user's events in the same date range
   and skip titles that already exist, then create all-day events with the title as is and the
   document link plus "Created by lifebox" in the description. Use the calendar named in README
   `calendar` when the connector lets you pick one.
2. **`.ics` file.** Pipe the events into `lifebox.py ics -o lifebox.ics`, hand the file to the user
   (download in Claude.ai, path in Claude Code) and save a copy as `Lifebox/lifebox.ics`. Import:
   Google Calendar → Settings → Import & export → Import (pick a dedicated "Lifebox" calendar);
   Apple Calendar → open the file; Outlook → File → Open & Export → Import/Export. Google Calendar
   ignores alarms inside imported files and applies its default notifications, which is why
   lifebox creates separate events on each reminder day. Re-importing the same file updates events
   in Apple Calendar and Outlook; in Google Calendar import only new events, or clear the Lifebox
   calendar first.
3. **No calendar.** List the dates in the chat and suggest the weekly review
   (`weekly-review.md`).

Never create events without confirmation, and never invite other people to them.
