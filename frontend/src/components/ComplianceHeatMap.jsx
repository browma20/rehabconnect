import React from 'react';

const ComplianceHeatMap = ({ data }) => {
  const getComplianceColor = (percentage) => {
    if (percentage >= 90) return 'bg-green-500';
    if (percentage >= 80) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getStatusText = (percentage) => {
    if (percentage >= 90) return 'Green';
    if (percentage >= 80) return 'Yellow';
    return 'Red';
  };

  const getStatusColor = (percentage) => {
    if (percentage >= 90) return 'text-green-600';
    if (percentage >= 80) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-4">
      {Object.entries(data).map(([metric, percentage]) => (
        <div key={metric} className="flex items-center space-x-4">
          <div className="flex-1">
            <div className="flex justify-between items-center mb-1">
              <span className="text-sm font-medium text-gray-700">{metric}</span>
              <span className={`text-sm font-semibold ${getStatusColor(percentage)}`}>
                {percentage}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all duration-300 ${getComplianceColor(percentage)}`}
                style={{ width: `${percentage}%` }}
              ></div>
            </div>
          </div>
          <div className={`text-sm font-medium ${getStatusColor(percentage)}`}>
            {getStatusText(percentage)}
          </div>
        </div>
      ))}
    </div>
  );
};

export default ComplianceHeatMap;