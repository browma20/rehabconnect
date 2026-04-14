import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { patientApi, therapyMinutesApi } from '../api';

const TherapyMinutes = () => {
  const { patientId } = useParams();
  const [patient, setPatient] = useState(null);
  const [dailyCompliance, setDailyCompliance] = useState(null);
  const [rollingCompliance, setRollingCompliance] = useState(null);
  const [therapySummary, setTherapySummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Form state for adding new session
  const [sessionForm, setSessionForm] = useState({
    therapy_type: 'PT',
    minutes: '',
    therapist_id: '',
    timestamp: new Date().toISOString().slice(0, 16) // YYYY-MM-DDTHH:MM format
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (patientId) {
      loadPatientData();
    }
  }, [patientId]);

  const loadPatientData = async () => {
    try {
      setLoading(true);

      // Load patient info
      const patientData = await patientApi.getPatient(patientId);
      setPatient(patientData);

      // Load compliance data
      const today = new Date().toISOString().split('T')[0];
      const daily = await therapyMinutesApi.getDailyCompliance(patientId, today);
      const rolling = await therapyMinutesApi.getRollingCompliance(patientId);
      const summary = await therapyMinutesApi.getTherapySummary(patientId);

      setDailyCompliance(daily);
      setRollingCompliance(rolling);
      setTherapySummary(summary);

    } catch (err) {
      setError('Failed to load patient data');
      console.error('Therapy minutes load error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setSessionForm(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!sessionForm.minutes || !sessionForm.therapist_id) {
      alert('Please fill in all required fields');
      return;
    }

    try {
      setSubmitting(true);
      await therapyMinutesApi.addTherapySession(patientId, {
        ...sessionForm,
        minutes: parseInt(sessionForm.minutes),
        timestamp: sessionForm.timestamp ? new Date(sessionForm.timestamp).toISOString() : undefined
      });

      // Reset form and reload data
      setSessionForm({
        therapy_type: 'PT',
        minutes: '',
        therapist_id: '',
        timestamp: new Date().toISOString().slice(0, 16)
      });

      await loadPatientData();
      alert('Therapy session added successfully!');

    } catch (err) {
      console.error('Failed to add therapy session:', err);
      alert('Failed to add therapy session. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const getComplianceColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'green': return 'text-green-600';
      case 'yellow': return 'text-yellow-600';
      case 'red': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getProgressBarColor = (delivered, target) => {
    const percentage = (delivered / target) * 100;
    if (percentage >= 100) return 'bg-green-500';
    if (percentage >= 67) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading therapy minutes...</div>
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
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          Therapy Minutes - {patient?.name}
        </h1>

        {/* Compliance Overview */}
        <div className="rc-grid grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Daily Compliance */}
          <div className="rc-card p-6">
            <h2 className="text-xl font-semibold mb-4">3-Hour Rule Meter</h2>
            {dailyCompliance && (
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm text-gray-600">Delivered Minutes</span>
                  <span className={`font-semibold ${getComplianceColor(dailyCompliance.status)}`}>
                    {dailyCompliance.delivered || 0}/180
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-4 mb-2">
                  <div
                    className={`h-4 rounded-full transition-all duration-300 ${getProgressBarColor(dailyCompliance.delivered || 0, 180)}`}
                    style={{ width: `${Math.min(((dailyCompliance.delivered || 0) / 180) * 100, 100)}%` }}
                  ></div>
                </div>
                <div className="text-sm text-gray-600">
                  Remaining: {Math.max(0, 180 - (dailyCompliance.delivered || 0))} minutes
                </div>
                <div className={`text-sm font-medium mt-1 ${getComplianceColor(dailyCompliance.status)}`}>
                  Status: {dailyCompliance.status || 'Unknown'}
                </div>
              </div>
            )}
          </div>

          {/* Rolling Compliance */}
          <div className="rc-card p-6">
            <h2 className="text-xl font-semibold mb-4">7-Day Rolling Intensity</h2>
            {rollingCompliance && (
              <div>
                <div className="text-2xl font-bold text-gray-900 mb-2">
                  {rollingCompliance.total_minutes || 0} minutes
                </div>
                <div className={`text-sm font-medium ${getComplianceColor(rollingCompliance.status)}`}>
                  Status: {rollingCompliance.status || 'Unknown'}
                </div>
                {rollingCompliance.notes && (
                  <div className="text-sm text-gray-600 mt-2">
                    {rollingCompliance.notes}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Add Therapy Session Form */}
        <div className="rc-card rc-card-elevated p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Add Therapy Session</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Therapy Type
                </label>
                <select
                  name="therapy_type"
                  value={sessionForm.therapy_type}
                  onChange={handleInputChange}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="PT">Physical Therapy (PT)</option>
                  <option value="OT">Occupational Therapy (OT)</option>
                  <option value="ST">Speech Therapy (ST)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Minutes Delivered *
                </label>
                <input
                  type="number"
                  name="minutes"
                  value={sessionForm.minutes}
                  onChange={handleInputChange}
                  min="0"
                  max="180"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter minutes"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Therapist ID *
                </label>
                <input
                  type="text"
                  name="therapist_id"
                  value={sessionForm.therapist_id}
                  onChange={handleInputChange}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter therapist ID"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Session Date/Time
                </label>
                <input
                  type="datetime-local"
                  name="timestamp"
                  value={sessionForm.timestamp}
                  onChange={handleInputChange}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? 'Adding Session...' : 'Add Therapy Session'}
            </button>
          </form>
        </div>

        {/* Therapy Summary */}
        {therapySummary && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Therapy Summary</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{therapySummary.total_sessions || 0}</div>
                <div className="text-sm text-gray-600">Total Sessions</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{therapySummary.total_minutes || 0}</div>
                <div className="text-sm text-gray-600">Total Minutes</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">{therapySummary.average_daily || 0}</div>
                <div className="text-sm text-gray-600">Avg Daily Minutes</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TherapyMinutes;