import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { patientApi, riskApi } from '../api';

const PatientList = () => {
  const navigate = useNavigate();
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('name');

  useEffect(() => {
    loadPatients();
  }, []);

  const loadPatients = async () => {
    try {
      setLoading(true);
      const patientList = await patientApi.listPatients();

      // Load risk scores for all patients
      const patientsWithRisk = await Promise.all(
        patientList.map(async (patient) => {
          try {
            const risk = await riskApi.getPatientRisk(patient.patient_id);
            return { ...patient, risk };
          } catch (err) {
            console.error(`Failed to get risk for patient ${patient.patient_id}:`, err);
            return { ...patient, risk: { score: 0, status: 'Unknown' } };
          }
        })
      );

      setPatients(patientsWithRisk);
    } catch (err) {
      setError('Failed to load patients');
      console.error('Patient list load error:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredPatients = patients
    .filter(patient =>
      patient.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      patient.patient_id.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'risk':
          return (b.risk?.score || 0) - (a.risk?.score || 0);
        case 'admission':
          return new Date(b.admission_datetime) - new Date(a.admission_datetime);
        default:
          return 0;
      }
    });

  const getRiskColor = (score) => {
    if (score >= 61) return 'text-red-600 bg-red-50';
    if (score >= 31) return 'text-yellow-600 bg-yellow-50';
    return 'text-green-600 bg-green-50';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-lg">Loading patients...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-red-600 text-lg">{error}</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md">
      <div className="p-6 border-b border-gray-200">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Patient List</h2>
          <button
            onClick={() => navigate('/patients/new')}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
          >
            Add New Patient
          </button>
        </div>

        <div className="flex space-x-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search patients..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="name">Sort by Name</option>
              <option value="risk">Sort by Risk Score</option>
              <option value="admission">Sort by Admission Date</option>
            </select>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        {filteredPatients.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            {searchTerm ? 'No patients match your search.' : 'No patients found.'}
          </div>
        ) : (
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Patient
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Admission Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Risk Score
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredPatients.map((patient) => (
                <tr key={patient.patient_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{patient.name}</div>
                      <div className="text-sm text-gray-500">ID: {patient.patient_id}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatDate(patient.admission_datetime)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRiskColor(patient.risk?.score || 0)}`}>
                      {patient.risk?.score || 0}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {patient.discharge_datetime ? 'Discharged' : 'Active'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                    <button
                      onClick={() => navigate(`/patients/${patient.patient_id}`)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      View
                    </button>
                    <button
                      onClick={() => navigate(`/patients/${patient.patient_id}/therapy`)}
                      className="text-green-600 hover:text-green-900"
                    >
                      Therapy
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default PatientList;