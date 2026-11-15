---
id: vehicle-inspection
title: Pass the periodic vehicle inspection
anchor: date the next inspection is due
applies_to: [vehicle_inspection, vehicle_registration]
summary: Book early, pre-check the car and leave time for repairs and a re-test.
reviewed: 2026-11-01
---
# Pass the periodic vehicle inspection

Generic template for roadworthiness inspections. When the first inspection is due, how often it
repeats and what is checked depend on the country and the vehicle. Always run the `localize` step
first.

## Steps

```lifebox-steps
-60 localize   Confirm when the inspection is due, the fee and where it can be done
-45 book       Book the inspection slot
-30 precheck   Pre-check lights, tyres, wipers, brakes, warning lights and windscreen; fix the obvious
-21 inspect    Take the vehicle to the inspection with the documents below
-14 retest     Buffer for repairs and a re-test if it fails
0   deadline   Inspection deadline: file the new certificate in lifebox
```

## Documents

```lifebox-documents
vehicle_registration  required  Vehicle registration certificate
vehicle_insurance     depends   Proof of valid insurance (some countries)
vehicle_inspection    depends   Previous inspection report
national_id           depends   ID of the person presenting the vehicle
```

## Localize

Confirm: the country where the vehicle is registered, its type and age, and whether the inspection
is tied to another deadline (road tax, registration renewal, emissions sticker). Look up the
official schedule, fee and approved inspection centres.

## Tips

- Registration renewals and road tax are often due around the same time: check the vault for
  `vehicle_registration` and `vehicle_insurance` dates while you are at it.
