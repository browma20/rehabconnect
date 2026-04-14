import React, { useCallback, useEffect, useState } from 'react';
import { automationApi } from '../api';
import RiskBadge from './RiskBadge';
import ComplianceFlag from './ComplianceFlag';

const toRiskStatus = (riskScore) => {
  if (riskScore == null) return 'Low';
  if (riskScore >= 70) return 'High';
  if (riskScore >= 40) return 'Medium';
  return 'Low';
};

const formatDateTime = (ts) => {
  if (!ts) return '—';
  try {
    return new Date(ts).toLocaleString();
  } catch {
    return ts;
  }
};

const normalizeValue = (entry, key) => {
  if (entry[key]) return entry[key];

  if (key === 'recommended_value' && entry.recommended_option) {
    if (typeof entry.recommended_option === 'string') return entry.recommended_option;
    return (
      entry.recommended_option.name
      || entry.recommended_option.therapist_name
      || entry.recommended_option.therapist_id
      || entry.recommended_option.recommended_time
      || JSON.stringify(entry.recommended_option)
    );
  }

  if (key === 'override_value' && entry.human_choice) {
    if (typeof entry.human_choice === 'string') return entry.human_choice;
    return (
      entry.human_choice.name
      || entry.human_choice.therapist_name
      || entry.human_choice.therapist_id
      || entry.human_choice.override_value
      || JSON.stringify(entry.human_choice)
    );
  }

  return '—';
};

const complianceText = (summary, fallbackReasons = []) => {
  if (!summary) {
    return fallbackReasons.length ? fallbackReasons.join(', ') : 'No compliance notes.';
  }

  if (typeof summary === 'string') return summary;

  const reasons = Array.isArray(summary.reasons) ? summary.reasons : [];
  if (reasons.length) return reasons.join(', ');
  return summary.compliant === false ? 'Non-compliant' : 'Compliant';
};

const AuditEntry = ({ entry }) => {
  const actionType = entry.action_type || entry.event_type || 'action';
  const recommendedValue = normalizeValue(entry, 'recommended_value');
  const overrideValue = normalizeValue(entry, 'override_value');
  const riskScore = entry.risk_score ?? entry.recommended_score;
  const riskStatus = toRiskStatus(riskScore);
  const summary = entry.compliance_summary;
  const fallbackReasons = entry.override_reason ? [entry.override_reason] : [];
  const reasons = Array.isArray(summary?.reasons) ? summary.reasons : fallbackReasons;
  const isCompliant = summary?.compliant !== false;

  return (
    <li className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm">
      <div className="flex items-start gap-3">
        <div className="w-40 shrink-0 text-xs text-slate-500">{formatDateTime(entry.timestamp)}</div>

        <div className="flex-1 space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center rounded-full bg-slate-800 px-2.5 py-1 text-xs font-semibold text-white">
              {actionType}
            </span>
            <RiskBadge status={riskStatus} />
            <ComplianceFlag compliant={isCompliant} reasons={reasons} />
            {riskScore != null && (
              <span className="text-xs text-slate-500">Score: {Number(riskScore).toFixed(2)}</span>
            )}
          </div>

          <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
            <div className="rounded-lg border border-slate-200 bg-white p-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Recommended</p>
              <p className="mt-1 text-sm text-slate-700">{recommendedValue}</p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Override</p>
              <p className="mt-1 text-sm text-slate-700">{overrideValue}</p>
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Compliance Summary</p>
            <p className="mt-1 text-xs text-slate-600">{complianceText(summary, fallbackReasons)}</p>
          </div>
        </div>
      </div>
    </li>
  );
};

const AuditPanel = ({ sessionId, refreshTrigger = 0 }) => {
  const [auditEntries, setAuditEntries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loadEntries = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    setError('');
    try {
      const data = await automationApi.getAuditTrail(sessionId);
      setAuditEntries(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || 'Failed to load audit trail');
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    loadEntries();
  }, [loadEntries, refreshTrigger]);

  const sorted = [...auditEntries].sort(
    (a, b) => new Date(b.timestamp) - new Date(a.timestamp)
  );

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-semibold text-slate-900">Audit Trail</h3>
        <button
          type="button"
          onClick={loadEntries}
          disabled={loading}
          className="rounded-lg border border-slate-200 px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-50"
        >
          {loading ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>

      {error && (
        <p className="mt-2 text-xs text-rose-600">{error}</p>
      )}

      {!loading && sorted.length === 0 && !error && (
        <p className="mt-3 text-sm text-slate-500">No audit entries for this session.</p>
      )}

      {loading && sorted.length === 0 && (
        <p className="mt-3 text-sm text-slate-400">Loading…</p>
      )}

      <ul className="mt-3 space-y-3">
        {sorted.map((entry, idx) => (
          <AuditEntry key={`${entry.id || idx}-${entry.timestamp || idx}`} entry={entry} />
        ))}
      </ul>
    </section>
  );
};

export default AuditPanel;
