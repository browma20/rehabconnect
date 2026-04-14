Page 3 – IDT Meeting Compliance

1. Purpose

This page defines the logic, data model, workflows, UI, and alerting for Interdisciplinary Team (IDT) Meeting Compliance, a core CMS IRF requirement. IDT meetings must be timely, structured, and documented in a way that clearly demonstrates coordinated, interdisciplinary care.

RehabConnect’s goal is to make IDT compliance automatic, structured, and survey‑ready.

2. CMS Requirements (Operationalized)

IDT Meeting Requirements

CMS requires that:

An IDT meeting occurs at least once per week

Required disciplines participate:

Physician

Rehabilitation nurse

PT

OT

SLP (if involved)

Documentation must include:

Patient progress

Barriers

Goal updates

Medical necessity

Interdisciplinary coordination

The meeting must be timely, coordinated, and signed by required participants

Common Denial Triggers

Missing required disciplines

Missing or vague documentation

No evidence of interdisciplinary coordination

Late or inconsistent IDT meetings

Notes that contradict therapy documentation

RehabConnect must surface these issues in real time.

3. Data Model

Entities

Patient

Patient ID

Admission date

Assigned disciplines

Expected length of stay

IDT Meeting

Meeting date/time

Required disciplines

Attendance record

Notes per discipline

Barriers

Goals updated

Medical necessity statement

Physician sign‑off

Attendance Record

Discipline

Present (Y/N)

Proxy allowed (Y/N)

Notes

Documentation Record

Discipline notes

Goal updates

Barriers

Action items

Timestamp

4. Core Calculations

IDT Timeliness

Days Since Last IDT = current date − last IDT meeting date

Compliance Status

Green: IDT completed within last 7 days

Yellow: 7–8 days since last IDT

Red: >8 days since last IDT

Attendance Compliance

Required Disciplines Present = count of required disciplines marked “Present”

Attendance Status:

Green: All required disciplines present

Yellow: One discipline missing (with proxy)

Red: One or more required disciplines missing (no proxy)

Documentation Completeness

Documentation Score = % of required fields completed(Goals, barriers, progress, medical necessity, discipline notes)

5. Workflow Logic

Therapist Workflow

Therapist opens IDT meeting page

Enters discipline‑specific notes

Updates goals and barriers

Confirms attendance

Signs off

Physician Workflow

Reviews interdisciplinary notes

Adds medical necessity statement

Signs off to finalize IDT

Leadership Workflow

Opens IDT dashboard

Sees timeliness status for all patients

Reviews missing disciplines

Reviews incomplete documentation

Exports IDT summary for surveyors

6. Alerts

Patient‑Level Alerts

“IDT meeting due within 24 hours”

“IDT overdue — documentation required”

“Missing required discipline: PT”

“Medical necessity statement missing”

Unit‑Level Alerts

“4 patients overdue for IDT”

“3 IDT meetings missing physician sign‑off”

7. UI Structure (Text‑Based Wireframe)

Therapist View

[Patient Name]
IDT Meeting – 03/28 10:00 AM

Attendance:
PT: Present
OT: Present
SLP: Present
RN: Present
Physician: Pending

Discipline Notes:
PT Notes: [   ]
OT Notes: [   ]
SLP Notes: [   ]

Goals Updated:
[ Mobility goal updated to... ]

Barriers:
[ Pain, cognitive deficits, endurance ]

[Save]

Physician View

IDT Summary – Review & Sign

Interdisciplinary Notes:
- PT: Improved transfers, still needs mod assist
- OT: ADLs improving, endurance limited
- SLP: Mild cognitive deficits persist

Medical Necessity Statement:
[ Patient continues to require IRF-level care due to... ]

[Sign & Finalize]

Leadership Dashboard

IDT Compliance Overview
-----------------------------------------------------
Patient A | Last IDT: 6 days ago | Green | Complete
Patient B | Last IDT: 8 days ago | Yellow | Missing SLP
Patient C | Last IDT: 10 days ago | Red | Overdue

Documentation Summary
-----------------------------------------------------
Complete: 12
Missing Fields: 3
Missing Physician Sign-Off: 2

8. Demo Script (For Hospital Leadership)

“Let me show you how RehabConnect makes IDT meetings compliant, structured, and survey‑ready.”

Open a patient’s IDT meeting

Show attendance tracking

Enter discipline notes

Add goals and barriers

Switch to physician view

Add medical necessity statement

Sign off

Flip to leadership dashboard

Show timeliness and completeness status

Close with:“This gives your team a clean, CMS‑aligned IDT record every week — and eliminates one of the most common denial and survey pain points.”

9. Integration Notes

Phase 1 – Manual

Manual entry of IDT notes

Manual attendance tracking

Phase 2 – CSV Import

Import therapy notes

Import attendance logs

Phase 3 – FHIR/HL7

Pull therapy documentation

Pull physician notes

Auto‑populate attendance from scheduling systems

10. Dependencies

Page 0 – Architecture & Vision

Page 1 – Therapy Minutes & 3‑Hour Rule Engine

Page 4 – Medical Necessity & Functional Improvement

Page 5 – Administrative Denial Prevention Dashboard