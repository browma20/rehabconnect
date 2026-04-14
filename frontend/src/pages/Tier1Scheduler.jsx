import React, { useCallback, useMemo, useState } from 'react';
import { automationApi } from '../api';
import RecommendationPanel from '../components/scheduler/RecommendationPanel';
import OverrideModal from '../components/scheduler/OverrideModal';
import AuditTrail from '../components/scheduler/AuditTrail';

const Tier1Scheduler = () => {
  const [sessionId, setSessionId] = useState('');
  const [mode, setMode] = useState('assignment');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [payload, setPayload] = useState(null);
  const [overrideOpen, setOverrideOpen] = useState(false);
  const [recommendedOption, setRecommendedOption] = useState(null);
  const [alternatives, setAlternatives] = useState([]);
  const [auditEntries, setAuditEntries] = useState([]);

  const recommendations = useMemo(() => payload?.recommendations || [], [payload]);

  const loadAuditEntries = useCallback(async (sid) => {
    try {
      const entries = await automationApi.getAuditTrail(sid);
      setAuditEntries(Array.isArray(entries) ? entries : []);
    } catch (_) {
      // audit trail is non-critical
    }
  }, []);

  const loadRecommendations = async (e) => {
    e.preventDefault();
    if (!sessionId.trim()) return;

    setLoading(true);
    setError('');

    try {
      const data = mode === 'assignment'
        ? await automationApi.suggestAssignment(sessionId.trim())
        : await automationApi.suggestReschedule(sessionId.trim());

      setPayload(data);
      const [top, ...rest] = data.recommendations || [];
      setRecommendedOption(top || null);
      setAlternatives(rest);
      await loadAuditEntries(sessionId.trim());
    } catch (err) {
      setError(err.message || 'Failed to load recommendations');
      setPayload(null);
    } finally {
      setLoading(false);
    }
  };

  const handleAccept = async (option) => {
    if (!sessionId.trim()) return;
    try {
      await automationApi.logManualAction({
        session_id: sessionId.trim(),
        event_type: mode === 'assignment' ? 'manual_assignment' : 'manual_reschedule',
        performed_by: 'scheduler_ui',
        human_choice: option || {},
        metadata: {
          confidence: payload?.confidence,
          risks: option?.risks || payload?.global_risks || [],
        },
      });
    } catch (_) {
      // best-effort
    }
    await loadAuditEntries(sessionId.trim());
  };

  const openOverride = (top, alts) => {
    setRecommendedOption(top || null);
    setAlternatives(alts || []);
    setOverrideOpen(true);
  };

  const handleSelectAlternative = (item) => {
    if (!recommendations.length) return;
    const [top, ...rest] = recommendations;
    const reordered = [item, top, ...rest.filter((x) => x !== item)];
    setPayload((prev) => ({ ...prev, recommendations: reordered }));
    setRecommendedOption(top);
    setAlternatives(reordered.slice(1));
    setOverrideOpen(true);
  };

  const handleOverrideSubmit = async ({ recommendedOption: rec, chosenOption, reason, notes }) => {
    if (!sessionId || !rec || !chosenOption) return;

    const metadata = {
      recommended_score: rec.score,
      chosen_score: chosenOption.score,
      confidence: payload?.confidence,
      risks: chosenOption.risks || payload?.global_risks || [],
      data_gaps: chosenOption.data_gaps || [],
      overridden_by: 'scheduler_ui',
    };

    await automationApi.logOverride({
      session_id: sessionId.trim(),
      recommended_therapist_id: rec.therapist_id || rec.name || 'recommended_option',
      chosen_therapist_id: chosenOption.therapist_id || chosenOption.name || 'chosen_option',
      reason: notes ? `${reason}: ${notes}` : reason,
      metadata,
    });

    await loadAuditEntries(sessionId.trim());
  };

  return (
    <div className="rc-page p-4 sm:p-6">
      <div className="space-y-6">
        <header className="rc-card rc-card-elevated rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h1 className="text-2xl font-bold text-slate-900">Tier 1 Scheduler</h1>
          <p className="mt-1 text-sm text-slate-600">Suggestion-only workflow for assignment and reschedule recommendations.</p>
        </header>

        <form onSubmit={loadRecommendations} className="rc-card rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
            <div className="md:col-span-2">
              <label className="mb-1 block text-xs font-semibold text-slate-600">Session ID</label>
              <input
                value={sessionId}
                onChange={(e) => setSessionId(e.target.value)}
                placeholder="Enter session ID"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-600">Mode</label>
              <select value={mode} onChange={(e) => setMode(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
                <option value="assignment">Suggest Assignment</option>
                <option value="reschedule">Suggest Reschedule</option>
              </select>
            </div>
            <div className="flex items-end">
              <button type="submit" disabled={loading} className="w-full rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-50">
                {loading ? 'Loading...' : 'Load Recommendations'}
              </button>
            </div>
          </div>
          {error && <p className="mt-3 text-sm text-rose-600">{error}</p>}
        </form>

        <div className="rc-grid grid grid-cols-1 gap-6 xl:grid-cols-3">
          <div className="xl:col-span-2">
            <RecommendationPanel
              recommendations={payload?.recommendations || []}
              confidence={payload?.confidence || 0}
              confidence_components={payload?.confidence_components || {}}
              summary_explanation={payload?.summary_explanation || ''}
              global_risks={payload?.global_risks || []}
              onAcceptTop={handleAccept}
              onChooseDifferent={openOverride}
              onSelectAlternative={handleSelectAlternative}
            />
          </div>
          <div>
            <AuditTrail entries={auditEntries} />
          </div>
        </div>
      </div>

      <OverrideModal
        isOpen={overrideOpen}
        recommendedOption={recommendedOption}
        alternatives={alternatives}
        onClose={() => setOverrideOpen(false)}
        onSubmit={handleOverrideSubmit}
      />
    </div>
  );
};

export default Tier1Scheduler;
