# Business rules (as told to us by the clinic)

Last updated by the clinic manager. Some points are still open. Those are marked.

## Hours and slots
- The clinic is in New York. Clinic time is America/New_York (US Eastern: UTC-4 in summer, UTC-5 in winter). All hours below are clinic time.
- Open Monday to Friday, 08:00 to 17:00. Closed on weekends.
- Lunch break 12:00 to 13:00. No appointment may overlap it.
- Appointments start on the half hour and last 30 or 60 minutes.
- Booking must be in the future and no more than 60 days ahead.

## Booking
- A doctor cannot have two appointments that overlap in time.
- A patient cannot have two appointments that overlap in time, even with different doctors.
- Back-to-back appointments are fine (09:00 to 09:30, then 09:30 to 10:00).

## Fees (all amounts in cents, percentages round half up)
- Each doctor has a base fee for 30 minutes. A 60-minute visit costs double.
- Insured patients get 20% off the consultation fee.
- Cancelling 24 hours or more before the start is free.
- Cancelling less than 24 hours before the start costs 50% of the consultation fee.
- A no-show costs 100% of the consultation fee. It can only be marked once the start time has passed.

## Lifecycle
`scheduled -> checked_in -> completed`, or `scheduled -> checked_in -> left_unseen`, or `scheduled -> cancelled`, or `scheduled -> no_show`.

- Only a `scheduled` appointment can be cancelled, and only before its start time. After the start time, mark it `no_show` or check the patient in. (T-005, pending clinic manager confirmation)
- A patient who checks in but leaves before being seen is marked `left_unseen`. No fee. (T-005, pending clinic manager confirmation)
- OPEN QUESTION: can a doctor reschedule an existing appointment, or must it be cancelled and rebooked? Waiting on the clinic manager.

## Admin
- Deleting an appointment is for administrators only and needs the admin token.
