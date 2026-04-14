Page 5 – Administrative Denial Prevention Dashboard

1. Purpose

The Administrative Denial Prevention Dashboard is the executive‑level command center for RehabConnect. It aggregates all compliance signals from Pages 1–4 and surfaces real‑time denial risk at the patient and unit level.

This dashboard exists to do one thing:

Prevent IRF administrative denials before they happen.

2. What This Dashboard Solves

Leadership Pain Points

No real‑time visibility into patients at risk

Compliance signals scattered across systems

Documentation gaps discovered only after discharge

Survey readiness is reactive, not continuous

RehabConnect’s Solution

Real‑time risk scoring

Patient‑level risk cards

Unit‑level compliance heat maps

CMS‑aligned documentation completeness

One‑click survey‑ready reporting

3. Inputs From Other Modules

The dashboard pulls structured signals from:

Page 1 – Therapy Minutes & 3‑Hour Rule

Delivered minutes

Remaining minutes

Missed minutes

Reason codes

Rolling intensity

Page 2 – Therapy Start Within 36 Hours

Hours elapsed

Hours remaining

Delay reason codes

Page 3 – IDT Meeting Compliance

Last IDT date

Attendance completeness

Documentation completeness

Physician sign‑off

Page 4 – Medical Necessity & Functional Improvement

Functional improvement

Plateau detection

Medical necessity documentation

Improvement rate

4. Risk Scoring Model

The dashboard uses a weighted composite score (0–100) to quantify denial risk.

Example Weighting (Configurable)

3‑Hour Rule Compliance: 30%

36‑Hour Start Compliance: 20%

IDT Compliance: 20%

Functional Improvement: 20%

Medical Necessity Documentation: 10%

Risk Categories

Green (0–30): Low risk

Yellow (31–60): Moderate risk

Red (61–100): High risk

Documentation Completeness Score

Documentation Completeness = % of required fields completed across all modules

Survey Readiness Score

Survey Readiness = weighted average of all compliance scores across the unit

5. Dashboard UI (Text‑Based Wireframe)

Executive Dashboard

Administrative Denial Prevention Dashboard
-----------------------------------------------------
Unit Summary
Patients: 22
High Risk (Red): 4
Moderate Risk (Yellow): 6
Low Risk (Green): 12
Survey Readiness Score: 87%

High-Risk Patients
-----------------------------------------------------
Patient A | Risk: 92 | Drivers: 3HR, IDT, No Progress
Patient B | Risk: 78 | Drivers: 36HR, Med Necessity
Patient C | Risk: 74 | Drivers: Plateau, Missed Minutes
Patient D | Risk: 69 | Drivers: IDT Missing SLP

Compliance Heat Map
-----------------------------------------------------
3-Hour Rule:        82% (Yellow)
36-Hour Start:      91% (Green)
IDT Compliance:     76% (Yellow)
Functional Progress: 68% (Yellow)
Med Necessity:      88% (Green)

Patient Risk Card

Patient A – Risk Score: 92 (Red)
-----------------------------------------------------
Top Risk Drivers:
- 3-Hour Rule not met (120/180)
- IDT overdue (9 days)
- No functional improvement in 4 days

Documentation Status:
- Medical Necessity: Complete
- IDT Notes: Missing PT
- Functional Scores: Up to date

[View Full Record]   [Export Patient Summary]

6. Alerts

Patient‑Level Alerts

“High risk: 3‑hour rule not met today”

“High risk: IDT overdue”

“High risk: No functional improvement in 4 days”

“High risk: Missing medical necessity documentation”

Unit‑Level Alerts

“5 patients in red status”

“IDT compliance below threshold”

“Therapy intensity trending low this week”

“Survey readiness score below target”

7. Workflow Logic

Therapist Workflow

Enter minutes, functional scores, IDT notes

System updates patient risk score

Therapist sees patient‑level risk indicators

Leadership Workflow

Open dashboard

Review high‑risk patients

Drill into risk drivers

Assign follow‑up actions

Export survey‑ready report

Compliance Workflow

Review documentation completeness

Review overdue items

Prepare for survey using exportable report

Track trends over time

8. Demo Script (For Hospital Leadership)

“Let me show you how RehabConnect prevents denials before they happen.”

Open the dashboard

Show high‑risk patients

Click into a risk card

Show top risk drivers

Export a survey‑ready report

Close with:“This gives your team real‑time visibility into IRF compliance — instead of discovering problems after discharge.”

9. Integration Notes

Phase 1 – Manual

All risk drivers calculated from therapist entries

Phase 2 – CSV Import

Import therapy minutes

Import IDT attendance

Import functional scores

Phase 3 – FHIR/HL7

Real‑time ADT

Real‑time therapy documentation

Physician notes

Automated risk scoring

10. Dependencies

Page 0 – Architecture & Vision

Page 1 – Therapy Minutes & 3‑Hour Rule

Page 2 – Therapy Start Within 36 Hours

Page 3 – IDT Meeting Compliance

Page 4 – Medical Necessity & Functional Improvement

Page 6 – Audit Trail & Governance