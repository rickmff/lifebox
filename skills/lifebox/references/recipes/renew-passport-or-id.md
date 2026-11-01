---
id: renew-passport-or-id
title: Renew a passport or ID card
anchor: expiry date of the passport or ID card
applies_to: [passport, national_id]
summary: Gather the documents, book the appointment and renew before the old document expires.
reviewed: 2026-11-01
---
# Renew a passport or ID card

Generic template. Rules, fees and processing times depend on the issuing country and, for people
living abroad, on the consulate. Always run the `localize` step first.

## Steps

```lifebox-steps
-270 localize     Confirm the rules, fees, processing time and where to apply (official sources)
-240 travel       Check upcoming trips: many destinations require 3–6 months of remaining validity
-210 photos       Get photos that meet the official specification, if they are not taken on site
-210 forms        Fill in the application form and gather the documents below
-180 appointment  Book the appointment (consulates and agencies can have long queues)
-150 submit       Attend the appointment or submit online, and pay the fee
-60  collect      Collect the new document or confirm its delivery
0    expiry       The old document expires: file the new one in lifebox
```

## Documents

```lifebox-documents
passport           depends   Current passport (when renewing a passport)
national_id        depends   Current ID card (when renewing an ID card)
birth_certificate  depends   Birth certificate (first issue, minors or a change of name)
proof_of_address   depends   Recent proof of address (some countries and consulates)
residence_permit   depends   Residence permit (when applying at a consulate abroad)
other              depends   Photos meeting the official specification
```

## Localize

Confirm: the issuing country; whether the user lives there or abroad (consulate); adult or minor;
any trip coming up. Then look up on the official website: required documents, fee, how to book,
processing time, whether the old document is handed in or returned cancelled, and the rules for a
change of name.

## Tips

- If appointments are scarce, renew the passport and the ID card in the same visit.
- A valid visa in the old passport usually stays valid with it: ask for the old passport back.
