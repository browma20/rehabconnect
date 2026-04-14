import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { patientApi, functionalApi } from '../api';

const Functional = () => {
  const { patientId } = useParams();
  const [patient, setPatient] = useState(null);
  const [scores, setScores] = useState([]);
  const [summary, setSummary] = useState(null);
  const [compliance, setCompliance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Form state for new score
  const [scoreForm, setScoreForm] = useState({
    score_type: 'FIM',
    score_value: '',
    assessor_id: '',
    assessment_date: new Date().toISOString().split('T')[0]
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

      const [patientData, scoresData, summaryData, complianceData] = await Promise.all([
        patientApi.getPatient(patientId),
        functionalApi.getFunctionalScores(patientId),
        functionalApi.getFunctionalSummary(patientId),
        functionalApi.getFunctionalCompliance(patientId)
      ]);

      setPatient(patientData);
      setScores(scoresData);
      setSummary(summaryData);
      setCompliance(complianceData);

    } catch (err) {
      setError('Failed to load functional data');
      console.error('Functional load error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setScoreForm(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!scoreForm.score_value || !scoreForm.assessor_id) {
      alert('Please fill in all required fields');
      return;
    }

    try {
      setSubmitting(true);
      await functionalApi.addFunctionalScore(patientId, {
        ...scoreForm,
        score_value: parseFloat(scoreForm.score_value)
      });

      // Reset form and reload data
      setScoreForm({
        score_type: 'FIM',
        score_value: '',
        assessor_id: '',
        assessment_date: new Date().toISOString().split('T')[0]
      });

      await loadPatientData();
      alert('Functional score added successfully!');

    } catch (err) {
      console.error('Failed to add functional score:', err);
      alert('Failed to add functional score. Please try again.');
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

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading functional assessment data...</div>
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
          Functional Assessment - {patient?.name}
        </h1>

        {/* Compliance Status */}
        <div className="rc-card rc-card-elevated p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Functional Improvement Compliance</h2>
          {compliance && (
            <div className={`p-4 rounded-lg ${getComplianceColor(compliance.status)}`}>
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="font-semibold">Current Status: {compliance.status}</h3>
                  {compliance.last_assessment && (
                    <p className="text-sm mt-1">
                      Last assessment: {formatDate(compliance.last_assessment)}
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

        {/* Add Functional Score */}
        <div className="rc-card p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Record Functional Assessment</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Assessment Type
                </label>
                <select
                  name="score_type"
                  value={scoreForm.score_type}
                  onChange={handleInputChange}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="FIM">FIM (Functional Independence Measure)</option>
                  <option value="AM-PAC">AM-PAC</option>
                  <option value="6MWT">6-Minute Walk Test</option>
                  <option value="TUG">Timed Up and Go</option>
                  <option value="BERG">Berg Balance Scale</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Score Value *
                </label>
                <input
                  type="number"
                  name="score_value"
                  value={scoreForm.score_value}
                  onChange={handleInputChange}
                  step="0.1"
                  min="0"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter score"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Assessor ID *
                </label>
                <input
                  type="text"
                  name="assessor_id"
                  value={scoreForm.assessor_id}
                  onChange={handleInputChange}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter assessor ID"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Assessment Date
                </label>
                <input
                  type="date"
                  name="assessment_date"
                  value={scoreForm.assessment_date}
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
              {submitting ? 'Recording Assessment...' : 'Record Functional Assessment'}
            </button>
          </form>
        </div>

        {/* Functional Summary */}
        {summary && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <h2 className="text-xl font-semibold mb-4">Functional Summary</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {Object.entries(summary).map(([scoreType, data]) => (
                <div key={scoreType} className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-gray-900 mb-2">{scoreType}</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Latest Score:</span>
                      <span className="font-medium">{data.latest_score || 'N/A'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Assessments:</span>
                      <span className="font-medium">{data.count || 0}</span>
                    </div>
                    {data.improvement_rate && (
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Improvement:</span>
                        <span className={`font-medium ${data.improvement_rate.rate > 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {data.improvement_rate.rate > 0 ? '+' : ''}{data.improvement_rate.rate.toFixed(2)}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Assessment History */}
        <div className="rc-card p-6">
          <h2 className="text-xl font-semibold mb-4">Assessment History</h2>
          {scores.length === 0 ? (
            <p className="text-gray-500">No functional assessments recorded.</p>
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
                  {scores.map((score) => (
                    <tr key={score.score_id} className="border-t">
                      <td className="px-4 py-2">{formatDate(score.assessment_date)}</td>
                      <td className="px-4 py-2">{score.score_type}</td>
                      <td className="px-4 py-2 font-medium">{score.score_value}</td>
                      <td className="px-4 py-2">{score.assessor_id}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Functional;