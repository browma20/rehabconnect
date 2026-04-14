import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  patientApi,
  therapyMinutesApi,
  physicianEvaluationApi,
  idtApi,
  functionalApi,
  medicalNecessityApi,
  riskApi
} from '../api';

const PatientDetail = () => {
  const { patientId } = useParams();
  const navigate = useNavigate();
  const [patient, setPatient] = useState(null);
  const [risk, setRisk] = useState(null);
  const [therapySessions, setTherapySessions] = useState([]);
  const [physicianEvaluations, setPhysicianEvaluations] = useState([]);
  const [idtMeetings, setIdtMeetings] = useState([]);
  const [functionalScores, setFunctionalScores] = useState([]);
  const [medicalRecords, setMedicalRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    if (patientId) {
      loadPatientData();
    }
  }, [patientId]);

  const loadPatientData = async () => {
    try {
      setLoading(true);

      // Load all patient data in parallel
      const [
        patientData,
        riskData,
        therapyData,
        physicianData,
        idtData,
        functionalData,
        medicalData
      ] = await Promise.all([
        patientApi.getPatient(patientId),
        riskApi.getPatientRisk(patientId).catch(() => ({ score: 0, status: 'Unknown' })),
        therapyMinutesApi.getTherapySessions(patientId).catch(() => []),
        physicianEvaluationApi.getPhysicianEvaluations(patientId).catch(() => []),
        idtApi.getIdtMeetings(patientId).catch(() => []),
        functionalApi.getFunctionalScores(patientId).catch(() => []),
        medicalNecessityApi.getMedicalNecessityRecords(patientId).catch(() => [])
      ]);

      setPatient(patientData);
      setRisk(riskData);
      setTherapySessions(therapyData);
      setPhysicianEvaluations(physicianData);
      setIdtMeetings(idtData);
      setFunctionalScores(functionalData);
      setMedicalRecords(medicalData);

    } catch (err) {
      setError('Failed to load patient data');
      console.error('Patient detail load error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (score) => {
    if (score >= 61) return 'text-red-600 bg-red-50';
    if (score >= 31) return 'text-yellow-600 bg-yellow-50';
    return 'text-green-600 bg-green-50';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading patient details...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-red-600 text-lg">{error}</div>
      </div>
    );
  }

  return (
    <div className="rc-page">
      <div>
        {/* Header */}
        <div className="rc-card rc-card-elevated p-6 mb-6">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{patient?.name}</h1>
              <p className="text-gray-600">Patient ID: {patient?.patient_id}</p>
              <p className="text-gray-600">Admission: {formatDate(patient?.admission_datetime)}</p>
              {patient?.discharge_datetime && (
                <p className="text-gray-600">Discharge: {formatDate(patient?.discharge_datetime)}</p>
              )}
            </div>
            <div className={`px-4 py-2 rounded-lg ${getRiskColor(risk?.score || 0)}`}>
              <div className="text-2xl font-bold">{risk?.score || 0}</div>
              <div className="text-sm">Risk Score</div>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="rc-card mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex">
              {[
                { id: 'overview', label: 'Overview' },
                { id: 'therapy', label: 'Therapy Minutes' },
                { id: 'physician', label: 'Physician Evaluations' },
                { id: 'idt', label: 'IDT Meetings' },
                { id: 'functional', label: 'Functional Scores' },
                { id: 'medical', label: 'Medical Necessity' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-6 py-3 text-sm font-medium border-b-2 ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div className="rc-card p-6">
          {activeTab === 'overview' && (
            <div>
              <h2 className="text-xl font-semibold mb-4">Patient Overview</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-blue-900 mb-2">Therapy Sessions</h3>
                  <p className="text-2xl font-bold text-blue-600">{therapySessions.length}</p>
                  <p className="text-sm text-blue-700">Total sessions recorded</p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-green-900 mb-2">Physician Evaluations</h3>
                  <p className="text-2xl font-bold text-green-600">{physicianEvaluations.length}</p>
                  <p className="text-sm text-green-700">Evaluations completed</p>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-purple-900 mb-2">IDT Meetings</h3>
                  <p className="text-2xl font-bold text-purple-600">{idtMeetings.length}</p>
                  <p className="text-sm text-purple-700">Meetings held</p>
                </div>
                <div className="bg-yellow-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-yellow-900 mb-2">Functional Scores</h3>
                  <p className="text-2xl font-bold text-yellow-600">{functionalScores.length}</p>
                  <p className="text-sm text-yellow-700">Assessments recorded</p>
                </div>
                <div className="bg-red-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-red-900 mb-2">Medical Records</h3>
                  <p className="text-2xl font-bold text-red-600">{medicalRecords.length}</p>
                  <p className="text-sm text-red-700">Necessity justifications</p>
                </div>
                <div className={`p-4 rounded-lg ${getRiskColor(risk?.score || 0)}`}>
                  <h3 className="font-semibold mb-2">Risk Status</h3>
                  <p className="text-2xl font-bold">{risk?.score || 0}</p>
                  <p className="text-sm">Overall risk score</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'therapy' && (
            <div>
              <h2 className="text-xl font-semibold mb-4">Therapy Sessions</h2>
              {therapySessions.length === 0 ? (
                <p className="text-gray-500">No therapy sessions recorded.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full table-auto">
                    <thead>
                      <tr className="bg-gray-50">
                        <th className="px-4 py-2 text-left">Date</th>
                        <th className="px-4 py-2 text-left">Type</th>
                        <th className="px-4 py-2 text-left">Minutes</th>
                        <th className="px-4 py-2 text-left">Therapist</th>
                      </tr>
                    </thead>
                    <tbody>
                      {therapySessions.map((session) => (
                        <tr key={session.session_id} className="border-t">
                          <td className="px-4 py-2">{formatDate(session.timestamp)}</td>
                          <td className="px-4 py-2">{session.therapy_type}</td>
                          <td className="px-4 py-2">{session.minutes}</td>
                          <td className="px-4 py-2">{session.therapist_id}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {activeTab === 'physician' && (
            <div>
              <h2 className="text-xl font-semibold mb-4">Physician Evaluations</h2>
              {physicianEvaluations.length === 0 ? (
                <p className="text-gray-500">No physician evaluations recorded.</p>
              ) : (
                <div className="space-y-4">
                  {physicianEvaluations.map((eval) => (
                    <div key={eval.evaluation_id} className="border rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <p className="font-semibold">{eval.physician_id}</p>
                          <p className="text-sm text-gray-600">{formatDateTime(eval.evaluation_datetime)}</p>
                        </div>
                      </div>
                      {eval.notes && (
                        <p className="text-gray-700 mt-2">{eval.notes}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'idt' && (
            <div>
              <h2 className="text-xl font-semibold mb-4">IDT Meetings</h2>
              {idtMeetings.length === 0 ? (
                <p className="text-gray-500">No IDT meetings recorded.</p>
              ) : (
                <div className="space-y-4">
                  {idtMeetings.map((meeting) => (
                    <div key={meeting.meeting_id} className="border rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <p className="font-semibold">{formatDateTime(meeting.meeting_datetime)}</p>
                          <p className="text-sm text-gray-600">Attendees: {meeting.attendees?.join(', ') || 'None'}</p>
                        </div>
                      </div>
                      {meeting.notes && (
                        <p className="text-gray-700 mt-2">{meeting.notes}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'functional' && (
            <div>
              <h2 className="text-xl font-semibold mb-4">Functional Scores</h2>
              {functionalScores.length === 0 ? (
                <p className="text-gray-500">No functional scores recorded.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full table-auto">
                    <thead>
                      <tr className="bg-gray-50">
                        <th className="px-4 py-2 text-left">Date</th>
                        <th className="px-4 py-2 text-left">Type</th>
                        <th className="px-4 py-2 text-left">Score</th>
                        <th className="px-4 py-2 text-left">Assessor</th>
                      </tr>
                    </thead>
                    <tbody>
                      {functionalScores.map((score) => (
                        <tr key={score.score_id} className="border-t">
                          <td className="px-4 py-2">{formatDate(score.assessment_date)}</td>
                          <td className="px-4 py-2">{score.score_type}</td>
                          <td className="px-4 py-2">{score.score_value}</td>
                          <td className="px-4 py-2">{score.assessor_id}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {activeTab === 'medical' && (
            <div>
              <h2 className="text-xl font-semibold mb-4">Medical Necessity Records</h2>
              {medicalRecords.length === 0 ? (
                <p className="text-gray-500">No medical necessity records.</p>
              ) : (
                <div className="space-y-4">
                  {medicalRecords.map((record) => (
                    <div key={record.record_id} className="border rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <p className="font-semibold">{record.clinician_id}</p>
                          <p className="text-sm text-gray-600">{formatDate(record.assessment_date)}</p>
                        </div>
                      </div>
                      <p className="text-gray-700 mt-2">{record.justification}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PatientDetail;