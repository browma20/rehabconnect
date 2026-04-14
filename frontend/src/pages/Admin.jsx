import React, { useState, useEffect } from 'react';
import { patientApi, physicianEvaluationApi, integrationApi } from '../api';

const Admin = () => {
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  // Physician evaluation form
  const [physicianForm, setPhysicianForm] = useState({
    patient_id: '',
    physician_id: '',
    evaluation_datetime: '',
    notes: ''
  });

  // Medical necessity form
  const [medicalForm, setMedicalForm] = useState({
    patient_id: '',
    justification: '',
    clinician_id: '',
    assessment_date: ''
  });

  useEffect(() => {
    loadPatients();
  }, []);

  const loadPatients = async () => {
    try {
      const patientList = await patientApi.listPatients();
      setPatients(patientList);
    } catch (err) {
      console.error('Failed to load patients:', err);
    }
  };

  const handlePhysicianSubmit = async (e) => {
    e.preventDefault();
    if (!physicianForm.patient_id || !physicianForm.physician_id) {
      setMessage('Please select a patient and enter physician ID');
      return;
    }

    try {
      setLoading(true);
      await physicianEvaluationApi.createPhysicianEvaluation(physicianForm.patient_id, {
        physician_id: physicianForm.physician_id,
        evaluation_datetime: physicianForm.evaluation_datetime || new Date().toISOString(),
        notes: physicianForm.notes
      });

      setMessage('Physician evaluation created successfully!');
      setPhysicianForm({
        patient_id: '',
        physician_id: '',
        evaluation_datetime: '',
        notes: ''
      });
    } catch (err) {
      setMessage('Failed to create physician evaluation');
      console.error('Physician evaluation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleMedicalSubmit = async (e) => {
    e.preventDefault();
    if (!medicalForm.patient_id || !medicalForm.justification || !medicalForm.clinician_id) {
      setMessage('Please fill in all required fields');
      return;
    }

    try {
      setLoading(true);
      await integrationApi.importHl7(`MSH|^~\\&|Admin|Hospital|RehabConnect|System|${new Date().toISOString()}||ADT^A01|123|P|2.5
PID|1||${medicalForm.patient_id}||Patient Name|||||||
PV1|1|I|${medicalForm.patient_id}||||${medicalForm.assessment_date}||||||${medicalForm.clinician_id}|||||||||||||
OBX|1|TX|MEDICAL_NECESSITY||${medicalForm.justification}||||||F`);

      setMessage('Medical necessity record processed successfully!');
      setMedicalForm({
        patient_id: '',
        justification: '',
        clinician_id: '',
        assessment_date: ''
      });
    } catch (err) {
      setMessage('Failed to process medical necessity record');
      console.error('Medical necessity error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleExportAll = async () => {
    try {
      setLoading(true);
      setMessage('Exporting all patient data...');

      for (const patient of patients) {
        try {
          await integrationApi.exportPatientCsv(patient.patient_id);
          await integrationApi.exportPatientFhir(patient.patient_id);
          await integrationApi.exportPatientHl7(patient.patient_id);
        } catch (err) {
          console.error(`Failed to export patient ${patient.patient_id}:`, err);
        }
      }

      setMessage('Export completed for all patients!');
    } catch (err) {
      setMessage('Export failed');
      console.error('Export error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rc-page">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Administrative Functions</h1>

        {message && (
          <div className={`mb-6 p-4 rounded-md ${message.includes('success') ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
            {message}
          </div>
        )}

        <div className="rc-grid grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Physician Evaluation */}
          <div className="rc-card rc-card-elevated p-6">
            <h2 className="text-xl font-semibold mb-4">Create Physician Evaluation</h2>
            <form onSubmit={handlePhysicianSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Patient *
                </label>
                <select
                  value={physicianForm.patient_id}
                  onChange={(e) => setPhysicianForm(prev => ({ ...prev, patient_id: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">Select Patient</option>
                  {patients.map(patient => (
                    <option key={patient.patient_id} value={patient.patient_id}>
                      {patient.name} ({patient.patient_id})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Physician ID *
                </label>
                <input
                  type="text"
                  value={physicianForm.physician_id}
                  onChange={(e) => setPhysicianForm(prev => ({ ...prev, physician_id: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter physician ID"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Evaluation Date/Time
                </label>
                <input
                  type="datetime-local"
                  value={physicianForm.evaluation_datetime}
                  onChange={(e) => setPhysicianForm(prev => ({ ...prev, evaluation_datetime: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notes
                </label>
                <textarea
                  value={physicianForm.notes}
                  onChange={(e) => setPhysicianForm(prev => ({ ...prev, notes: e.target.value }))}
                  rows={3}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Evaluation notes..."
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create Physician Evaluation'}
              </button>
            </form>
          </div>

          {/* Medical Necessity */}
          <div className="rc-card p-6">
            <h2 className="text-xl font-semibold mb-4">Medical Necessity Documentation</h2>
            <form onSubmit={handleMedicalSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Patient *
                </label>
                <select
                  value={medicalForm.patient_id}
                  onChange={(e) => setMedicalForm(prev => ({ ...prev, patient_id: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">Select Patient</option>
                  {patients.map(patient => (
                    <option key={patient.patient_id} value={patient.patient_id}>
                      {patient.name} ({patient.patient_id})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Clinician ID *
                </label>
                <input
                  type="text"
                  value={medicalForm.clinician_id}
                  onChange={(e) => setMedicalForm(prev => ({ ...prev, clinician_id: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter clinician ID"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Assessment Date
                </label>
                <input
                  type="date"
                  value={medicalForm.assessment_date}
                  onChange={(e) => setMedicalForm(prev => ({ ...prev, assessment_date: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Medical Necessity Justification *
                </label>
                <textarea
                  value={medicalForm.justification}
                  onChange={(e) => setMedicalForm(prev => ({ ...prev, justification: e.target.value }))}
                  rows={4}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Document medical necessity justification..."
                  required
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 disabled:opacity-50"
              >
                {loading ? 'Processing...' : 'Process Medical Necessity'}
              </button>
            </form>
          </div>
        </div>

        {/* Data Export */}
        <div className="bg-white rounded-lg shadow-md p-6 mt-8">
          <h2 className="text-xl font-semibold mb-4">Data Export & Integration</h2>
          <div className="space-y-4">
            <p className="text-gray-600">
              Export all patient data in multiple formats for compliance and integration purposes.
            </p>

            <div className="flex space-x-4">
              <button
                onClick={handleExportAll}
                disabled={loading}
                className="bg-purple-600 text-white py-2 px-6 rounded-md hover:bg-purple-700 disabled:opacity-50"
              >
                {loading ? 'Exporting...' : 'Export All Patient Data'}
              </button>

              <div className="text-sm text-gray-500 py-2">
                Exports CSV, FHIR Bundle, and HL7 messages for all patients
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Admin;