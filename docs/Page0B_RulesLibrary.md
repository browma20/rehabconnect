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