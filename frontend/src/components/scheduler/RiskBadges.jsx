import React from 'react';

const BADGE_CONFIG = {
  overload_risk: { label: 'Overload', tone: 'bg-rose-100 text-rose-700 border-rose-200' },
  timeoff_proximity: { label: 'Time Off', tone: 'bg-amber-100 text-amber-700 border-amber-200' },
  high_cancellation_risk: { label: 'Cancellation Risk', tone: 'bg-orange-100 text-orange-700 border-orange-200' },
  predictive_alert: { label: 'Predictive Alert', tone: 'bg-violet-100 text-violet-700 border-violet-200' },
  missing_data: { label: 'Missing Data', tone: 'bg-slate-100 text-slate-700 border-slate-200' },
};

const toRiskKey = (risk) => {
  const value = String(risk || '').toLowerCase();
  if (value.includes('overload')) return 'overload_risk';
  if (value.includes('time') && value.includes('off')) return 'timeoff_proximity';
  if (value.includes('cancellation') || value.includes('reliability')) return 'high_cancellation_risk';
  if (value.includes('predictive')) return 'predictive_alert';
  return null;
};

const RiskBadges = ({ risks = [], riskPenalties = {}, dataGaps = [] }) => {
  const keys = new Set();

  Object.keys(riskPenalties || {}).forEach((k) => {
    if ((riskPenalties[k] || 0) > 0 && BADGE_CONFIG[k]) {
      keys.add(k);
    }
  });

  risks.forEach((risk) => {
    const mapped = toRiskKey(risk);
    if (mapped) keys.add(mapped);
  });

  if ((dataGaps || []).length > 0) {
    keys.add('missing_data');
  }

  if (keys.size === 0) {
    return <span className="text-xs text-emerald-700 bg-emerald-100 px-2 py-1 rounded-full">Low Risk</span>;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {Array.from(keys).map((key) => {
        const cfg = BADGE_CONFIG[key];
        if (!cfg) return null;
        return (
          <span
            key={key}
            className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium ${cfg.tone}`}
          >
            {cfg.label}
          </span>
        );
      })}
    </div>
  );
};

export default RiskBadges;
