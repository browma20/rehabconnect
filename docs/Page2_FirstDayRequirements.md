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

Page 2 – First‑Day Requirements (Physician 24‑Hour Evaluation + Therapy 36‑Hour Start)

1. Purpose

This module tracks and enforces the two Medicare‑defined first‑day IRF requirements:

Physician Post‑Admission Evaluation within 24 hours

First Therapy Treatment within 36 hours

RehabConnect also supports optional hospital‑specific stricter standards, such as requiring therapy within 24 hours.

This page powers:

Compliance alerts

Risk scoring

Survey readiness

Documentation completeness

Leadership dashboards

2. CMS Requirements Overview

A. Physician Post‑Admission Evaluation — 24 Hours (CMS Requirement)

A rehabilitation physician must complete a post‑admission evaluation within 24 hours of IRF admission.

This is a Medicare requirement and is audited during surveys.

B. First Therapy Treatment — 36 Hours (CMS Requirement)

The first therapy session must begin within 36 hours from midnight of the day of admission.

Applies to PT/OT/SLP.

This is the therapy‑specific Medicare requirement.

C. Optional Local Standard — Therapy Within 24 Hours (Hospital Policy)

Many IRFs adopt a stricter internal standard:

Therapy must begin within 24 hours of admission.

This is not a CMS requirement but is common in high‑performing programs.

RehabConnect supports both:

CMS baseline

Hospital‑specific stricter thresholds

3. Inputs

Required Data

Admission timestamp

Physician evaluation timestamp

First therapy session timestamp

Discipline (PT/OT/SLP)

Delay reason codes (if applicable)

Optional Data

Hospital‑defined therapy threshold (e.g., 24 hours)

4. Compliance Logic

Rule 2.1 — Physician Evaluation Within 24 Hours

Trigger: AdmissionLogic:

evaluation_time - admission_time ≤ 24 hoursStatus:

Green: Completed within 24 hours

Red: OverdueDocumentation:

Physician must document evaluation

Rule 2.2 — First Therapy Treatment Within 36 Hours

Trigger: AdmissionLogic:

first_therapy_time - admission_time ≤ 36 hoursStatus:

Green: Completed within 36 hours

Red: OverdueDocumentation:

PT/OT/SLP must document session

Rule 2.3 — Optional Local Standard (Therapy Within 24 Hours)

Trigger: Hospital configurationLogic:

first_therapy_time - admission_time ≤ 24 hoursStatus:

Green: <24 hours

Yellow: 24–36 hours

Red: >36 hoursPurpose:

Supports hospitals with stricter internal expectations

5. Alerts

Physician Evaluation Alerts

“Physician evaluation due within 4 hours”

“Physician evaluation overdue”

“Physician evaluation completed”

Therapy Start Alerts

“Therapy start due within 8 hours”

“Therapy start overdue (CMS 36‑hour rule)”

“Therapy start overdue (local 24‑hour standard)”

“Therapy start completed”

6. Dashboard Signals

Patient‑Level

Patient A
-----------------------------------------
Physician Eval: Completed at 14h (Green)
Therapy Start: Completed at 22h (Green)
Local Standard: Met
CMS Standard: Met

Unit‑Level

First-Day Compliance Summary
-----------------------------------------
Physician 24h Compliance: 95%
Therapy 24h Local Standard: 72%
Therapy 36h CMS Standard: 98%
Patients Overdue: 1

7. Risk Scoring Inputs

High‑Risk Drivers

Physician evaluation >24 hours

First therapy >36 hours

Missing documentation

No reason code for delay

Moderate‑Risk Drivers

Therapy between 24–36 hours (if local standard enabled)

Low‑Risk Drivers

All first‑day requirements met

8. Workflow Logic

Physician Workflow

Complete post‑admission evaluation

Document findings

System logs timestamp

Therapist Workflow

Deliver first therapy session

Document minutes and discipline

System logs timestamp

Leadership Workflow

Monitor first‑day compliance

Review overdue patients

Assign follow‑up actions

9. Integration Notes

Phase 1 — Manual

Physician enters evaluation timestamp

Therapist enters first therapy timestamp

Phase 2 — CSV Import

Import therapy sessions

Import physician evaluations

Phase 3 — FHIR/HL7

Real‑time ADT triggers countdown

Physician notes imported

Therapy sessions imported

10. Dependencies

Page 0B – CMS IRF Rules Library

Page 0D – Data Dictionary

Page 5 – Administrative Denial Prevention Dashboard

Page 6 – Audit Trail & Governance

Page 7 – Integration Layer