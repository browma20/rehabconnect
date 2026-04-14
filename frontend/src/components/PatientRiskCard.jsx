import React from 'react';
import { useNavigate } from 'react-router-dom';

const PatientRiskCard = ({ patient, risk }) => {
  const navigate = useNavigate();

  const getRiskColor = (score) => {
    if (score >= 61) return 'text-red-600 bg-red-50 border-red-200';
    if (score >= 31) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-green-600 bg-green-50 border-green-200';
  };

  const getStatusText = (score) => {
    if (score >= 61) return 'High Risk';
    if (score >= 31) return 'Moderate Risk';
    return 'Low Risk';
  };

  return (
    <div className={`border rounded-lg p-4 ${getRiskColor(risk.score)}`}>
      <div className="flex justify-between items-start mb-2">
        <div>
          <h3 className="font-semibold text-gray-900">{patient.name}</h3>
          <p className="text-sm text-gray-600">ID: {patient.patient_id}</p>
        </div>
        <div className="text-right">
          <div className="text-lg font-bold">{risk.score}</div>
          <div className="text-sm">{getStatusText(risk.score)}</div>
        </div>
      </div>

      {risk.drivers && risk.drivers.length > 0 && (
        <div className="mb-3">
          <p className="text-sm font-medium text-gray-700 mb-1">Top Risk Drivers:</p>
          <ul className="text-sm text-gray-600 space-y-1">
            {risk.drivers.slice(0, 3).map((driver, index) => (
              <li key={index} className="flex items-center">
                <span className="w-2 h-2 bg-red-400 rounded-full mr-2"></span>
                {driver}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex space-x-2">
        <button
          onClick={() => navigate(`/patients/${patient.patient_id}`)}
          className="text-sm bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 transition-colors"
        >
          View Full Record
        </button>
        <button
          onClick={() => {
            // TODO: Implement export functionality
            console.log('Export patient summary:', patient.patient_id);
          }}
          className="text-sm bg-gray-600 text-white px-3 py-1 rounded hover:bg-gray-700 transition-colors"
        >
          Export Summary
        </button>
      </div>
    </div>
  );
};

export default PatientRiskCard;