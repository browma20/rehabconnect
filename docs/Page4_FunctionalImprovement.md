Page 4 – Medical Necessity & Functional Improvement

1. Purpose

This page defines the logic, data model, workflows, UI, and alerting for Medical Necessity and Functional Improvement tracking — two core CMS IRF requirements that directly influence administrative denial risk.

RehabConnect’s goal is to make functional progress visible, measurable, and defensible, while ensuring therapists document medical necessity in a structured, CMS‑aligned way.

2. CMS Requirements (Operationalized)

Medical Necessity

CMS requires that:

The patient needs intensive rehabilitation

The patient is reasonably expected to benefit

The therapy plan is individualized and justified

Documentation supports why IRF level of care is required

Functional Improvement

CMS expects:

Objective, measurable functional gains

Regular updates to functional status

Documentation of barriers, plateaus, and clinical reasoning

Evidence that therapy is effective and necessary

Denial Risk Triggers

No documented functional improvement

Long plateaus without explanation

Vague or generic therapy notes

Missing medical necessity statements

Inconsistent scoring across disciplines

RehabConnect must surface these risks in real time.

3. Data Model

Entities

Patient

Patient ID

Diagnoses

Comorbidities

Therapy orders

Expected length of stay

Functional Score Record

Discipline (PT/OT/SLP)

Date/time

Score type (e.g., mobility, ADLs, cognition, swallowing)

Score value

Notes (optional)

Medical Necessity Record

Daily justification statement

Barriers to progress

Clinical reasoning

Risk factors

Therapist signature

Trend Record

Change in functional score over time

Plateau detection

Improvement rate

4. Core Calculations

Functional Change Over Time

Functional Change = Latest Score − Baseline Score

Rate of Improvement

Improvement Rate = Functional Change ÷ Days Since Admission

Plateau Detection

Plateau = No functional change for ≥ 3 consecutive days(Threshold configurable by admin)

Risk Score Contribution

Each factor contributes to denial risk:

No improvement

Plateau

Missing medical necessity documentation

Contradictory notes

Low improvement rate

RehabConnect aggregates these into the Administrative Denial Risk Score (Page 5).

5. Workflow Logic

Therapist Workflow

Therapist selects patient

Enters functional score(s)

Adds medical necessity justification

System updates trend graphs

Alerts fire if plateau or lack of progress detected

Leadership Workflow

Opens Functional Improvement Dashboard

Reviews patients with low or no improvement

Reviews missing medical necessity documentation

Reviews plateau alerts

Exports functional summary for surveyors

6. Alerts

Patient‑Level Alerts

“No functional improvement in 3 days — review needed”

“Medical necessity documentation missing today”

“Improvement rate below expected threshold”

“Functional scores inconsistent across disciplines”

Unit‑Level Alerts

“4 patients showing plateaus”

“2 patients missing medical necessity documentation”

7. UI Structure (Text‑Based Wireframe)

Therapist View

[Patient Name]
Functional Improvement Tracker

Mobility Score: [ 4 ]  (Previous: 3)
ADL Score: [ 5 ]       (Previous: 5)
Cognition Score: [ 6 ] (Previous: 6)

Medical Necessity Statement:
[ Patient continues to require IRF-level intensity due to... ]

Barriers to Progress:
[ Pain, fatigue, cognitive deficits ]

[Save]

Leadership Dashboard

Functional Improvement Overview
-----------------------------------------------------
Patient A | +2 improvement | On Track (Green)
Patient B | 0 improvement  | Plateau (Yellow)
Patient C | -1 regression  | High Risk (Red)

Medical Necessity Compliance
-----------------------------------------------------
Complete Today: 14
Missing Today: 3
At Risk: 2

Trend Summary
-----------------------------------------------------
Avg Improvement Rate: +0.4/day
Plateaus Detected: 4

8. Demo Script (For Hospital Leadership)

“Let me show you how RehabConnect makes functional improvement and medical necessity visible in real time.”

Select a patient

Enter a new functional score

Watch the trend graph update

Enter a medical necessity justification

Flip to the leadership dashboard

Show plateau detection and missing documentation alerts

Close with:“This is the first time your therapists and leaders can see functional progress and medical necessity in a structured, CMS‑aligned way — and prevent denials before they happen.”

9. Integration Notes

Phase 1 – Manual

Therapist enters functional scores

Therapist enters medical necessity statements

Phase 2 – CSV Import

Import functional scores from EMR

Import therapy notes for analysis

Phase 3 – FHIR/HL7

Pull functional scores from therapy systems

Pull physician documentation signals

Auto‑populate medical necessity prompts

10. Dependencies

Page 0 – Architecture & Vision

Page 1 – Therapy Minutes & 3‑Hour Rule Engine

Page 5 – Administrative Denial Prevention Dashboard

Page 7 – Integration Layer