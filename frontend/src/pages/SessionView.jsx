import React, { useState, useCallback } from 'react';
import { automationApi } from '../api';
import RiskBadge from '../components/RiskBadge';
import ComplianceFlag from '../components/ComplianceFlag';
import AuditPanel from '../components/AuditPanel';
import DemoPatientLoader from '../components/DemoPatientLoader';
import SessionOverrideModal from '../components/SessionOverrideModal';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const toRiskStatus = (risks = []) => {
  const flags = risks.map((r) => String(r).toLowerCase());
  if (flags.some((f) => f.includes('overload') || f.includes('predictive'))) return 'High';
  if (flags.some((f) => f.includes('cancellation') || f.includes('timeoff'))) return 'Medium';
  if (flags.length > 0) return 'Medium';
  return 'Low';
};

const toSingleRiskStatus = (risk) => {
  const value = String(risk || '').toLowerCase();
  if (value.includes('high') || value.includes('critical') || value.includes('predictive')) return 'High';
  if (value.includes('medium') || value.includes('moderate') || value.includes('timeoff') || value.includes('cancellation')) return 'Medium';
  return 'Low';
};

const ConfidenceBar = ({ score = 0 }) => {
  const pct = Math.max(0, Math.min(100, Math.round(Number(score || 0) * 100)));
  const tone = pct >= 75 ? 'bg-emerald-500' : pct >= 50 ? 'bg-amber-500' : 'bg-rose-500';
  return (
    <div className="mt-2">
      <div className="mb-1 flex items-center justify-between text-xs text-slate-600">
        <span>Confidence</span>
        <span className="font-semibold">{pct}%</span>
      </div>
      <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
        <div className={`h-full ${tone} transition-all`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
};

const ResultCard = ({ title, data, onOverride }) => {
  if (!data) return null;

  const topRec =
    data.recommendations?.[0] ||
    (data.recommended_therapist
      ? { name: data.recommended_therapist, risks: data.risks || [], explanation: data.explanation }
      : null) ||
    (data.recommended_time
      ? { name: data.recommended_time, risks: data.risks || [], explanation: data.explanation }
      : null);

  const risks = data.risks || data.global_risks || topRec?.risks || [];
  const complianceFlags = data.compliance_flags || [];
  const explanation = data.explanation || data.summary_explanation || topRec?.explanation || '';

  return (
    <div className="rounded-2xl border border-blue-200 bg-blue-50/40 p-4 shadow-sm">
      <h3 className="text-sm font-semibold uppercase tracking-wide text-blue-700">{title}</h3>

      {topRec && (
        <p className="mt-2 text-lg font-bold text-slate-900">
          {topRec.name ||
            topRec.therapist_name ||
            topRec.therapist_id ||
            topRec.date ||
            'See details below'}
        </p>
      )}

      <ConfidenceBar score={data.confidence ?? (topRec?.score ? topRec.score / 100 : 0)} />

      <div className="mt-3 flex flex-wrap gap-2">
        <RiskBadge status={toRiskStatus(risks)} />
        {complianceFlags.map((flag, idx) => (
          <ComplianceFlag
            key={idx}
            compliant={flag.compliant !== false}
            reasons={flag.reasons || (flag.compliant === false ? [flag.rule || flag.name || 'flag'] : [])}
          />
        ))}
        {complianceFlags.length === 0 && (
          <ComplianceFlag compliant={true} reasons={[]} />
        )}
      </div>

      {risks.length > 0 && (
        <div className="mt-3 rounded-lg bg-rose-50 px-3 py-2 text-xs text-rose-700">
          <span className="font-semibold">Risks: </span>
          {risks.join(' · ')}
        </div>
      )}

      {explanation && (
        <p className="mt-3 text-sm leading-6 text-slate-700">{explanation}</p>
      )}

      {data.recommendations && data.recommendations.length > 1 && (
        <details className="mt-3">
          <summary className="cursor-pointer text-xs font-medium text-blue-600 hover:underline">
            {data.recommendations.length - 1} alternatives
          </summary>
          <ul className="mt-2 space-y-2">
            {data.recommendations.slice(1).map((rec, idx) => (
              <li key={idx} className="rounded-lg border border-slate-200 bg-white p-2 text-xs text-slate-700">
                <span className="font-medium">
                  {rec.name || rec.therapist_name || rec.therapist_id || rec.date || `Option ${idx + 2}`}
                </span>
                {rec.explanation && <span className="ml-2 text-slate-500">{rec.explanation}</span>}
                <div className="mt-1 flex gap-2">
                  <RiskBadge status={toRiskStatus(rec.risks || [])} />
                </div>
              </li>
            ))}
          </ul>
        </details>
      )}

      <button
        type="button"
        onClick={onOverride}
        className="mt-4 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50"
      >
        Log Override
      </button>
    </div>
  );
};

const RescheduleSuggestionCard = ({ result, onOverride }) => {
  if (!result) return null;

  const recommendedTime = result.recommended_time
    || result.recommendations?.[0]?.recommended_time
    || result.recommendations?.[0]?.start_time
    || 'Not provided';
  const risks = Array.isArray(result.risks) ? result.risks : [];
  const complianceFlags = Array.isArray(result.compliance_flags) ? result.compliance_flags : [];
  const explanation = result.explanation || 'No explanation provided.';

  return (
    <section className="rounded-2xl border border-indigo-200 bg-indigo-50/40 p-4 shadow-sm">
      <h3 className="text-sm font-semibold uppercase tracking-wide text-indigo-700">Reschedule Suggestion</h3>

      <div className="mt-3 rounded-xl border border-indigo-300 bg-white p-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">Recommended Time</p>
        <p className="mt-1 text-lg font-bold text-slate-900">{recommendedTime}</p>
      </div>

      <div className="mt-3">
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-600">Risks</p>
        {risks.length === 0 ? (
          <div className="flex items-center gap-2">
            <RiskBadge status="Low" />
            <span className="text-xs text-slate-500">No risks returned</span>
          </div>
        ) : (
          <ul className="space-y-2">
            {risks.map((risk, idx) => (
              <li key={`${risk}-${idx}`} className="flex items-center gap-2 text-sm text-slate-700">
                <RiskBadge status={toSingleRiskStatus(risk)} />
                <span>{risk}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="mt-3">
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-600">Compliance Flags</p>
        {complianceFlags.length === 0 ? (
          <ComplianceFlag compliant={true} reasons={[]} />
        ) : (
          <ul className="space-y-2">
            {complianceFlags.map((flag, idx) => (
              <li key={idx} className="flex items-center gap-2 text-sm text-slate-700">
                <ComplianceFlag
                  compliant={flag.compliant !== false}
                  reasons={flag.reasons || (flag.compliant === false ? [flag.rule || flag.name || 'Non-compliant rule'] : [])}
                />
                <span>{flag.rule || flag.name || 'Compliance check'}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="mt-3 rounded-lg bg-white px-3 py-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-600">Explanation</p>
        <p className="mt-1 text-sm leading-6 text-slate-700">{explanation}</p>
      </div>

      <button
        type="button"
        onClick={onOverride}
        className="mt-4 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50"
      >
        Log Override
      </button>
    </section>
  );
};

// ---------------------------------------------------------------------------
// Main SessionView
// ---------------------------------------------------------------------------

const SessionView = () => {
  const api = automationApi;
  const [sessionId, setSessionId] = useState('');
  const [assignmentResult, setAssignmentResult] = useState(null);
  const [rescheduleResult, setRescheduleResult] = useState(null);
  const [assignmentLoading, setAssignmentLoading] = useState(false);
  const [rescheduleLoading, setRescheduleLoading] = useState(false);
  const [assignmentError, setAssignmentError] = useState('');
  const [rescheduleError, setRescheduleError] = useState('');
  const [overrideOpen, setOverrideOpen] = useState(false);
  const [auditRefresh, setAuditRefresh] = useState(0);

  const handleSuggestAssignment = useCallback(async () => {
    if (!sessionId.trim()) return;
    setAssignmentLoading(true);
    setAssignmentError('');
    try {
      const data = await api.suggestAssignment(sessionId.trim());
      setAssignmentResult(data);
    } catch (err) {
      setAssignmentError(err.message || 'Assignment suggestion failed');
      setAssignmentResult(null);
    } finally {
      setAssignmentLoading(false);
    }
  }, [api, sessionId]);

  const handleSuggestReschedule = useCallback(async () => {
    if (!sessionId.trim()) return;
    setRescheduleLoading(true);
    setRescheduleError('');
    try {
      const data = await api.suggestReschedule(sessionId.trim());
      setRescheduleResult(data);
    } catch (err) {
      setRescheduleError(err.message || 'Reschedule suggestion failed');
      setRescheduleResult(null);
    } finally {
      setRescheduleLoading(false);
    }
  }, [api, sessionId]);

  const handleOverrideComplete = useCallback(() => {
    setAuditRefresh((n) => n + 1);
  }, []);

  return (
    <div className="space-y-6">
      <header className="rc-card rc-card-elevated">
        <h1 className="text-2xl font-bold text-slate-900">Session Workspace</h1>
        <p className="mt-1 text-sm text-slate-600">
          Manage assignment and reschedule suggestions with transparent audit visibility.
        </p>
      </header>

      <div className="rc-grid grid grid-cols-1 gap-6 xl:grid-cols-2">
        <section className="rc-card">
          <h2 className="text-lg font-semibold text-slate-900">Demo Patient Loader</h2>
          <p className="mt-1 text-sm text-slate-600">Choose a patient and session to load into this workspace.</p>
          <div className="mt-4">
            <DemoPatientLoader
              onSessionSelected={(sid) => {
                setSessionId(sid);
                setAssignmentResult(null);
                setRescheduleResult(null);
              }}
            />
          </div>
        </section>

        <section className="rc-card">
          <h2 className="text-lg font-semibold text-slate-900">Audit Trail</h2>
          <p className="mt-1 text-sm text-slate-600">Track automated recommendations and human overrides.</p>
          <div className="mt-4">
            <AuditPanel sessionId={sessionId.trim()} refreshTrigger={auditRefresh} />
          </div>
        </section>

        <section className="rc-card">
          <h2 className="text-lg font-semibold text-slate-900">Suggest Assignment</h2>
          <div className="mt-3 flex flex-wrap items-end gap-2">
            <div className="min-w-[240px] flex-1">
              <label className="mb-1 block text-xs font-semibold text-slate-600">Session ID</label>
              <input
                value={sessionId}
                onChange={(e) => setSessionId(e.target.value)}
                placeholder="Enter or load a session ID"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
            <button
              type="button"
              onClick={handleSuggestAssignment}
              disabled={assignmentLoading || !sessionId.trim()}
              className="rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {assignmentLoading ? 'Loading…' : 'Suggest Assignment'}
            </button>
          </div>
          {assignmentError && <p className="mt-2 text-xs text-rose-600">{assignmentError}</p>}
          <div className="mt-4">
            {assignmentResult ? (
              <ResultCard title="Assignment Suggestion" data={assignmentResult} onOverride={() => setOverrideOpen(true)} />
            ) : (
              <div className="rounded-xl border border-dashed border-slate-300 p-4 text-sm text-slate-400">
                Assignment recommendation will appear here.
              </div>
            )}
          </div>
        </section>

        <section className="rc-card">
          <h2 className="text-lg font-semibold text-slate-900">Suggest Reschedule</h2>
          <div className="mt-3 flex flex-wrap items-end gap-2">
            <div className="min-w-[240px] flex-1">
              <label className="mb-1 block text-xs font-semibold text-slate-600">Session ID</label>
              <input
                value={sessionId}
                onChange={(e) => setSessionId(e.target.value)}
                placeholder="Enter or load a session ID"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
            <button
              type="button"
              onClick={handleSuggestReschedule}
              disabled={rescheduleLoading || !sessionId.trim()}
              className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {rescheduleLoading ? 'Loading…' : 'Suggest Reschedule'}
            </button>
          </div>
          {rescheduleError && <p className="mt-2 text-xs text-rose-600">{rescheduleError}</p>}
          <div className="mt-4">
            {rescheduleResult ? (
              <RescheduleSuggestionCard result={rescheduleResult} onOverride={() => setOverrideOpen(true)} />
            ) : (
              <div className="rounded-xl border border-dashed border-slate-300 p-4 text-sm text-slate-400">
                Reschedule recommendation will appear here.
              </div>
            )}
          </div>
        </section>
      </div>

      <SessionOverrideModal
        isOpen={overrideOpen}
        sessionId={sessionId.trim()}
        onClose={() => setOverrideOpen(false)}
        onOverrideComplete={handleOverrideComplete}
      />
    </div>
  );
};

export default SessionView;
