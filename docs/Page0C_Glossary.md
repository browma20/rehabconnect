Page 0B – CMS IRF Rules Library (Master Operational Rules)

This Rules Library defines the operational interpretation of CMS IRF requirements and translates them into structured, system‑ready logic. Every compliance engine in RehabConnect references these rules.

1. Purpose of the Rules Library

The CMS IRF Rules Library exists to:

Convert CMS regulations into clear, operational logic

Provide consistent definitions across all modules

Power real‑time compliance calculations

Drive alerts, dashboards, and risk scoring

Support survey readiness and denial appeals

Allow hospitals to configure stricter internal standards

Every rule includes:

Trigger

Inputs

Operational logic

Compliance thresholds

Signals

Artifacts

2. Rule Categories

Physician & Therapy First‑Day Requirements

Therapy Minutes & 3‑Hour Rule

IDT Meeting Compliance

Medical Necessity & Functional Improvement

Administrative Denial Prevention Signals

3. Rules Library (Master List)

Category 1 — First‑Day Requirements (Updated)

Rule 1.1 — Physician Post‑Admission Evaluation (24 Hours)

Trigger: AdmissionInputs: Physician evaluation timestampLogic:

evaluation_time - admission_time ≤ 24 hoursCompliance Threshold: ≤24 hoursSignals:

Green: Completed

Red: OverdueArtifacts: Physician evaluation record

Rule 1.2 — First Therapy Treatment (36 Hours)

Trigger: AdmissionInputs: First therapy timestampLogic:

first_therapy_time - admission_time ≤ 36 hoursCompliance Threshold: ≤36 hoursSignals:

Green: Completed

Red: OverdueArtifacts: First therapy session record

Rule 1.3 — Optional Local Standard (Therapy Within 24 Hours)

Trigger: Hospital configurationInputs: First therapy timestampLogic:

first_therapy_time - admission_time ≤ 24 hoursCompliance Threshold: ≤24 hoursSignals:

Green: <24 hours

Yellow: 24–36 hours

Red: >36 hoursArtifacts: Local standard compliance summary

Category 2 — Therapy Minutes & 3‑Hour Rule (Page 1)

Rule 2.1 — Daily 3‑Hour Rule

Trigger: Daily therapy sessionsInputs: Delivered minutesLogic: ≥180 minutes/dayThreshold: 180 minutesSignals: Green/Yellow/Red

Rule 2.2 — 7‑Day Rolling Intensity

Trigger: Any therapy sessionInputs: 7‑day delivered minutesLogic: ≥900 minutesThreshold: 900 minutesSignals: Rolling intensity trend

Rule 2.3 — Missed Minutes Documentation

Trigger: Delivered < scheduledInputs: Reason codeLogic: 100% reason code coverageThreshold: 100%Signals: Missing documentation alerts

Category 3 — IDT Meeting Compliance (Page 3)

Rule 3.1 — Weekly IDT Meeting

Logic: ≤7 days between meetingsThreshold: 7 days

Rule 3.2 — Required Disciplines Present

Logic: Physician, RN, PT, OT; SLP if involvedThreshold: 100%

Rule 3.3 — Documentation Completeness

Logic: All required fields completedThreshold: 100%

Category 4 — Medical Necessity & Functional Improvement (Page 4)

Rule 4.1 — Functional Improvement Tracking

Logic: Improvement OR documented barrier

Rule 4.2 — Plateau Detection

Logic: No improvement ≥3 days

Rule 4.3 — Medical Necessity Documentation

Logic: Daily justification required

Category 5 — Administrative Denial Prevention Signals (Page 5)

Rule 5.1 — Composite Risk Score

Logic: Weighted combination of all rule outputs

Rule 5.2 — High‑Risk Patient Identification

Logic: Risk score >60

Rule 5.3 — Survey Readiness Score

Logic: Weighted average of compliance metrics

4. Rule Change Management

Each rule versioned

Changes logged in audit trail

Historical versions preserved

Risk scoring recalculates automatically

5. How This Library Is Used

Page 2 uses Rules 1.1–1.3

Page 1 uses Rules 2.1–2.3

Page 3 uses Rules 3.1–3.3

Page 4 uses Rules 4.1–4.3

Page 5 uses Rules 5.1–5.3

This ensures consistency, accuracy, and CMS alignment across the platform.

6. Future Expansion

Pre‑admission screening rules

Therapy intensity exceptions

Medical complexity scoring

Documentation quality scoring

Payer‑specific overlays

Page 0C – Glossary of Terms (CMS + RehabConnect)

This glossary defines all key terms used across RehabConnect and CMS IRF regulations. It serves as the shared vocabulary for product design, compliance logic, documentation, and communication with hospital partners.

1. CMS IRF Regulatory Terms

3‑Hour Rule

CMS requirement that IRF patients receive at least 3 hours of therapy per day, 5 days per week, or 15 hours over 7 days.

7‑Day Rolling Intensity

A CMS‑aligned measure of therapy intensity calculated over the previous 7 days.

36‑Hour Rule (Therapy Start Requirement)

First therapy session must begin within 36 hours of IRF admission.

IDT (Interdisciplinary Team)

A required weekly meeting including:

Physician

Rehabilitation nurse

PT

OT

SLP (if involved)

Medical Necessity

Documentation demonstrating that the patient requires IRF‑level care and is reasonably expected to benefit from intensive therapy.

Functional Improvement

Objective, measurable progress in mobility, ADLs, cognition, or swallowing.

Plateau

A period of no functional improvement for ≥3 days, requiring documented clinical reasoning.

Administrative Denial

A CMS denial based on documentation or compliance failures (not medical judgment).

Survey Readiness

The state of being fully compliant with CMS IRF requirements at any time, not just during audits.

Reason Codes (CMS‑Aligned)

Structured explanations for missed minutes or therapy delays (e.g., medical instability, refusal).

ADT Feed (Admission/Discharge/Transfer)

HL7 messages that communicate patient movement through the hospital.

2. RehabConnect Platform Terms

Compliance Engine

The logic layer that evaluates CMS rules in real time (minutes, IDT, 36‑hour rule, etc.).

Risk Score

A composite score (0–100) representing a patient’s administrative denial risk.

Risk Drivers

Specific compliance failures contributing to a patient’s risk score (e.g., missed minutes, overdue IDT).

Patient Risk Card

A structured summary showing a patient’s risk score, risk drivers, and documentation status.

Compliance Heat Map

A unit‑level visualization showing compliance status across all CMS rule categories.

Survey Readiness Score

A weighted score representing overall compliance strength across the unit.

Documentation Completeness Score

Percentage of required documentation fields completed for a patient.

Audit Log

An immutable record of all user actions, imports, and system events.

Version History

A chronological record of all changes to clinical documentation.

Role‑Based Access Control (RBAC)

Permissions system defining what each user role can view or modify.

Integration Layer

The system that handles manual entry, CSV imports, and FHIR/HL7 integrations.

3. Therapy & Clinical Terms

Delivered Minutes

Actual therapy minutes completed during a session.

Scheduled Minutes

Minutes planned for a therapy session.

Missed Minutes

Scheduled minutes not delivered, requiring a reason code.

Functional Score

A numeric measure of patient ability (mobility, ADLs, cognition, swallowing).

Barriers to Progress

Clinical or functional factors limiting improvement (pain, fatigue, cognition).

Clinical Reasoning

Therapist explanation of why progress is limited or plateaued.

Goal Update

Changes to patient goals documented during IDT or therapy sessions.

4. Integration & Data Terms

CSV Import

Batch upload of therapy minutes, scores, or attendance.

FHIR Resource

Standardized API object used for healthcare data exchange (e.g., Patient, Encounter, Observation).

HL7 Message

Legacy hospital messaging format used for ADT events.

Data Mapping

The process of aligning external data fields to RehabConnect’s internal schema.

Source Tagging

Labeling data as manual, CSV, or integration‑derived for audit purposes.

5. Governance & Security Terms

Immutable Record

A record that cannot be deleted or altered — only appended.

User Role

A defined set of permissions (Therapist, RN, Physician, Compliance Officer, Admin).

Access Control

Rules determining what data each user can view or modify.

Audit Artifact

Exportable evidence used for surveys or appeals (minutes log, IDT summary, risk card).

6. Dashboard & Reporting Terms

High‑Risk Patient

A patient with a risk score >60.

Moderate‑Risk Patient

Risk score between 31–60.

Low‑Risk Patient

Risk score between 0–30.

Unit Summary

Aggregate compliance metrics for the entire IRF unit.

Exportable Report

A structured summary used for surveys, appeals, or leadership review.

7. Product & Architecture Terms

Use Case Layer

Defines the functional purpose of each module.

Data Layer

Defines the data structures powering each module.

Workflow Layer

Defines the logic and sequences of actions.

Experience Layer

Defines the UI and user interactions.

Progressive Enhancement Model

RehabConnect’s approach to supporting manual → CSV → integrated workflows.