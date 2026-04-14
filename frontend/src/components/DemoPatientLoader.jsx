import React, { useCallback, useEffect, useState } from 'react';
import apiClient from '../api/apiClient';

const MOCK_DEMO_PATIENTS = [
  { patient_id: 'DEMO-P001', first_name: 'Emma', last_name: 'Johnson' },
  { patient_id: 'DEMO-P002', first_name: 'Noah', last_name: 'Williams' },
  { patient_id: 'DEMO-P003', first_name: 'Ava', last_name: 'Brown' },
];

const DemoPatientLoader = ({ onSessionSelected, onSessionSelect }) => {
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState('');
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState('');
  const [loadingPatients, setLoadingPatients] = useState(false);
  const [loadingSessions, setLoadingSessions] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchPatients = async () => {
      setLoadingPatients(true);
      setError('');
      try {
        const data = await apiClient.get('/patients/demo');
        setPatients(Array.isArray(data) ? data : []);
      } catch (err) {
        // Fallback for demos if backend endpoint is unavailable.
        setPatients(MOCK_DEMO_PATIENTS);
        setError('Using local demo patients (GET /patients/demo unavailable).');
      } finally {
        setLoadingPatients(false);
      }
    };
    fetchPatients();
  }, []);

  const handlePatientChange = useCallback(async (patientId) => {
    setSelectedPatient(patientId);
    setSelectedSession('');
    setSessions([]);
    if (!patientId) return;

    setLoadingSessions(true);
    setError('');
    try {
      const data = await apiClient.get(`/patients/${encodeURIComponent(patientId)}/sessions`);
      const list = Array.isArray(data) ? data : (data.sessions || data.data || []);
      setSessions(list);
    } catch (err) {
      // Fallback to query-based endpoint if dedicated endpoint is unavailable.
      try {
        const fallbackData = await apiClient.get(`/sessions?patient_id=${encodeURIComponent(patientId)}`);
        const fallbackList = Array.isArray(fallbackData) ? fallbackData : (fallbackData.sessions || []);
        setSessions(fallbackList);
      } catch {
        setError('Could not load sessions for this patient.');
      }
    } finally {
      setLoadingSessions(false);
    }
  }, []);

  const handleSessionChange = (sessionId) => {
    setSelectedSession(sessionId);
    const callback = onSessionSelected || onSessionSelect;
    if (callback) {
      callback(sessionId);
    }
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="text-base font-semibold text-slate-900">Demo Patient Loader</h3>
      <p className="mt-1 text-xs text-slate-500">Select a patient to browse their sessions and load one into the scheduler.</p>

      <div className="mt-3">
        <label className="mb-1 block text-xs font-semibold text-slate-600">Patient</label>
        {loadingPatients ? (
          <p className="text-xs text-slate-400">Loading patients…</p>
        ) : (
          <select
            value={selectedPatient}
            onChange={(e) => handlePatientChange(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800"
          >
            <option value="">— Select a patient —</option>
            {patients.map((p) => (
              <option key={p.patient_id} value={p.patient_id}>
                {p.first_name} {p.last_name} ({p.patient_id})
              </option>
            ))}
          </select>
        )}
      </div>

      {error && <p className="mt-2 text-xs text-rose-600">{error}</p>}

      {selectedPatient && (
        <div className="mt-4">
          <label className="mb-1 block text-xs font-semibold text-slate-600">Session</label>
          {loadingSessions ? (
            <p className="text-xs text-slate-400">Loading sessions…</p>
          ) : (
            <select
              value={selectedSession}
              onChange={(e) => handleSessionChange(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800"
            >
              <option value="">— Select a session —</option>
              {sessions.map((session) => {
                const sid = session.id || session.session_id;
                const label = `${session.discipline || 'Session'} · ${session.date || ''} ${session.start_time || ''}-${session.end_time || ''}`.trim();
                return (
                  <option key={sid} value={sid}>
                    {label} ({sid})
                  </option>
                );
              })}
            </select>
          )}
          {!loadingSessions && sessions.length === 0 && !error && (
            <p className="mt-2 text-xs text-slate-500">No sessions found for this patient.</p>
          )}
        </div>
      )}
    </div>
  );
};

export default DemoPatientLoader;
