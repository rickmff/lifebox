---
id: lease-end
title: End or renew a lease
anchor: end date of the lease
applies_to: [lease]
summary: Decide early, give notice in the required form and get the deposit back.
reviewed: 2026-11-01
---
# End or renew a lease

Generic template. Notice periods, how notice must be given and deposit rules come from the lease
and local law. Always run the `localize` step first.

## Steps

```lifebox-steps
-120 localize    Read the lease and local rules: notice period, how notice must be sent, deposit deadline
-100 decide      Decide: renew, renegotiate or leave
-90  notice      Send notice in the required form and keep proof (adjust to your notice period)
-60  move-plan   If leaving, plan the move (see the moving-house recipe)
-14  preinspect  Ask for a pre-inspection and fix what you are responsible for
0    handover    Handover: photos, meter readings, keys and a signed check-out report
+30  deposit     Follow up on the deposit return
```

## Documents

```lifebox-documents
lease         required  Current lease
other         depends   Check-in inventory and photos
receipt       depends   Proof of rent payments
utility_bill  depends   Final utility bills
```

## Localize

Confirm: the country and city, and the lease type (fixed term or open-ended). Look up the legal
minimum notice period, accepted ways of giving notice, and the deadline for returning the deposit.

## Tips

- Compare the check-out state with the check-in inventory photos before signing anything.
