---
id: renew-driver-license
title: Renew a driver's license
anchor: expiry date of the driver's license
applies_to: [driver_license]
summary: Check medical requirements, apply and keep proof of renewal before the licence expires.
reviewed: 2026-11-01
---
# Renew a driver's license

Generic template. Who issues licences, when a medical or eye test is required and what a foreign
licence needs differ a lot between countries. Always run the `localize` step first.

## Steps

```lifebox-steps
-120 localize   Confirm the renewal rules, fee, and whether a medical certificate or eye test is needed
-100 medical    Get the medical certificate or eye test, if required
-90  photos     Get photos that meet the official specification, if required
-90  apply      Book the appointment or submit the online renewal, and pay the fee
-30  status     Check the application status; keep the receipt or temporary permit with you
0    expiry     The licence expires: carry the receipt if the new card has not arrived
```

## Documents

```lifebox-documents
driver_license    required  Current driver's license
national_id       depends   Passport or ID card
residence_permit  depends   Residence permit (foreign residents)
medical           depends   Medical certificate or eye test (some countries, ages or categories)
proof_of_address  depends   Recent proof of address (some countries)
other             depends   Photos meeting the official specification
```

## Localize

Confirm: the country of residence; whether the licence was issued by another country (it may need
to be exchanged rather than renewed, often within a deadline after becoming a resident); the
holder's age (older drivers often need medicals); professional categories (trucks, buses, taxis
usually have extra requirements). Then look up the official requirements, fee and booking system.

## Tips

- A medical certificate is usually only valid for a limited time: do not get it too early.
- Some countries let you renew online with an existing photo and signature on file.
