Page 0E – Entity Relationship Diagram (Text‑Based Architecture Map)

This page describes the logical data model of RehabConnect using text‑based diagrams. It shows how Patients, Sessions, Scores, IDT meetings, Risk, Audit, Users, and Integrations connect to power the compliance engine and dashboards.

1. High‑Level System View

[User] → performs actions → [RehabConnect App] → writes → [Data Layer]

[Data Layer] feeds:
  - Compliance Engines (Pages 1–4)
  - First-Day Engines (Physician + Therapy)
  - Risk & Dashboard Engine (Page 5)
  - Audit & Governance (Page 6)
  - Integration Layer (Page 7)

2. Patient‑Centric Core (Updated)

                 ┌────────────────────┐
                 │      Patient       │
                 │  patient_id (PK)   │
                 └────────┬──────────┘
                          │ 1
                          │
     ┌────────────────────┼───────────────────────────────┐
     │                    │                               │
     ▼                    ▼                               ▼
┌──────────────┐   ┌────────────────┐            ┌──────────────────────┐
│TherapySession│   │PhysicianEval   │            │     IDTMeeting       │
│patient_id(FK)│   │patient_id(FK)  │            │ patient_id(FK)       │
└──────────────┘   └────────────────┘            └──────────────────────┘
     │                    │                               │
     ▼                    ▼                               ▼
┌──────────────┐   ┌────────────────┐            ┌──────────────────────┐
│FunctionalScore│   │MedicalNecessity│            │      AuditLog        │
│patient_id(FK) │   │patient_id(FK)  │            │ patient_id (opt FK)  │
└──────────────┘   └────────────────┘            └──────────────────────┘
                          │
                          ▼
                 ┌──────────────────────┐
                 │      RiskScore       │
                 │   patient_id(FK)     │
                 └──────────────────────┘

What’s new here

PhysicianEval sits parallel to TherapySession

Both feed into First‑Day Compliance Engines

Both feed into RiskScore

Both are auditable

3. New Entity: PhysicianEvaluation

Purpose

Supports CMS requirement:Physician post‑admission evaluation within 24 hours.

Entity Structure

PhysicianEvaluation
----------------------------
evaluation_id (PK)
patient_id (FK)
evaluation_timestamp
physician_id (FK to User)
notes
source (manual/integration)
created_at
updated_at

Relationships

Patient 1 ──< PhysicianEvaluation (many)
User 1 ──< PhysicianEvaluation (many)
PhysicianEvaluation 1 ──< AuditLog (many)

4. First‑Day Compliance Engines (Updated)

Patient
   │
   ├── PhysicianEvaluation (24h rule)
   │       - evaluation_timestamp
   │
   └── TherapySession (36h rule)
           - first therapy timestamp

Engine Logic

First-Day Engine
-----------------------------------------
Inputs:
  - admission_datetime
  - physician_evaluation_timestamp
  - first_therapy_timestamp

Outputs:
  - Physician 24h compliance
  - Therapy 36h compliance
  - Optional therapy 24h local standard
  - Delay reason codes
  - Risk drivers

5. Updated Compliance Flow

[PhysicianEvaluation] → 24h Engine → RiskScore
[TherapySession]      → 36h Engine → RiskScore

Both feed:

Patient‑level alerts

Unit‑level dashboards

Survey readiness

Administrative denial prevention

6. Updated Integration Layer Diagram

External Systems (EMR, ADT, Physician Notes)
        │
        ▼
[Integration Layer]
   - FHIR: DocumentReference → PhysicianEvaluation
   - HL7 ADT: Admission triggers countdown
   - CSV: Physician eval imports
        │
        ▼
[PhysicianEvaluation] + [TherapySession]
        │
        ▼
[First-Day Compliance Engines]
        │
        ▼
[RiskScore] → [Dashboard]

7. Updated Summary Mental Model

Patient
  ├── PhysicianEvaluation (24h)
  ├── TherapySession (36h)
  ├── FunctionalScore
  ├── IDTMeeting
  ├── MedicalNecessityRecord
  └── AuditLog

All → Compliance Engines → RiskScore → Dashboard → Governance