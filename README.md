# RehabConnect

A comprehensive, CMS-compliant rehabilitation management system built with Flask (backend) and React (frontend). Designed to ensure regulatory compliance while providing real-time monitoring of patient care and risk assessment.

## Overview

RehabConnect addresses the complex requirements of inpatient rehabilitation facilities (IRFs) under CMS regulations. The system provides:

- **Real-time Compliance Monitoring**: Automated tracking of therapy minutes, physician evaluations, and interdisciplinary team meetings
- **Risk Assessment**: Dynamic patient risk scoring with visual dashboards
- **Medical Necessity Documentation**: Comprehensive justification for skilled rehabilitation services
- **Data Integration**: HL7/FHIR support for seamless integration with hospital systems
- **Audit Trails**: Complete documentation for regulatory compliance

## Architecture

### Backend (Flask + SQLAlchemy + PostgreSQL)
- **Models**: Patient, TherapySession, PhysicianEvaluation, IDTMeeting, FunctionalAssessment
- **Engines**: ComplianceEngine, RiskEngine, TherapyMinutesEngine
- **Services**: Business logic layer with validation and processing
- **Routes**: RESTful API endpoints for frontend communication
- **Integration**: HL7/FHIR import/export capabilities

### Frontend (React + Tailwind CSS)
- **Components**: Reusable UI components for patient cards, compliance heatmaps, etc.
- **Pages**: Dashboard, Patient Management, Therapy Tracking, Admin Functions
- **API Clients**: Dedicated modules for backend communication
- **Routing**: React Router for navigation

## Key CMS Compliance Features

### 1. 3-Hour Rule Compliance
- Real-time tracking of therapy minutes per patient per day
- Visual progress meters showing compliance status
- Automated alerts for non-compliance

### 2. Physician Evaluation (First 24 Hours)
- Tracking of physician evaluations within 24 hours of admission
- Compliance status indicators
- Audit trail of evaluation documentation

### 3. Interdisciplinary Team (IDT) Meetings
- Weekly meeting scheduling and documentation
- Patient progress reviews
- Care plan coordination tracking

### 4. Functional Assessments
- FIM (Functional Independence Measure) scoring
- Progress tracking over time
- Standardized assessment documentation

### 5. Medical Necessity
- Comprehensive justification documentation
- Skilled service requirements
- Regulatory compliance reporting

### 6. Risk Assessment
- Dynamic patient risk scoring
- Visual heat maps for unit-wide risk overview
- Risk factor identification and mitigation

## Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- npm or yarn

### Backend Setup

1. **Clone and navigate to backend directory**
   ```bash
   cd rehabconnect/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up database**
   ```bash
   # Update config.py with your PostgreSQL connection details
   flask db upgrade
   ```

5. **Run the backend**
   ```bash
   flask run
   ```
   Backend will be available at `http://localhost:5000`

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd rehabconnect/frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment**
   ```bash
   # Create .env file
   echo "REACT_APP_API_URL=http://localhost:5000/api" > .env
   ```

4. **Start development server**
   ```bash
   npm start
   ```
   Frontend will be available at `http://localhost:3000`

## API Documentation

### Core Endpoints

#### Patients
- `GET /api/patients` - List all patients
- `POST /api/patients` - Create new patient
- `GET /api/patients/{id}` - Get patient details
- `PUT /api/patients/{id}` - Update patient

#### Therapy Minutes
- `POST /api/therapy-minutes` - Record therapy session
- `GET /api/therapy-minutes/patient/{id}` - Get patient therapy history
- `GET /api/therapy-minutes/compliance/{id}` - Check 3-hour rule compliance

#### Risk Assessment
- `GET /api/risk/summary` - Get unit risk summary
- `GET /api/risk/patient/{id}` - Get patient risk assessment
- `POST /api/risk/assess` - Perform risk assessment

#### Physician Evaluations
- `POST /api/physician-evaluations` - Create physician evaluation
- `GET /api/physician-evaluations/patient/{id}` - Get patient evaluations

#### IDT Meetings
- `POST /api/idt-meetings` - Schedule IDT meeting
- `GET /api/idt-meetings` - List upcoming meetings
- `PUT /api/idt-meetings/{id}` - Update meeting

#### Functional Assessments
- `POST /api/functional-assessments` - Record functional assessment
- `GET /api/functional-assessments/patient/{id}` - Get patient assessments

#### Integration
- `POST /api/integration/hl7` - Import HL7 message
- `GET /api/integration/export/csv/{id}` - Export patient data as CSV
- `GET /api/integration/export/fhir/{id}` - Export patient data as FHIR Bundle

## Database Schema

### Core Tables
- **patients**: Patient demographic and admission information
- **therapy_sessions**: Individual therapy session records
- **physician_evaluations**: Physician assessment documentation
- **idt_meetings**: Interdisciplinary team meeting records
- **functional_assessments**: FIM scores and functional status
- **risk_assessments**: Dynamic risk scoring data
- **compliance_logs**: Audit trail of compliance events

## Development

### Running Tests
```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test
```

### Code Quality
- Backend: Follows PEP 8 style guidelines
- Frontend: ESLint configuration for React best practices
- Pre-commit hooks for code quality checks

## Deployment

### Production Backend
```bash
export FLASK_ENV=production
flask run --host=0.0.0.0 --port=8000
```

### Production Frontend
```bash
npm run build
# Serve build/ directory with nginx or similar
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with proper tests
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Regulatory Compliance

This system is designed to assist with CMS compliance but does not guarantee compliance. Users are responsible for ensuring their use of the system meets all applicable regulatory requirements. Always consult with legal and compliance experts for your specific situation.

## Support

For support and questions:
- Create an issue in the GitHub repository
- Review the documentation in the `docs/` directory
- Check the API documentation for integration questions