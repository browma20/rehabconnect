# RehabConnect Frontend API Clients

This directory contains API client classes for communicating with the RehabConnect backend.

## API Clients Overview

### Base Client (`apiClient.js`)
- **Purpose**: Base HTTP client with common functionality
- **Features**:
  - Automatic JSON parsing
  - Error handling
  - File upload support
  - Configurable base URL via `REACT_APP_API_URL` environment variable

### Domain-Specific Clients

#### `patientApi.js` - Patient Management
- Create, read, update, delete patients
- List all patients

#### `therapyMinutesApi.js` - Therapy Sessions
- Add therapy sessions
- Get therapy sessions for a patient
- Get daily/rolling compliance
- Get therapy summaries

#### `physicianEvaluationApi.js` - Physician Evaluations
- Create physician evaluations
- Get evaluations for a patient
- Check first-day compliance

#### `idtApi.js` - IDT Meetings
- Create IDT meetings
- Get meetings for a patient
- Update meeting notes
- Check IDT compliance

#### `functionalApi.js` - Functional Assessments
- Add functional scores
- Get scores for a patient
- Get functional summaries
- Check functional improvement compliance

#### `medicalNecessityApi.js` - Medical Necessity
- Add medical necessity records
- Get records for a patient
- Check medical necessity compliance

#### `riskApi.js` - Risk Assessment
- Get patient risk scores
- Get unit-level risk summaries
- Identify high-risk patients

#### `integrationApi.js` - Data Integration
- Export patient data (CSV, FHIR, HL7)
- Import data from various formats

## Usage Examples

```javascript
import { patientApi, therapyMinutesApi } from './api';

// Create a patient
const patient = await patientApi.createPatient({
  patient_id: 'P001',
  name: 'John Doe',
  admission_datetime: '2024-01-15T10:00:00Z'
});

// Add a therapy session
const session = await therapyMinutesApi.addTherapySession('P001', {
  therapy_type: 'PT',
  minutes: 45,
  therapist_id: 'T001'
});

// Get patient risk
const risk = await riskApi.getPatientRisk('P001');
```

## Error Handling

All API methods throw errors for HTTP errors. Use try/catch blocks:

```javascript
try {
  const patient = await patientApi.getPatient('P001');
  console.log(patient);
} catch (error) {
  console.error('Failed to get patient:', error.message);
}
```

## Environment Configuration

Set the backend API URL in your environment:

```bash
# .env file
REACT_APP_API_URL=http://localhost:5000/api
```

## File Structure

```
api/
├── index.js              # Exports all API clients
├── apiClient.js          # Base HTTP client
├── patientApi.js         # Patient operations
├── therapyMinutesApi.js  # Therapy operations
├── physicianEvaluationApi.js  # Physician operations
├── idtApi.js             # IDT operations
├── functionalApi.js      # Functional assessment operations
├── medicalNecessityApi.js # Medical necessity operations
├── riskApi.js            # Risk assessment operations
└── integrationApi.js     # Data integration operations
```