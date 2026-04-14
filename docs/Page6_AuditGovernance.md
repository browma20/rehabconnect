Page 6 – Audit Trail & Governance

1. Purpose

This page defines the audit, governance, and security framework for RehabConnect. It ensures that every action taken within the platform is:

Traceable

Timestamped

Attributable

Immutable

CMS‑aligned

This module is essential for:

Survey readiness

Administrative denial appeals

Internal compliance reviews

Legal defensibility

Enterprise adoption

2. What This Module Solves

IRF Leadership Pain Points

“We can’t prove who documented what, or when.”

“Surveyors ask for audit trails we can’t easily produce.”

“We need role‑based access to protect sensitive data.”

“We need a defensible record for appeals.”

RehabConnect’s Solution

Full audit logging

Role‑based permissions

Immutable documentation history

Exportable audit artifacts

CMS‑aligned timestamping

3. Governance Model

RehabConnect uses a role‑based access control (RBAC) model.

Core Roles

Therapist (PT/OT/SLP)

Enter minutes, functional scores, IDT notes

View their own caseload

Cannot modify others’ documentation

Rehab Nurse

Enter nursing notes

View patient summaries

Physician

Enter medical necessity statements

Sign IDT meetings

View all patient data

Compliance Officer

View all audit logs

Export compliance reports

Cannot modify clinical documentation

Rehab Director / Leadership

View dashboards

View risk scores

Assign follow‑up actions

Administrator

Manage users

Configure reason codes, thresholds

Manage integrations

Principles

Least privilege: Users only see what they need.

Segregation of duties: No single user can alter both data and audit logs.

Immutable records: Once saved, documentation cannot be deleted — only amended.

4. Audit Log Schema

Every action in RehabConnect generates an audit entry.

Audit Log Fields

Timestamp

User ID

User role

Patient ID

Action type

Previous value (if applicable)

New value

Source (manual, CSV import, integration)

IP/device metadata (optional for enterprise)

Examples of Logged Actions

Minutes entered or edited

Reason code selected

Functional score updated

IDT attendance recorded

Medical necessity statement added

Physician sign‑off

User role changes

Integration imports

Immutable Record Rule

Audit entries cannot be edited or deleted — only appended.

5. Documentation Versioning

RehabConnect maintains version history for all clinical documentation.

Versioning Rules

Each save creates a new version

Users can view prior versions

Only administrators can restore a previous version

Restores are also logged in the audit trail

Versioned Items

Therapy minutes

Functional scores

IDT notes

Medical necessity statements

Reason codes

6. Compliance & Survey Readiness

Survey‑Ready Audit Exports

RehabConnect can generate:

Patient‑level audit history

Unit‑level compliance summary

Documentation completeness report

Timestamped IDT history

Therapy minutes audit trail

CMS Alignment

Audit logs support:

3‑hour rule validation

36‑hour start validation

IDT timeliness

Functional improvement trends

Medical necessity documentation

Appeal Support

Audit logs provide:

Evidence of timely documentation

Evidence of interdisciplinary coordination

Evidence of medical necessity

Evidence of compliance with CMS rules

7. UI Structure (Text‑Based Wireframe)

Audit Log Viewer

Audit Log – Patient A
-----------------------------------------------------
03/28 09:14 | PT01 | PT | Minutes updated: 45 → 60
03/28 09:16 | PT01 | PT | Reason code added: Medical
03/28 10:02 | MD03 | Physician | Medical necessity statement added
03/28 10:15 | OT07 | OT | Functional score updated: ADL 4 → 5
03/28 10:30 | SYS | Integration | Schedule imported (CSV)

Role Management

User Management
-----------------------------------------------------
User: PT01
Role: Physical Therapist
Permissions: [View Caseload] [Enter Minutes] [Enter Scores]
Status: Active

[Change Role]   [Deactivate User]

Documentation Version History

Medical Necessity Statement – Version History
-----------------------------------------------------
v3 | 03/28 10:02 | MD03 | Updated statement
v2 | 03/27 14:45 | MD03 | Added barriers
v1 | 03/27 09:12 | MD03 | Initial entry

8. Workflow Logic

Therapist Workflow

Enter documentation

System logs action

Version history updated

Compliance Workflow

Review audit logs

Export patient‑level audit trail

Validate documentation completeness

Administrator Workflow

Manage users and roles

Configure thresholds

Review system‑level audit logs

9. Demo Script (For Hospital Leadership)

“Let me show you how RehabConnect creates a defensible, CMS‑aligned audit trail.”

Open a patient’s audit log

Show timestamped entries

Show version history

Show role‑based permissions

Export an audit summary

Close with:“This gives your team a complete, immutable, survey‑ready audit trail — something most IRFs struggle to produce.”

10. Integration Notes

Phase 1 – Manual

All audit entries generated from user actions

Phase 2 – CSV Import

Imported data tagged as “integration source”

Phase 3 – FHIR/HL7

Real‑time documentation imports

Physician notes

ADT events

All integration events are logged with source metadata.

11. Dependencies

Page 0 – Architecture & Vision

Page 1 – Therapy Minutes & 3‑Hour Rule

Page 2 – Therapy Start Within 36 Hours

Page 3 – IDT Meeting Compliance

Page 4 – Medical Necessity & Functional Improvement

Page 5 – Administrative Denial Prevention Dashboard

Page 7 – Integration Layer