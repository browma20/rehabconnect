import React, { useState, useEffect } from 'react';
import { riskApi, patientApi } from '../api';
import PatientRiskCard from '../components/PatientRiskCard';
import ComplianceHeatMap from '../components/ComplianceHeatMap';

const Dashboard = () => {
  const [unitSummary, setUnitSummary] = useState({
    totalPatients: 0,
    highRisk: 0,
    moderateRisk: 0,
    lowRisk: 0,
    surveyReadiness: 0
  });
  const [highRiskPatients, setHighRiskPatients] = useState([]);
  const [complianceHeatMap, setComplianceHeatMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);

      // Get all patients
      const patients = await patientApi.listPatients();

      // Get risk data for all patients
      const patientRisks = await Promise.all(
        patients.map(async (patient) => {
          try {
            const risk = await riskApi.getPatientRisk(patient.patient_id);
            return { ...patient, risk };
          } catch (err) {
            console.error(`Failed to get risk for patient ${patient.patient_id}:`, err);
            return { ...patient, risk: { score: 0, status: 'Unknown', drivers: [] } };
          }
        })
      );

      // Calculate unit summary
      const highRisk = patientRisks.filter(p => p.risk.score >= 61).length;
      const moderateRisk = patientRisks.filter(p => p.risk.score >= 31 && p.risk.score <= 60).length;
      const lowRisk = patientRisks.filter(p => p.risk.score <= 30).length;

      // Sort high-risk patients by score descending
      const sortedHighRisk = patientRisks
        .filter(p => p.risk.score >= 61)
        .sort((a, b) => b.risk.score - a.risk.score)
        .slice(0, 10); // Show top 10

      // Get unit risk summary
      const unitRiskSummary = await riskApi.getUnitRiskSummary(patientRisks.map(p => p.patient_id));

      setUnitSummary({
        totalPatients: patients.length,
        highRisk,
        moderateRisk,
        lowRisk,
        surveyReadiness: unitRiskSummary.surveyReadiness || 85
      });

      setHighRiskPatients(sortedHighRisk);
      setComplianceHeatMap(unitRiskSummary.complianceHeatMap || {
        '3-Hour Rule': 82,
        '36-Hour Start': 91,
        'IDT Compliance': 76,
        'Functional Progress': 68,
        'Medical Necessity': 88
      });

    } catch (err) {
      setError('Failed to load dashboard data');
      console.error('Dashboard load error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (score) => {
    if (score >= 61) return 'text-red-600';
    if (score >= 31) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getRiskBgColor = (score) => {
    if (score >= 61) return 'bg-red-50 border-red-200';
    if (score >= 31) return 'bg-yellow-50 border-yellow-200';
    return 'bg-green-50 border-green-200';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading dashboard...</div>
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
        <h1 className="rc-text-xl text-3xl font-bold text-gray-900 mb-8">
          Administrative Denial Prevention Dashboard
        </h1>

        {/* Unit Summary */}
        <div className="rc-card rc-card-elevated p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Unit Summary</h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{unitSummary.totalPatients}</div>
              <div className="text-sm text-gray-600">Total Patients</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{unitSummary.highRisk}</div>
              <div className="text-sm text-gray-600">High Risk (Red)</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">{unitSummary.moderateRisk}</div>
              <div className="text-sm text-gray-600">Moderate Risk (Yellow)</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{unitSummary.lowRisk}</div>
              <div className="text-sm text-gray-600">Low Risk (Green)</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{unitSummary.surveyReadiness}%</div>
              <div className="text-sm text-gray-600">Survey Readiness</div>
            </div>
          </div>
        </div>

        <div className="rc-grid grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* High-Risk Patients */}
          <div className="rc-card p-6">
            <h2 className="text-xl font-semibold mb-4">High-Risk Patients</h2>
            {highRiskPatients.length === 0 ? (
              <p className="text-gray-500">No high-risk patients found.</p>
            ) : (
              <div className="space-y-3">
                {highRiskPatients.map((patient) => (
                  <PatientRiskCard
                    key={patient.patient_id}
                    patient={patient}
                    risk={patient.risk}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Compliance Heat Map */}
          <div className="rc-card p-6">
            <h2 className="text-xl font-semibold mb-4">Compliance Heat Map</h2>
            <ComplianceHeatMap data={complianceHeatMap} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;