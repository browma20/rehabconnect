import React, { useState, useEffect } from 'react';
import { integrationApi, patientApi } from '../api';

const MedicalNecessity = () => {
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState('');
  const [necessityRecords, setNecessityRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  // New medical necessity form
  const [formData, setFormData] = useState({
    justification: '',
    clinician_id: '',
    clinician_name: '',
    assessment_date: '',
    medical_conditions: '',
    functional_deficits: '',
    treatment_goals: '',
    expected_outcomes: '',
    frequency_duration: '',
    skilled_services: ''
  });

  useEffect(() => {
    loadPatients();
  }, []);

  useEffect(() => {
    if (selectedPatient) {
      loadNecessityRecords(selectedPatient);
    }
  }, [selectedPatient]);

  const loadPatients = async () => {
    try {
      const patientList = await patientApi.listPatients();
      setPatients(patientList);
    } catch (err) {
      console.error('Failed to load patients:', err);
    }
  };

  const loadNecessityRecords = async (patientId) => {
    try {
      setLoading(true);
      // For now, we'll use a placeholder since the API might not have this endpoint yet
      // In a real implementation, this would call an API to get medical necessity records
      setNecessityRecords([]);
    } catch (err) {
      console.error('Failed to load necessity records:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedPatient || !formData.justification || !formData.clinician_id || !formData.clinician_name) {
      setMessage('Please select a patient and fill in all required fields');
      return;
    }

    try {
      setLoading(true);

      // Create HL7 message for medical necessity documentation
      const hl7Message = `MSH|^~\\&|RehabConnect|Hospital|System|Receiver|${new Date().toISOString()}||ADT^A01|${Date.now()}|P|2.5
PID|1||${selectedPatient}||Patient Name|||||||
PV1|1|I|${selectedPatient}||||${formData.assessment_date}||||||${formData.clinician_id}|||||||||||||
OBX|1|TX|MEDICAL_NECESSITY||${formData.justification}||||||F
OBX|2|TX|MEDICAL_CONDITIONS||${formData.medical_conditions}||||||F
OBX|3|TX|FUNCTIONAL_DEFICITS||${formData.functional_deficits}||||||F
OBX|4|TX|TREATMENT_GOALS||${formData.treatment_goals}||||||F
OBX|5|TX|EXPECTED_OUTCOMES||${formData.expected_outcomes}||||||F
OBX|6|TX|FREQUENCY_DURATION||${formData.frequency_duration}||||||F
OBX|7|TX|SKILLED_SERVICES||${formData.skilled_services}||||||F
OBX|8|TX|CLINICIAN_NAME||${formData.clinician_name}||||||F`;

      await integrationApi.importHl7(hl7Message);

      setMessage('Medical necessity documentation created successfully!');
      setFormData({
        justification: '',
        clinician_id: '',
        clinician_name: '',
        assessment_date: '',
        medical_conditions: '',
        functional_deficits: '',
        treatment_goals: '',
        expected_outcomes: '',
        frequency_duration: '',
        skilled_services: ''
      });
      loadNecessityRecords(selectedPatient);
    } catch (err) {
      setMessage('Failed to create medical necessity documentation');
      console.error('Medical necessity creation error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rc-page">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Medical Necessity Documentation</h1>

        {message && (
          <div className={`mb-6 p-4 rounded-md ${message.includes('success') ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
            {message}
          </div>
        )}

        <div className="rc-grid grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Patient Selection */}
          <div className="rc-card p-6">
            <h2 className="text-xl font-semibold mb-4">Select Patient</h2>
            <select
              value={selectedPatient}
              onChange={(e) => setSelectedPatient(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select Patient</option>
              {patients.map(patient => (
                <option key={patient.patient_id} value={patient.patient_id}>
                  {patient.name} ({patient.patient_id})
                </option>
              ))}
            </select>
          </div>

          {/* Medical Necessity Form */}
          <div className="rc-card rc-card-elevated p-6 lg:col-span-2">
            <h2 className="text-xl font-semibold mb-4">Document Medical Necessity</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Clinician ID *
                  </label>
                  <input
                    type="text"
                    value={formData.clinician_id}
                    onChange={(e) => setFormData(prev => ({ ...prev, clinician_id: e.target.value }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter clinician ID"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Clinician Name *
                  </label>
                  <input
                    type="text"
                    value={formData.clinician_name}
                    onChange={(e) => setFormData(prev => ({ ...prev, clinician_name: e.target.value }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter clinician name"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Assessment Date
                </label>
                <input
                  type="date"
                  value={formData.assessment_date}
                  onChange={(e) => setFormData(prev => ({ ...prev, assessment_date: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Medical Necessity Justification *
                </label>
                <textarea
                  value={formData.justification}
                  onChange={(e) => setFormData(prev => ({ ...prev, justification: e.target.value }))}
                  rows={3}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Describe why skilled rehabilitation services are medically necessary..."
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Medical Conditions
                </label>
                <textarea
                  value={formData.medical_conditions}
                  onChange={(e) => setFormData(prev => ({ ...prev, medical_conditions: e.target.value }))}
                  rows={2}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="List relevant medical conditions..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Functional Deficits
                </label>
                <textarea
                  value={formData.functional_deficits}
                  onChange={(e) => setFormData(prev => ({ ...prev, functional_deficits: e.target.value }))}
                  rows={2}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Describe functional impairments..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Treatment Goals
                </label>
                <textarea
                  value={formData.treatment_goals}
                  onChange={(e) => setFormData(prev => ({ ...prev, treatment_goals: e.target.value }))}
                  rows={2}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Specify measurable treatment goals..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Expected Outcomes
                </label>
                <textarea
                  value={formData.expected_outcomes}
                  onChange={(e) => setFormData(prev => ({ ...prev, expected_outcomes: e.target.value }))}
                  rows={2}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Describe expected functional improvements..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Frequency & Duration
                </label>
                <textarea
                  value={formData.frequency_duration}
                  onChange={(e) => setFormData(prev => ({ ...prev, frequency_duration: e.target.value }))}
                  rows={2}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Specify frequency and duration of services..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Skilled Services Required
                </label>
                <textarea
                  value={formData.skilled_services}
                  onChange={(e) => setFormData(prev => ({ ...prev, skilled_services: e.target.value }))}
                  rows={2}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Describe skilled services that can only be provided by qualified professionals..."
                />
              </div>

              <button
                type="submit"
                disabled={loading || !selectedPatient}
                className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create Medical Necessity Documentation'}
              </button>
            </form>
          </div>
        </div>

        {/* Documentation History */}
        {selectedPatient && (
          <div className="bg-white rounded-lg shadow-md p-6 mt-8">
            <h2 className="text-xl font-semibold mb-4">Documentation History</h2>
            {loading ? (
              <div className="text-center py-8">Loading documentation...</div>
            ) : necessityRecords.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No medical necessity documentation found for this patient
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full table-auto">
                  <thead>
                    <tr className="bg-gray-50">
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Clinician</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Justification</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {necessityRecords.map((record, index) => (
                      <tr key={index}>
                        <td className="px-4 py-2 text-sm text-gray-900">
                          {new Date(record.assessment_date).toLocaleDateString()}
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-900">
                          {record.clinician_name}
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-900 max-w-xs truncate">
                          {record.justification}
                        </td>
                        <td className="px-4 py-2">
                          <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                            Active
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default MedicalNecessity;