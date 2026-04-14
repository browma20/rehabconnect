import React from 'react';
import RiskBadges from './RiskBadges';

const RecommendationCard = ({
  recommendation,
  isTop = false,
  onAccept,
  onChooseDifferent,
}) => {
  if (!recommendation) return null;

  const label = recommendation.name || recommendation.therapist_name || recommendation.therapist_id || 'Recommended Option';
  const when = recommendation.date
    ? `${recommendation.date} ${recommendation.start_time || ''} - ${recommendation.end_time || ''}`
    : `${recommendation.start_time || ''} - ${recommendation.end_time || ''}`;

  return (
    <article className={`rounded-2xl border p-4 shadow-sm ${isTop ? 'border-blue-200 bg-blue-50/50' : 'border-slate-200 bg-white'}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-500">{isTop ? 'Top Recommendation' : 'Recommendation'}</p>
          <h3 className="text-lg font-semibold text-slate-900">{label}</h3>
          <p className="text-sm text-slate-600">{when}</p>
        </div>
        <div className="rounded-lg bg-slate-900 px-3 py-2 text-right text-white">
          <p className="text-xs uppercase tracking-wide text-slate-200">Score</p>
          <p className="text-xl font-bold">{Number(recommendation.score || 0).toFixed(2)}</p>
        </div>
      </div>

      <p className="mt-3 text-sm leading-6 text-slate-700">{recommendation.explanation || 'No explanation available.'}</p>

      <div className="mt-3 space-y-2">
        <RiskBadges
          risks={recommendation.risks || []}
          riskPenalties={recommendation.risk_penalties || recommendation.slot_risk_penalties || {}}
          dataGaps={recommendation.data_gaps || []}
        />

        {(recommendation.data_gaps || []).length > 0 && (
          <div className="rounded-lg bg-slate-50 p-2 text-xs text-slate-600">
            Data Gaps: {(recommendation.data_gaps || []).join(', ')}
          </div>
        )}
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => onAccept && onAccept(recommendation)}
          className="rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700"
        >
          Accept Recommendation
        </button>
        <button
          type="button"
          onClick={() => onChooseDifferent && onChooseDifferent(recommendation)}
          className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
        >
          Choose Different Therapist/Time
        </button>
      </div>
    </article>
  );
};

export default RecommendationCard;
