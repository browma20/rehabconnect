import React, { useState, useEffect } from 'react';
import { physicianEvaluationApi, patientApi } from '../api';

const PhysicianEvaluation = () => {
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState('');
  const [evaluations, setEvaluations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  // New evaluation form
  const [formData, setFormData] = useState({
    physician_id: '',
    evaluation_datetime: '',
    notes: '',
    first_day_compliance: false,
    physician_name: ''
  });

  useEffect(() => {
    loadPatients();
  }, []);

  useEffect(() => {
    if (selectedPatient) {
      loadEvaluations(selectedPatient);
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

  const loadEvaluations = async (patientId) => {
    try {
      setLoading(true);
      const evalList = await physicianEvaluationApi.getPhysicianEvaluations(patientId);
      setEvaluations(evalList);
    } catch (err) {
      console.error('Failed to load evaluations:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedPatient || !formData.physician_id || !formData.physician_name) {
      setMessage('Please select a patient and fill in required physician information');
      return;
    }

    try {
      setLoading(true);
      await physicianEvaluationApi.createPhysicianEvaluation(selectedPatient, {
        physician_id: formData.physician_id,
        physician_name: formData.physician_name,
        evaluation_datetime: formData.evaluation_datetime || new Date().toISOString(),
        notes: formData.notes,
        first_day_compliance: formData.first_day_compliance
      });

      setMessage('Physician evaluation created successfully!');
      setFormData({
        physician_id: '',
        evaluation_datetime: '',
        notes: '',
        first_day_compliance: false,
        physician_name: ''
      });
      loadEvaluations(selectedPatient);
    } catch (err) {
      setMessage('Failed to create physician evaluation');
      console.error('Evaluation creation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getComplianceStatus = (evaluation) => {
    if (evaluation.first_day_compliance) {
      return { status: 'Compliant', color: 'text-green-600', bg: 'bg-green-100' };
    }
    return { status: 'Non-Compliant', color: 'text-red-600', bg: 'bg-red-100' };
  };

  return (
    <div className="rc-page">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Physician Evaluations</h1>

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

          {/* New Evaluation Form */}
          <div className="rc-card rc-card-elevated p-6 lg:col-span-2">
            <h2 className="text-xl font-semibold mb-4">Create New Evaluation</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Physician ID *
                  </label>
                  <input
                    type="text"
                    value={formData.physician_id}
                    onChange={(e) => setFormData(prev => ({ ...prev, physician_id: e.target.value }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter physician ID"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Physician Name *
                  </label>
                  <input
                    type="text"
                    value={formData.physician_name}
                    onChange={(e) => setFormData(prev => ({ ...prev, physician_name: e.target.value }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter physician name"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Evaluation Date/Time
                </label>
                <input
                  type="datetime-local"
                  value={formData.evaluation_datetime}
                  onChange={(e) => setFormData(prev => ({ ...prev, evaluation_datetime: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.first_day_compliance}
                    onChange={(e) => setFormData(prev => ({ ...prev, first_day_compliance: e.target.checked }))}
                    className="mr-2"
                  />
                  <span className="text-sm font-medium text-gray-700">First Day Compliance Met</span>
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notes
                </label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                  rows={3}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Evaluation notes and observations..."
                />
              </div>

              <button
                type="submit"
                disabled={loading || !selectedPatient}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create Physician Evaluation'}
              </button>
            </form>
          </div>
        </div>

        {/* Evaluation History */}
        {selectedPatient && (
          <div className="rc-card p-6 mt-8">
            <h2 className="text-xl font-semibold mb-4">Evaluation History</h2>
            {loading ? (
              <div className="text-center py-8">Loading evaluations...</div>
            ) : evaluations.length === 0 ? (
              <div className="text-center py-8 text-gray-500">No evaluations found for this patient</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full table-auto">
                  <thead>
                    <tr className="bg-gray-50">
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Physician</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">First Day Compliance</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Notes</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {evaluations.map((evaluation, index) => {
                      const compliance = getComplianceStatus(evaluation);
                      return (
                        <tr key={index}>
                          <td className="px-4 py-2 text-sm text-gray-900">
                            {new Date(evaluation.evaluation_datetime).toLocaleDateString()}
                          </td>
                          <td className="px-4 py-2 text-sm text-gray-900">
                            {evaluation.physician_name} ({evaluation.physician_id})
                          </td>
                          <td className="px-4 py-2">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${compliance.bg} ${compliance.color}`}>
                              {compliance.status}
                            </span>
                          </td>
                          <td className="px-4 py-2 text-sm text-gray-900 max-w-xs truncate">
                            {evaluation.notes || 'No notes'}
                          </td>
                        </tr>
                      );
                    })}
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

export default PhysicianEvaluation;