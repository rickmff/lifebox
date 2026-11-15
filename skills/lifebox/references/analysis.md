# Reading a document

Goal: a correct record with honest confidence. A missing field is fine; a guessed field is not.

## 1. Get the content

- Use the storage adapter's read operation (text extraction). For scans and photos, also look at
  the image itself when the client lets you see it: IDs and cards need a visual check.
- Multi-page PDFs: keep reading until type, holder and dates are found; contracts often put dates
  on the first and last pages.
- If you only received text and it is garbled, say so and ask the user for a clearer scan instead
  of filling gaps.

## 2. Identify the type

Pick a key from the type table in `vault-spec.md`. Useful cues:

| Cue | Type |
|---|---|
| Two lines of 44 characters starting `P<` | `passport` |
| Three lines of 30 characters starting `I`, `A` or `C`; "identity card", "cartão de cidadão", "DNI", "carte d'identité", "Personalausweis" | `national_id` |
| "residence permit", "autorização/título de residência", "permiso de residencia", "titre de séjour", "Aufenthaltstitel", "permesso di soggiorno" | `residence_permit` |
| "driving licence", "carta de condução", "carteira nacional de habilitação", "licencia/permiso de conducir", "permis de conduire", "Führerschein", "patente di guida" | `driver_license` |
| Policy number + insured period + vehicle plate | `vehicle_insurance` |
| Policy number + insured period (home, life, travel, health) | `insurance_policy` / `health_insurance` |
| "lease", "contrato de arrendamento/aluguel", "contrato de alquiler", "bail", "Mietvertrag" | `lease` |
| Inspection result + plate + next inspection date | `vehicle_inspection` |
| Supplier, billing period, amount due, service address | `utility_bill` |

If two types fit, prefer the more specific one. If nothing fits, use `other` and say so.

## 3. Extract the fields

- **Machine-readable zone.** If the text has MRZ lines, run `lifebox.py mrz`. When `valid` is
  true, its dates and number win over anything read from the printed text.
- **Dates** → `YYYY-MM-DD`. A numeric date like `03/04/2027` is day-first in most countries and
  month-first in the United States and a few others: decide from the issuing country, and ask if
  it is still ambiguous. Two-digit expiry years are 20xx.
- **Expiry wording**: "valid until", "expiry date", "expires"; "válido até", "validade"; "válido
  hasta", "fecha de caducidad/vencimiento"; "date d'expiration", "valable jusqu'au"; "gültig bis",
  "Ablaufdatum"; "scadenza".
- **Issue wording**: "date of issue"; "data de emissão"; "fecha de expedición"; "date de
  délivrance"; "Ausstellungsdatum"; "data di rilascio".
- **Contracts and policies**: `issued` = start date, `expires` = end date or next renewal date;
  put renewal and notice terms in the summary ("renews yearly unless cancelled 30 days before").
- **Warranties**: `expires` = purchase date + warranty period when both are stated; otherwise ask.
- **Bills and statements**: usually no expiry. Keep the statement or billing date as `issued`; the
  recipes decide how recent they must be.
- **Number**: keep only the last 4 characters (`****1234`) unless the README says
  `full_numbers: true`. Never store MRZ text, signatures, photos or biometric data.
- **Holder**: the person named on the document, matched to README `holders`. If it is a new person,
  ask before adding them. Family policies: the policyholder, plus the others in the summary.
- **Issuer and country**: the authority or company, and its ISO country code.

## 4. Confidence

| Level | When |
|---|---|
| `high` | Printed clearly, or confirmed by a valid MRZ |
| `medium` | Readable but blurry, cropped or inferred from context |
| `low` | Partly guessed — must be confirmed by the user before filing |

The record's `confidence` is the lowest among `type`, `holder` and `expires`.

## 5. Summary

One or two sentences in the user's language: what the document is and what it is used for. No
numbers, no full addresses (a city is fine).

## 6. Confirm and file

Show the proposed file name and the key fields in one compact block, ask a single batched
question for anything missing or `low`, then file it (see the workflow in `SKILL.md`). Set
`confirmed: true` only after the user agreed.
