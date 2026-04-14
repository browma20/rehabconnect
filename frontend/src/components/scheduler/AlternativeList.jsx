import React from 'react';
import RiskBadges from './RiskBadges';

const AlternativeList = ({ alternatives = [], onSelect }) => {
  if (!alternatives.length) {
    return <p className="text-sm text-slate-500">No alternatives available.</p>;
  }

  return (
    <div className="space-y-3">
      {alternatives.map((item, idx) => {
        const name = item.name || item.therapist_name || item.therapist_id || `Alternative ${idx + 1}`;
        return (
          <div key={`${name}-${item.start_time}-${idx}`} className="rounded-xl border border-slate-200 bg-white p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h4 className="text-sm font-semibold text-slate-800">{name}</h4>
                <p className="text-xs text-slate-600">{item.date || ''} {item.start_time || ''} - {item.end_time || ''}</p>
              </div>
              <div className="text-sm font-semibold text-slate-800">{Number(item.score || 0).toFixed(2)}</div>
            </div>

            <p className="mt-2 text-xs text-slate-600">{item.explanation || 'No explanation available.'}</p>
            <div className="mt-2">
              <RiskBadges
                risks={item.risks || []}
                riskPenalties={item.risk_penalties || item.slot_risk_penalties || {}}
                dataGaps={item.data_gaps || []}
              />
            </div>
            <div className="mt-3">
              <button
                type="button"
                onClick={() => onSelect && onSelect(item)}
                className="rounded-lg border border-blue-200 bg-blue-50 px-3 py-1.5 text-xs font-medium text-blue-700 hover:bg-blue-100"
              >
                Select
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default AlternativeList;
