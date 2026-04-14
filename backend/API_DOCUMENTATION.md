# RehabConnect API Documentation

## Overview
RehabConnect provides RESTful API endpoints for managing rehabilitation patients, therapy sessions, compliance tracking, and risk assessment.

## Base URL
```
http://localhost:5000/api
```

## Authentication
Currently no authentication implemented - for development/demo purposes only.

## Endpoints

### Patient Management

#### Create Patient
- **POST** `/patients`
- **Body:**
```json
{
  "patient_id": "string",
  "name": "string",
  "admission_datetime": "ISO 8601 datetime string (optional)"
}
```
- **Response:** Patient object with 201 status

#### Get Patient
- **GET** `/patients/{patient_id}`
- **Response:** Patient details

#### Update Patient
- **PUT** `/patients/{patient_id}`
- **Body:** Fields to update
- **Response:** Updated patient

#### Delete Patient
- **DELETE** `/patients/{patient_id}`
- **Response:** Success message

#### List Patients
- **GET** `/patients`
- **Response:** Array of patients

### Therapy Minutes

#### Add Therapy Session
- **POST** `/patients/{patient_id}/therapy-sessions`
- **Body:**
```json
{
  "therapy_type": "PT|OT|ST",
  "minutes": 45,
  "therapist_id": "string",
  "timestamp": "ISO 8601 datetime (optional)"
}
```

#### Get Therapy Sessions
- **GET** `/patients/{patient_id}/therapy-sessions`
- **Response:** Array of therapy sessions

#### Get Daily Compliance
- **GET** `/patients/{patient_id}/compliance/daily?date=YYYY-MM-DD`
- **Response:** Compliance status for the day

#### Get Rolling Compliance
- **GET** `/patients/{patient_id}/compliance/rolling`
- **Response:** Rolling compliance status

### Physician Evaluations

#### Create Evaluation
- **POST** `/patients/{patient_id}/physician-evaluations`
- **Body:**
```json
{
  "physician_id": "string",
  "evaluation_datetime": "ISO 8601 (optional)",
  "notes": "string (optional)"
}
```

#### Get Evaluations
- **GET** `/patients/{patient_id}/physician-evaluations`

#### Get First-Day Compliance
- **GET** `/patients/{patient_id}/compliance/first-day`

### IDT Meetings

#### Create IDT Meeting
- **POST** `/patients/{patient_id}/idt-meetings`
- **Body:**
```json
{
  "meeting_datetime": "ISO 8601",
  "attendees": ["array", "of", "ids"],
  "notes": "string (optional)"
}
```

#### Get IDT Meetings
- **GET** `/patients/{patient_id}/idt-meetings`

#### Update Meeting Notes
- **PUT** `/patients/{patient_id}/idt-meetings/{meeting_id}`
- **Body:** `{"notes": "updated notes"}`

#### Get IDT Compliance
- **GET** `/patients/{patient_id}/compliance/idt`

### Functional Scores

#### Add Functional Score
- **POST** `/patients/{patient_id}/functional-scores`
- **Body:**
```json
{
  "score_type": "string",
  "score_value": 85.5,
  "assessor_id": "string",
  "assessment_date": "ISO 8601 (optional)"
}
```

#### Get Functional Scores
- **GET** `/patients/{patient_id}/functional-scores`

#### Get Functional Summary
- **GET** `/patients/{patient_id}/functional-summary`

#### Get Functional Compliance
- **GET** `/patients/{patient_id}/compliance/functional`

### Medical Necessity

#### Add Medical Necessity Record
- **POST** `/patients/{patient_id}/medical-necessity-records`
- **Body:**
```json
{
  "justification": "string",
  "clinician_id": "string",
  "assessment_date": "ISO 8601 (optional)"
}
```

#### Get Medical Necessity Records
- **GET** `/patients/{patient_id}/medical-necessity-records`

#### Get Medical Necessity Compliance
- **GET** `/patients/{patient_id}/compliance/medical-necessity`

### Risk Assessment

#### Get Patient Risk
- **GET** `/patients/{patient_id}/risk`
- **Response:** Risk score and details

#### Get Unit Risk Summary
- **POST** `/unit/risk-summary`
- **Body:** `{"patient_ids": ["id1", "id2"]}`

#### Get High Risk Patients
- **GET** `/patients/high-risk?threshold=60`

### Data Integration

#### Export Patient CSV
- **GET** `/patients/{patient_id}/export/csv`
- **Response:** CSV file download

#### Export Patient FHIR
- **GET** `/patients/{patient_id}/export/fhir`
- **Response:** FHIR Bundle JSON

#### Export Patient HL7
- **GET** `/patients/{patient_id}/export/hl7`
- **Response:** HL7 message string

#### Import CSV
- **POST** `/import/csv`
- **Body:** Multipart form with CSV file

#### Import FHIR
- **POST** `/import/fhir`
- **Body:** FHIR Bundle JSON

#### Import HL7
- **POST** `/import/hl7`
- **Body:** `{"hl7_message": "HL7 string"}`

## Error Responses
All endpoints return JSON error responses with appropriate HTTP status codes:
```json
{
  "error": "Error description"
}
```

## Data Types
- **patient_id**: String identifier for patients
- **datetime**: ISO 8601 format strings
- **therapy_type**: "PT", "OT", or "ST"
- **compliance_status**: "Green", "Yellow", or "Red"
- **risk_score**: Integer 0-100</content>
<parameter name="filePath">c:\Users\menik\OneDrive\Documents\Github Portfolio\Python Project Folders\rehabconnect\backend\API_DOCUMENTATION.md