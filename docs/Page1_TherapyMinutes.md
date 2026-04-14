Page 1 – Therapy Minutes & 3‑Hour Rule Engine

Therapy Minutes & 3‑Hour Rule Engine

1. Purpose

This page defines the logic, data model, workflows, UI, and alerts for the 3‑Hour Rule and therapy minutes tracking — the foundational compliance engine for RehabConnect.

2. CMS Requirements (Operationalized)

3‑Hour Rule (Daily Minimum)

Patients must receive at least 3 hours of therapy per day, 5 days per week, or 15 hours over 7 days.

Intensity Requirement (7‑Day Rolling)

Therapy must be intensive, typically requiring multiple disciplines and consistent delivery.

Missed Minutes

Missed minutes must be documented with CMS‑aligned reason codes.

3. Data Model

Entities

Patient

Patient ID

Admission date/time

Assigned disciplines

Therapy orders

Therapy Session

Discipline (PT/OT/SLP)

Scheduled minutes

Delivered minutes

Missed minutes

Reason code

Timestamp

Daily Summary

Total scheduled minutes

Total delivered minutes

Remaining minutes

Compliance status

Reason Codes

Medical

Patient refusal

Scheduling conflict

Therapist unavailable

Other (with note)

4. Core Calculations

Daily Minutes Calculation

Delivered Minutes = sum of all minutes recorded for each therapy session

Remaining Minutes

Remaining Minutes = 180 − Delivered Minutes

7‑Day Rolling Intensity

Rolling Total = sum of all Delivered Minutes over the past 7 days

Compliance Status

Green: ≥ 180 minutes

Yellow: 120–179 minutes

Red: < 120 minutes or missed minutes without reason

5. Workflow Logic

Therapist Workflow

Therapist selects patient

Enters delivered minutes

If minutes < scheduled → selects reason code

System recalculates daily/rolling totals

Alerts fire if thresholds crossed

Leadership Workflow

Opens dashboard

Sees patient‑level compliance status

Reviews patients at risk

Exports daily summary if needed

6. Alerts

Patient‑Level Alerts

“At risk today: <60 minutes delivered by noon”

“Missed minutes require reason code”

“Rolling intensity trending low”

Unit‑Level Alerts

“3 patients below target today”

“Discipline variance detected (PT low)”

7. UI Structure (Text‑Based Wireframe)

Therapist View

[Patient Name]
[3‑Hour Rule Meter: 120/180 minutes]

Delivered Minutes: [   ]
Reason Code (if needed): [dropdown]

[Save]   [Add Another Session]

Rolling 7‑Day Total: 840 minutes
Status: On Track (Green)

Leadership Dashboard

Patients at Risk Today (3)
-------------------------------------
Patient A   | 90/180 | Red
Patient B   | 130/180 | Yellow
Patient C   | 160/180 | Yellow

Unit Summary
-------------------------------------
Avg Delivered: 142 minutes
Missed Minutes: 45
Top Reason: Medical

8. Demo Script (For Hospital Leadership)

“Let me show you how RehabConnect prevents denials before they happen.”

Select a patient

Enter delivered minutes

Show the 3‑hour rule meter updating in real time

Enter a missed minute reason code

Flip to the leadership dashboard

Show the patient moving from red → yellow → green

End with:“This is the first time your therapists and leaders can see compliance in real time instead of discovering problems after discharge.