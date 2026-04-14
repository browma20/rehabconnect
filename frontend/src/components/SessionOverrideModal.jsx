import React, { useState } from 'react';
import { automationApi as api } from '../api';

const OVERRIDE_TYPES = ['therapist', 'time'];

const SessionOverrideModal = ({ isOpen, sessionId, onClose, onOverrideComplete }) => {
  const [overrideType, setOverrideType] = useState('therapist');
  const [overrideValue, setOverrideValue] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!overrideValue.trim()) {
      setError('Override value is required.');
      return;
    }
    setError('');
    setSubmitting(true);
    try {
      await api.submitOverride({
        sessionId,
        overrideType,
        overrideValue: overrideValue.trim(),
      });
      setOverrideValue('');
      setOverrideType('therapist');
      onClose();
      if (onOverrideComplete) {
        onOverrideComplete();
      }
    } catch (err) {
      setError(err.message || 'Override failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-5 shadow-xl">
        <h3 className="text-lg font-semibold text-slate-900">Log Override</h3>
        <p className="mt-1 text-sm text-slate-500">
          Submit a therapist or time override for session <span className="font-mono font-medium">{sessionId}</span>.
        </p>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-600">Override Type</label>
            <select
              value={overrideType}
              onChange={(e) => setOverrideType(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            >
              {OVERRIDE_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t.charAt(0).toUpperCase() + t.slice(1)} Override
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600">
              {overrideType === 'therapist' ? 'Therapist ID / Name' : 'New Time (e.g. 2024-05-10T09:00)'}
            </label>
            <input
              type="text"
              value={overrideValue}
              onChange={(e) => setOverrideValue(e.target.value)}
              placeholder={overrideType === 'therapist' ? 'THER-001' : '2024-05-10T09:00'}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </div>

          {error && <p className="text-xs text-rose-600">{error}</p>}

          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              {submitting ? 'Submitting…' : 'Submit Override'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default SessionOverrideModal;
