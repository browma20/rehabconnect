Page 0 – Architecture & Vision

RehabConnect – Architecture & Vision

1. Vision and North Star

Vision:RehabConnect is a rehab operations and compliance platform that protects IRF revenue, improves documentation quality, and creates real‑time visibility for clinicians, leaders, and families.

Current North Star:Protect IRF revenue by preventing CMS IRF administrative denials through real‑time compliance intelligence.

Primary Outcomes

Revenue protection through reduced administrative denials

Reliable, real‑time CMS compliance

Operational clarity for therapists and leaders

Future lane: transparent family engagement

2. Core Problem Statements

IRF Leadership

Lack of real‑time visibility into patients at risk of denial

Compliance buried in documentation, not surfaced as signals

Survey readiness is reactive, not continuous

Therapists

No live meter for 3‑hour rule or intensity

Missed minutes and reasons scattered across systems

IDT prep and documentation are manual and repetitive

Compliance Teams

Reconstructing a single stay takes hours

Hard to produce clean, structured compliance stories for surveyors

3. Four‑Layer Architecture

Every feature maps to:Use Case → Data → Workflow → Experience

3.1 Use Case Layer (Product Pillars)

Pillar 1 – Therapy Minutes & 3‑Hour Rule

Track daily/rolling minutes

Detect under‑delivery

Capture CMS‑aligned reason codes

Pillar 2 – Therapy Start Within 36 Hours

Track admission → first therapy

Alert before non‑compliance

Document reasons for delay

Pillar 3 – IDT Meeting Compliance

Required disciplines

Structured notes

CMS‑aligned summaries

Pillar 4 – Medical Necessity & Functional Improvement

Functional scoring

Trend detection

Documentation gap alerts

Pillar 5 – Administrative Denial Prevention Dashboard

Aggregate risk signals

Patient‑level risk scoring

Survey‑ready reporting

Pillar 6 – Audit Trail & Governance

Roles and permissions

Audit logs

Exportable artifacts

3.2 Data Layer

Phase 1 – Manual / Lightweight

Therapist‑entered minutes, reasons, functional scores

Manually entered admission/first therapy times

Manually entered IDT notes

Phase 2 – Semi‑Automated

CSV uploads (WellSky, Epic)

Daily schedule imports

Patient demographics/orders via file import

Phase 3 – Integrated

FHIR APIs

HL7 ADT feed

Direct therapy system integration

Design Rule: Every feature must work with Phase 1 data and improve with Phase 2/3 — never blocked by them.

3.3 Workflow Layer (Engines)

Compliance Engine

3‑hour rule calculations

7‑day intensity tracking

36‑hour start timer

IDT compliance checks

Functional improvement trends

Denial risk scoring

Scheduling & Minutes Engine

Patient → discipline → minutes mapping

Scheduled vs. delivered

Gap detection

Alerting Engine

Patient‑level alerts

Unit‑level alerts

Time‑based alerts

Reporting Engine

Daily compliance summary

Survey readiness report

Monthly variance analysis

Exportable PDFs/CSVs

3.4 Experience Layer (Interfaces)

Therapist View

Daily caseload

3‑hour rule meter

Minutes entry + reason codes

Functional score entry

IDT prep

Leadership/Compliance View

Denial risk dashboard

Patients at highest risk

Unit‑level metrics

Survey readiness report

Monthly trends

Admin View

User/role management

Configuration (disciplines, reason codes, thresholds)

Integration settings

Audit log viewer

Family View (Future Lane)

Today’s therapy schedule

Completed vs. missed

High‑level progress

4. Product Pillars and Linked Pages

Page 1 – Therapy Minutes & 3‑Hour Rule Engine

Page 2 – Therapy Start Within 36 Hours

Page 3 – IDT Meeting Compliance

Page 4 – Medical Necessity & Functional Improvement

Page 5 – Administrative Denial Prevention Dashboard

Page 6 – Audit Trail & Governance

Page 7 – Integration Layer

5. CMS IRF Rules Library – Template

For each rule, capture:

Name

Owner (pillar/engine)

Trigger

Inputs

Logic (plain language)

Signals (UI/alerts)

Artifacts (exportable evidence)

6. Roadmap and Sequencing

Phase 1 – Foundational Compliance

Page 1: Therapy minutes & 3‑hour rule

Page 2: Therapy start within 36 hours

Phase 2 – Deepening Compliance

Page 3: IDT meeting compliance

Page 4: Functional improvement tracking

Phase 3 – Executive Value

Page 5: Denial prevention dashboard

Page 6: Audit & governance

Phase 4 – Integration & Family

Page 7: Integration layer

Family portal