Page 7 – Integration Layer

1. Purpose

The Integration Layer defines how RehabConnect exchanges data with hospital systems, therapy platforms, and documentation sources. It ensures RehabConnect can operate in:

Phase 1: Manual entry

Phase 2: CSV import

Phase 3: Real‑time integration (FHIR/HL7)

This module is essential for:

reducing manual data entry

improving accuracy

enabling real‑time compliance intelligence

scaling to enterprise IRF environments

2. Integration Philosophy

RehabConnect is built on a progressive enhancement model:

Phase 1 — Manual

Everything works with manual entry.

Phase 2 — Semi‑Automated

CSV uploads reduce manual work.

Phase 3 — Fully Integrated

FHIR/HL7 connections automate data flow.

No feature is blocked by lack of integration.Integration simply enhances speed, accuracy, and automation.

3. Data Sources & Targets

Primary Data Sources

EMR (Epic, Cerner, Meditech)

Therapy systems (WellSky, NetHealth, Raintree)

Scheduling systems

Physician documentation

ADT feeds (admissions/discharges/transfers)

Primary Data Targets

RehabConnect compliance engine

Risk scoring model

Dashboards

Audit trail

Survey readiness reports

4. Data Categories & Required Fields

A. Patient Demographics

Patient ID

Name

DOB

MRN

Admission date/time

Discharge date/time (if applicable)

B. Therapy Minutes

Discipline (PT/OT/SLP)

Scheduled minutes

Delivered minutes

Missed minutes

Reason codes

Timestamp

C. Functional Scores

Score type (mobility, ADL, cognition, swallowing)

Score value

Date/time

Discipline

D. IDT Data

Meeting date/time

Attendance

Discipline notes

Physician sign‑off

E. Physician Documentation

Medical necessity statements

Barriers

Clinical reasoning

F. ADT Events

Admission

Transfer

Discharge

5. Integration Methods

Phase 1 — Manual Entry

Therapists enter minutes, scores, IDT notes

Physicians enter medical necessity

Leadership views dashboards

Phase 2 — CSV Import

RehabConnect supports CSV uploads for:

Therapy minutes

Functional scores

IDT attendance

Patient demographics

Schedules

CSV Import Rules

Must include required fields

Missing fields flagged

Imported data tagged as “integration source: CSV”

All imports logged in audit trail

Phase 3 — FHIR API Integration

RehabConnect supports FHIR resources such as:

Patient

Encounter

Observation (functional scores)

Procedure (therapy sessions)

CarePlan (therapy plan)

DocumentReference (physician notes)

FHIR Integration Benefits

Real‑time therapy minutes

Real‑time functional scores

Real‑time physician documentation

Automated IDT population

HL7 Integration (ADT Feed)

RehabConnect consumes:

A01 (admission)

A02 (transfer)

A03 (discharge)

ADT Benefits

Auto‑start 36‑hour timer

Auto‑populate patient list

Auto‑close patient record on discharge

6. Data Mapping Examples

Therapy Minutes (CSV or FHIR)

patient_id
discipline
delivered_minutes
missed_minutes
reason_code
timestamp

Functional Scores

patient_id
discipline
score_type
score_value
timestamp

IDT Attendance

patient_id
meeting_date
discipline
present (Y/N)
proxy_used (Y/N)

7. Integration Workflow

CSV Workflow

User uploads CSV

System validates fields

Errors flagged for correction

Valid rows imported

Audit log updated

Dashboards recalculate

FHIR/HL7 Workflow

Hospital sends data via API or HL7 feed

RehabConnect receives and validates

Data mapped to internal schema

Compliance engine updates

Risk scores recalculate

Audit log updated

8. Error Handling & Validation

Validation Rules

Required fields must be present

Patient ID must match existing record

Timestamps must be valid

Disciplines must match configured list

Error Types

Missing fields

Invalid values

Duplicate entries

Unmapped disciplines

Error Handling Workflow

Errors flagged in UI

User corrects and re‑uploads

System logs all errors

9. Security & Compliance

Data Security

Encrypted in transit

Encrypted at rest

Role‑based access

Audit Logging

All imports logged

All API calls logged

All HL7 events logged

Compliance Alignment

HIPAA

CMS IRF documentation requirements

Enterprise IT security standards

10. UI Structure (Text‑Based Wireframe)

Integration Dashboard

Integration Status
-----------------------------------------------------
CSV Imports: Last import 03/28 09:14 AM (Success)
FHIR API: Connected
HL7 ADT Feed: Connected
Errors: 0

Recent Imports
-----------------------------------------------------
Therapy Minutes CSV | 03/28 09:14 | 142 rows | Success
Functional Scores CSV | 03/27 16:02 | 88 rows | 2 errors
IDT Attendance CSV | 03/27 10:45 | 22 rows | Success

Error Viewer

CSV Import Errors – Functional Scores
-----------------------------------------------------
Row 14 | Missing score_value
Row 37 | Invalid discipline: "RT"

11. Demo Script (For Hospital Leadership)

“Let me show you how RehabConnect integrates with your existing systems.”

Open Integration Dashboard

Show CSV import history

Show FHIR/HL7 connection status

Show how imported data updates dashboards instantly

Show audit log entries for imports

Close with:“RehabConnect meets you where you are — manual, CSV, or fully integrated — and scales with your hospital’s capabilities.”

12. Dependencies

Page 0 – Architecture & Vision

Page 1 – Therapy Minutes & 3‑Hour Rule

Page 2 – Therapy Start Within 36 Hours

Page 3 – IDT Meeting Compliance

Page 4 – Medical Necessity & Functional Improvement

Page 5 – Administrative Denial Prevention Dashboard

Page 6 – Audit Trail & Governance