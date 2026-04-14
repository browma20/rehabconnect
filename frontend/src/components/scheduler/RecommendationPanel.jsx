import React from 'react';
import RecommendationCard from './RecommendationCard';
import AlternativeList from './AlternativeList';
import ConfidenceMeter from './ConfidenceMeter';

const RecommendationPanel = ({
  recommendations = [],
  confidence = 0,
  confidence_components = {},
  summary_explanation = '',
  global_risks = [],
  onAcceptTop,
  onChooseDifferent,
  onSelectAlternative,
}) => {
  const [top, ...alternatives] = recommendations;

  return (
    <section className="space-y-4">
      <ConfidenceMeter confidence={confidence} components={confidence_components} />

      {top ? (
        <RecommendationCard
          recommendation={top}
          isTop
          onAccept={onAcceptTop}
          onChooseDifferent={() => onChooseDifferent && onChooseDifferent(top, alternatives)}
        />
      ) : (
        <div className="rounded-xl border border-dashed border-slate-300 p-4 text-sm text-slate-600">No recommendations returned.</div>
      )}

      <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <h3 className="text-base font-semibold text-slate-900">Alternatives</h3>
        <div className="mt-3">
          <AlternativeList alternatives={alternatives} onSelect={onSelectAlternative} />
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <h3 className="text-base font-semibold text-slate-900">Summary</h3>
        <p className="mt-2 text-sm leading-6 text-slate-700">{summary_explanation || 'No summary available.'}</p>
        {(global_risks || []).length > 0 && (
          <div className="mt-3 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">
            <p className="font-semibold">Global Risks</p>
            <ul className="mt-1 list-disc pl-5">
              {global_risks.map((risk, idx) => (
                <li key={`${risk}-${idx}`}>{risk}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </section>
  );
};

export default RecommendationPanel;
