---
id: moving-house
title: Move house
anchor: moving day
applies_to: [lease, proof_of_address]
summary: Plan the move, transfer utilities and update your address everywhere it matters.
reviewed: 2026-11-01
---
# Move house

Generic template. Some countries require registering a new address with the authorities within a
few days of moving, and some documents must show the current address. Always run the `localize`
step first.

## Steps

```lifebox-steps
-60 localize   Check local duties after moving (address registration and documents that show the address)
-45 movers     Get quotes from movers or book a van
-30 addresses  List who needs the new address: bank, employer, tax and social security, health, insurance, vehicle, schools, subscriptions
-14 utilities  Arrange electricity, water, gas and internet at the new address; cancel or transfer the old ones
-7  mail       Set up mail forwarding, if available
0   move       Moving day: meter readings and photos at both homes
+7  register   Register the new address with the authorities, if required
+14 update     Update the address on documents that must show it (ID, driver's licence, vehicle registration)
+30 check      Check that everyone on the list has the new address; file new proofs of address in lifebox
```

## Documents

```lifebox-documents
lease                 depends   New lease or deed
proof_of_address      depends   Proof of the new address
national_id           depends   ID card (if it shows the address)
driver_license        depends   Driver's licence (if it shows the address)
vehicle_registration  depends   Vehicle registration (if it shows the address)
utility_bill          optional  First utility bill at the new address
```

## Localize

Confirm: the country and city you are moving to, and whether it is a move within the country or
abroad. Look up address registration duties and deadlines, and which documents must be updated.

## Tips

- Leaving a lease too? Run the `lease-end` recipe with the lease end date as its anchor.
