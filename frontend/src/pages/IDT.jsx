import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { patientApi, idtApi } from '../api';

const IDT = () => {
  const { patientId } = useParams();
  const [patient, setPatient] = useState(null);
  const [meetings, setMeetings] = useState([]);
  const [compliance, setCompliance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Form state for new meeting
  const [meetingForm, setMeetingForm] = useState({
    meeting_datetime: '',
    attendees: '',
    notes: ''
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

      const [patientData, meetingsData, complianceData] = await Promise.all([
        patientApi.getPatient(patientId),
        idtApi.getIdtMeetings(patientId),
        idtApi.getIdtCompliance(patientId)
      ]);

      setPatient(patientData);
      setMeetings(meetingsData);
      setCompliance(complianceData);

    } catch (err) {
      setError('Failed to load IDT data');
      console.error('IDT load error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setMeetingForm(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!meetingForm.meeting_datetime) {
      alert('Please select a meeting date and time');
      return;
    }

    try {
      setSubmitting(true);
      const attendees = meetingForm.attendees
        ? meetingForm.attendees.split(',').map(a => a.trim()).filter(a => a)
        : [];

      await idtApi.createIdtMeeting(patientId, {
        ...meetingForm,
        attendees
      });

      // Reset form and reload data
      setMeetingForm({
        meeting_datetime: '',
        attendees: '',
        notes: ''
      });

      await loadPatientData();
      alert('IDT meeting created successfully!');

    } catch (err) {
      console.error('Failed to create IDT meeting:', err);
      alert('Failed to create IDT meeting. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const getComplianceColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'green': return 'text-green-600 bg-green-50';
      case 'yellow': return 'text-yellow-600 bg-yellow-50';
      case 'red': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading IDT data...</div>
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
          IDT Meetings - {patient?.name}
        </h1>

        {/* Compliance Status */}
        <div className="rc-card rc-card-elevated p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">IDT Compliance Status</h2>
          {compliance && (
            <div className={`p-4 rounded-lg ${getComplianceColor(compliance.status)}`}>
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="font-semibold">Current Status: {compliance.status}</h3>
                  {compliance.days_since_last && (
                    <p className="text-sm mt-1">
                      Days since last meeting: {compliance.days_since_last}
                    </p>
                  )}
                  {compliance.next_due && (
                    <p className="text-sm">
                      Next meeting due: {formatDateTime(compliance.next_due)}
                    </p>
                  )}
                </div>
                {compliance.status === 'Red' && (
                  <div className="text-red-600 font-bold text-lg">⚠️</div>
                )}
              </div>
              {compliance.notes && (
                <p className="text-sm mt-2">{compliance.notes}</p>
              )}
            </div>
          )}
        </div>

        {/* Schedule New Meeting */}
        <div className="rc-card p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Schedule IDT Meeting</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Meeting Date & Time *
                </label>
                <input
                  type="datetime-local"
                  name="meeting_datetime"
                  value={meetingForm.meeting_datetime}
                  onChange={handleInputChange}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Attendees (comma-separated)
                </label>
                <input
                  type="text"
                  name="attendees"
                  value={meetingForm.attendees}
                  onChange={handleInputChange}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="PT, OT, MD, RN..."
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Meeting Notes
              </label>
              <textarea
                name="notes"
                value={meetingForm.notes}
                onChange={handleInputChange}
                rows={4}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Meeting agenda, decisions, action items..."
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? 'Scheduling Meeting...' : 'Schedule IDT Meeting'}
            </button>
          </form>
        </div>

        {/* Meeting History */}
        <div className="rc-card p-6">
          <h2 className="text-xl font-semibold mb-4">IDT Meeting History</h2>
          {meetings.length === 0 ? (
            <p className="text-gray-500">No IDT meetings recorded.</p>
          ) : (
            <div className="space-y-4">
              {meetings.map((meeting) => (
                <div key={meeting.meeting_id} className="border rounded-lg p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-semibold text-lg">
                        {formatDateTime(meeting.meeting_datetime)}
                      </h3>
                      {meeting.attendees && meeting.attendees.length > 0 && (
                        <p className="text-sm text-gray-600 mt-1">
                          Attendees: {meeting.attendees.join(', ')}
                        </p>
                      )}
                    </div>
                  </div>
                  {meeting.notes && (
                    <div className="bg-gray-50 p-3 rounded-md">
                      <p className="text-gray-700 whitespace-pre-wrap">{meeting.notes}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default IDT;