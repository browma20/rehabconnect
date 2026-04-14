Page 0D – Data Dictionary (All Entities & Fields)

This Data Dictionary defines every core entity, field, and relationship used across the RehabConnect platform. It ensures consistency across engineering, product, compliance, integrations, and analytics.

Each entity includes:

Field name

Description

Data type

Required/optional

Source (manual, CSV, integration)

This is the backbone of your data model.

1. Patient Entity

Entity: Patient

Field

Description

Type

Required

Source

patient_id

Unique internal patient identifier

string

yes

all

mrn

Medical Record Number

string

yes

integration/CSV

first_name

Patient first name

string

yes

integration

last_name

Patient last name

string

yes

integration

dob

Date of birth

date

yes

integration

admission_datetime

IRF admission timestamp

datetime

yes

integration/CSV/manual

discharge_datetime

IRF discharge timestamp

datetime

no

integration

primary_diagnosis

ICD‑10 code

string

no

integration/manual

comorbidities

List of ICD‑10 codes

array

no

integration/manual

assigned_disciplines

PT/OT/SLP

array

yes

manual/CSV

2. Physician Evaluation Entity

Entity: PhysicianEvaluation

Supports CMS requirement: post‑admission physician evaluation within 24 hours.

Field

Description

Type

Required

Source

evaluation_id

Unique evaluation identifier

string

yes

system

patient_id

Links to Patient

string

yes

all

physician_id

Links to User (physician role)

string

yes

manual/integration

evaluation_timestamp

Timestamp of physician evaluation

datetime

yes

manual/integration

notes

Optional physician notes

string

no

manual

source

manual/CSV/FHIR

string

yes

system

created_at

Record creation timestamp

datetime

yes

system

updated_at

Record update timestamp

datetime

yes

system

3. Therapy Session Entity

Entity: TherapySession

Field

Description

Type

Required

Source

session_id

Unique session identifier

string

yes

system

patient_id

Links to Patient

string

yes

all

discipline

PT/OT/SLP

string

yes

manual/CSV/integration

delivered_minutes

Minutes completed

integer

yes

manual/CSV/integration

scheduled_minutes

Minutes planned

integer

no

manual/CSV

missed_minutes

Minutes not delivered

integer

no

manual/CSV

reason_code

CMS‑aligned reason for missed minutes

string

conditional

manual/CSV

timestamp

Date/time of session

datetime

yes

manual/CSV/integration

source

manual/CSV/FHIR/HL7

string

yes

system

4. Functional Score Entity

Entity: FunctionalScore

Field

Description

Type

Required

Source

score_id

Unique score identifier

string

yes

system

patient_id

Links to Patient

string

yes

all

discipline

PT/OT/SLP

string

yes

manual/CSV/integration

score_type

Mobility, ADL, Cognition, Swallowing

string

yes

manual/CSV/integration

score_value

Numeric score

integer

yes

manual/CSV/integration

timestamp

Date/time score recorded

datetime

yes

manual/CSV/integration

notes

Optional therapist notes

string

no

manual

source

manual/CSV/FHIR

string

yes

system

5. IDT Meeting Entity

Entity: IDTMeeting

Field

Description

Type

Required

Source

idt_id

Unique meeting identifier

string

yes

system

patient_id

Links to Patient

string

yes

all

meeting_datetime

Date/time of IDT

datetime

yes

manual

physician_present

Physician attendance

boolean

yes

manual

rn_present

Rehab nurse attendance

boolean

yes

manual

pt_present

PT attendance

boolean

yes

manual

ot_present

OT attendance

boolean

yes

manual

slp_present

SLP attendance (if assigned)

boolean

conditional

manual

goals_updated

Whether goals were updated

boolean

no

manual

barriers

Documented barriers

string

no

manual

physician_signoff

Physician signature timestamp

datetime

no

manual

6. Medical Necessity Entity

Entity: MedicalNecessityRecord

Field

Description

Type

Required

Source

record_id

Unique identifier

string

yes

system

patient_id

Links to Patient

string

yes

all

statement

Medical necessity justification

string

yes

manual/integration

barriers

Barriers to progress

string

no

manual

clinical_reasoning

Therapist explanation

string

no

manual

timestamp

Date/time entered

datetime

yes

manual/integration

discipline

PT/OT/SLP/Physician

string

yes

manual/integration

7. Risk Score Entity

Entity: RiskScore

Field

Description

Type

Required

Source

risk_id

Unique identifier

string

yes

system

patient_id

Links to Patient

string

yes

system

score

Composite risk score (0–100)

integer

yes

system

risk_category

Green/Yellow/Red

string

yes

system

top_drivers

List of risk drivers

array

yes

system

last_updated

Timestamp of last calculation

datetime

yes

system

8. Audit Log Entity

Entity: AuditLog

Field

Description

Type

Required

Source

audit_id

Unique audit entry

string

yes

system

timestamp

When the action occurred

datetime

yes

system

user_id

Who performed the action

string

yes

system

user_role

Role at time of action

string

yes

system

patient_id

Optional link to patient

string

no

system

action_type

What happened

string

yes

system

previous_value

Before change

string

no

system

new_value

After change

string

no

system

source

manual/CSV/integration/system

string

yes

system

9. User Entity

Entity: User

Field

Description

Type

Required

Source

user_id

Unique user identifier

string

yes

system

first_name

User first name

string

yes

admin

last_name

User last name

string

yes

admin

role

Therapist, RN, Physician, Compliance, Admin

string

yes

admin

status

Active/Inactive

string

yes

admin

created_at

Timestamp created

datetime

yes

system

last_login

Timestamp of last login

datetime

no

system

10. Integration Event Entity

Entity: IntegrationEvent

Field

Description

Type

Required

Source

event_id

Unique identifier

string

yes

system

event_type

CSV import, FHIR update, HL7 ADT

string

yes

system

timestamp

When event occurred

datetime

yes

system

file_name

For CSV imports

string

no

system

row_count

Number of rows processed

integer

no

system

error_count

Number of errors

integer

no

system

source_system

Epic, Cerner, WellSky, etc.

string

no

integration

11. Updated Relationships Overview

Patient → PhysicianEvaluation

1:N (one patient, many evaluations)

Patient → TherapySession

1:N

Patient → FunctionalScore

1:N

Patient → IDTMeeting

1:N

Patient → MedicalNecessityRecord

1:N

Patient → RiskScore

1:1 (latest score)

User → PhysicianEvaluation

1:N (physicians only)

User → AuditLog

1:N

IntegrationEvent → AuditLog

1:N