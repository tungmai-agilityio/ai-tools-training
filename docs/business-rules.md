# Business rules (as told to us by the clinic)

Last updated by the clinic manager. Some points are still open. Those are marked.

## Hours and slots
- The clinic is in New York. Clinic time is America/New_York (US Eastern: UTC-4 in summer, UTC-5 in winter). All hours below are clinic time.
- Open Monday to Friday, 08:00 to 17:00. Closed on weekends.
- Lunch break 12:00 to 13:00. No appointment may overlap it.
- Appointments start on the half hour and last 30 or 60 minutes.
- Booking must be in the future and no more than 60 days ahead.

## Holidays and time off (T-014, defaults chosen by dev, pending clinic manager confirmation)
- On a clinic holiday the whole clinic is closed: no doctor can be booked that day.
- A doctor's time off blocks whole days (start and end date included) for that doctor only.
- Both are whole clinic-time days. Only an administrator (admin token) can add or remove them.
- A day that still has active appointments (scheduled or checked in) cannot be made a holiday or time off. Reschedule or cancel those appointments first.

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
- A `scheduled` appointment can be rescheduled before its start time. It keeps the same record and doctor, and there is no fee. The new time must pass the same booking checks; changing the length changes the consultation fee. To change doctor, cancel and rebook. (T-009, approved by the clinic manager)

## Authentication (T-019 to T-023, approved by client)
- Only staff and administrators can use the clinic system, including every read; patients have no accounts. Only the health check, the sign-in page and its files, the API docs and login are public. (T-021, approved by client)
- Staff can book, check in, complete, mark left-unseen or no-show, cancel and reschedule. Administrators can do all of that plus holidays, time off, deleting appointments, the revenue report and user management. (T-021, approved by client)
- A login lasts 8 hours and cannot be extended; the user signs in again afterwards. (T-019, approved by client)
- After 5 failed logins in a row a username is locked for 15 minutes, even with the right password; a successful login resets the count. An administrator can unlock it early. (T-019, approved by client)
- A password has at least 12 characters, with no other rules. (T-019, approved by client)
- A signed-in user can change their own password by entering the current one; the new one must differ from it. (T-023, approved by client)
- An administrator can reset a user's password. The user gets a temporary password shown once and must change it at next sign-in before doing anything else. (T-023, approved by client)
- Changing, resetting or disabling a password or account ends that user's other sessions. (T-023, approved by client)
- Administrators create, disable and re-enable accounts. The last active administrator cannot be disabled or demoted. (T-020, approved by client)

## Admin
- Deleting an appointment is for administrators only and needs an administrator login (T-021, approved by client).

## Revenue report (T-015, defaults chosen by dev, pending clinic manager confirmation)
- Only an administrator (admin token) can read the revenue report.
- Consultation revenue is the fee of `completed` visits. Penalty revenue is the fee charged on `no_show` and late-cancelled appointments. They are reported separately.
- Each appointment counts on the clinic-local day of its scheduled start, whatever day it was completed or cancelled.
- Amounts are gross: there are no refunds, and a deleted appointment drops out of the totals.
