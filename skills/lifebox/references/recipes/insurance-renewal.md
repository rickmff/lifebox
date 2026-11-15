---
id: insurance-renewal
title: Renew or switch an insurance policy
anchor: renewal or end date of the policy
applies_to: [vehicle_insurance, insurance_policy, health_insurance]
summary: Review the policy, compare quotes and act before the cancellation notice deadline.
reviewed: 2026-11-01
---
# Renew or switch an insurance policy

Generic template for car, home, health, travel and other policies. Automatic renewal and notice
periods are set by the policy and by local law. Always run the `localize` step first.

## Steps

```lifebox-steps
-60 localize   Read the policy: automatic renewal or not, the cancellation notice period and how to cancel
-45 review     Review the coverage, past claims and changes in your situation (new car, home, family)
-40 quotes     Get two or three comparable quotes
-30 notice     Last day to send a cancellation notice if switching (adjust to the policy's notice period)
-14 confirm    Confirm the renewal or the new policy's start date, with no gap in coverage
0   renewal    Renewal date: file the new policy and certificate in lifebox
```

## Documents

```lifebox-documents
insurance_policy      required  Current policy and its conditions
vehicle_insurance     depends   Current car insurance certificate (car policies)
vehicle_registration  depends   Vehicle registration (car policies)
driver_license        depends   Driver's licences of the named drivers (car policies)
national_id           depends   ID of the policyholder
proof_of_address      depends   Proof of address (home policies)
```

## Localize

Confirm: the type of policy and the country. Then check the policy conditions for the notice period
and the accepted ways to cancel (letter, email, online form), and whether local law caps notice
periods or allows cancelling at any time after the first year.

## Tips

- Send cancellations in a way that leaves proof (registered letter, email with receipt) and file
  the proof in lifebox.
- Make the new policy start the day the old one ends.
