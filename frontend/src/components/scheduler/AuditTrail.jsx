import React from 'react';

const formatOption = (option) => {
  if (!option) return null;
  if (typeof option === 'string') return option;
  const parts = [
    option.name || option.therapist_name || option.therapist_id,
    option.date,
    option.start_time && `${option.start_time}–${option.end_time}`,
  ].filter(Boolean);
  return parts.length ? parts.join(' ') : JSON.stringify(option);
};

const AuditTrail = ({ entries = [] }) => {
  const sorted = [...entries].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="text-base font-semibold text-slate-900">Audit Trail</h3>
      {sorted.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500">No actions logged in this session.</p>
      ) : (
        <ul className="mt-3 space-y-3">
          {sorted.map((entry, idx) => (
            <li key={`${entry.timestamp}-${idx}`} className="rounded-lg border border-slate-100 bg-slate-50 p-3 text-sm text-slate-700">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-semibold text-slate-800">{entry.event_type}</span>
                <span className="text-xs text-slate-500">{entry.timestamp}</span>
              </div>
              {entry.recommended_option && (
                <p className="mt-1"><span className="font-medium">System: </span>{formatOption(entry.recommended_option)}</p>
              )}
              {entry.human_choice && Object.keys(entry.human_choice).length > 0 && (
                <p><span className="font-medium">Human choice: </span>{formatOption(entry.human_choice)}</p>
              )}
              {entry.confidence_score != null && (
                <p><span className="font-medium">Confidence: </span>{Math.round(entry.confidence_score * 100)}%</p>
              )}
              {entry.risks?.length > 0 && (
                <p><span className="font-medium">Risks: </span>{entry.risks.join(', ')}</p>
              )}
              {entry.override_reason && (
                <p><span className="font-medium">Reason: </span>{entry.override_reason}</p>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
};

export default AuditTrail;
