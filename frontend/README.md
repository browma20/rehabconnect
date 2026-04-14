# RehabConnect Frontend

A React-based frontend for the RehabConnect CMS-compliant rehabilitation management system.

## Features

- **Dashboard**: Risk assessment overview with compliance heat maps
- **Patient Management**: Searchable patient lists and detailed patient views
- **Therapy Minutes Tracking**: Real-time 3-hour rule compliance monitoring
- **IDT Meetings**: Interdisciplinary team meeting scheduling and documentation
- **Functional Assessments**: FIM scoring and progress tracking
- **Physician Evaluations**: First-day compliance tracking
- **Medical Necessity**: Documentation for skilled service requirements
- **Admin Functions**: System administration and data export

## Technology Stack

- **React 18**: Modern React with hooks and functional components
- **React Router**: Client-side routing for navigation
- **Tailwind CSS**: Utility-first CSS framework for styling
- **Fetch API**: HTTP client for backend communication

## Project Structure

```
src/
├── api/                 # API client modules
│   ├── apiClient.js     # Base API client with error handling
│   ├── patientApi.js    # Patient-related API calls
│   ├── therapyMinutesApi.js
│   ├── physicianEvaluationApi.js
│   ├── idtApi.js
│   ├── functionalApi.js
│   ├── medicalNecessityApi.js
│   ├── riskApi.js
│   ├── integrationApi.js
│   └── index.js         # API exports
├── components/          # Reusable React components
│   ├── PatientRiskCard.jsx
│   ├── ComplianceHeatMap.jsx
│   ├── TherapyMinutesPanel.jsx
│   └── FunctionalImprovementPanel.jsx
├── pages/               # Main page components
│   ├── Dashboard.jsx
│   ├── PatientList.jsx
│   ├── PatientDetail.jsx
│   ├── TherapyMinutes.jsx
│   ├── IDT.jsx
│   ├── Functional.jsx
│   ├── PhysicianEvaluation.jsx
│   ├── MedicalNecessity.jsx
│   └── Admin.jsx
├── styles/
│   └── index.css        # Tailwind CSS imports
├── App.js               # Main app component with routing
└── index.js             # React app entry point
```

## Setup Instructions

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Environment Configuration**
   Create a `.env` file in the root directory:
   ```
   REACT_APP_API_URL=http://localhost:5000/api
   ```

3. **Start Development Server**
   ```bash
   npm start
   ```
   The app will run on `http://localhost:3000`

4. **Build for Production**
   ```bash
   npm run build
   ```

## API Integration

The frontend communicates with the Flask backend through RESTful APIs. All API calls are handled through dedicated client modules in the `api/` directory.

### Key API Endpoints

- `GET /api/patients` - List all patients
- `POST /api/patients` - Create new patient
- `GET /api/patients/{id}` - Get patient details
- `POST /api/therapy-minutes` - Record therapy minutes
- `GET /api/risk/summary` - Get unit risk summary
- `POST /api/physician-evaluations` - Create physician evaluation
- `POST /api/integration/hl7` - Import HL7 messages

## CMS Compliance Features

- **3-Hour Rule Monitoring**: Real-time tracking of therapy minutes per patient per day
- **Risk Assessment**: Automated risk scoring with visual heat maps
- **First-Day Compliance**: Physician evaluation tracking within 24 hours
- **Medical Necessity**: Comprehensive documentation for skilled services
- **IDT Meetings**: Weekly interdisciplinary team coordination
- **Functional Assessments**: Standardized FIM scoring and progress tracking

## Navigation

The app uses React Router for client-side navigation with the following routes:

- `/` - Dashboard
- `/patients` - Patient list
- `/patients/:id` - Patient detail view
- `/therapy` - Therapy minutes tracking
- `/idt` - IDT meeting management
- `/functional` - Functional assessments
- `/physician` - Physician evaluations
- `/medical-necessity` - Medical necessity documentation
- `/admin` - Administrative functions

## Styling

The application uses Tailwind CSS for consistent, responsive styling. Key design principles:

- Clean, professional healthcare interface
- Responsive design for desktop and tablet use
- Color-coded risk indicators (green/yellow/red)
- Progress bars for compliance metrics
- Accessible form controls and navigation

## Development Notes

- All components follow React best practices with hooks
- API calls include proper error handling
- State management is component-level (no external state libraries)
- Components are designed to be reusable and maintainable
- Follows the existing backend API contracts exactly