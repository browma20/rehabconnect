import React from 'react';

const ConfidenceMeter = ({ confidence = 0, components = {} }) => {
  const percent = Math.max(0, Math.min(100, Math.round(Number(confidence || 0) * 100)));
  const tone = percent >= 75 ? 'bg-emerald-500' : percent >= 50 ? 'bg-amber-500' : 'bg-rose-500';

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-800">Confidence</h3>
        <span className="text-sm font-semibold text-slate-700">{percent}%</span>
      </div>
      <div className="h-3 w-full overflow-hidden rounded-full bg-slate-100" title={`Match Quality: ${components.match_quality || 0}\nCandidate Spread: ${components.candidate_spread || 0}\nData Completeness: ${components.data_completeness || 0}\nRisk Adjustment: ${components.risk_adjustment || 0}`}>
        <div className={`h-full ${tone}`} style={{ width: `${percent}%` }} />
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-slate-600 sm:grid-cols-4">
        <div>MQ: {components.match_quality ?? 0}</div>
        <div>CS: {components.candidate_spread ?? 0}</div>
        <div>DC: {components.data_completeness ?? 0}</div>
        <div>RA: {components.risk_adjustment ?? 0}</div>
      </div>
    </div>
  );
};

export default ConfidenceMeter;
