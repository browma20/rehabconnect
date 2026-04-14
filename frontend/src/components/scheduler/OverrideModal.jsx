import React, { useMemo, useState } from 'react';

const REASONS = [
  'Clinical continuity',
  'Patient preference',
  'Staffing constraint',
  'Schedule practicality',
  'Other',
];

const optionLabel = (item) => {
  if (!item) return 'Not selected';
  const name = item.name || item.therapist_name || item.therapist_id || 'Option';
  const time = `${item.date || ''} ${item.start_time || ''}-${item.end_time || ''}`.trim();
  return `${name} | ${time}`;
};

const OverrideModal = ({
  isOpen,
  recommendedOption,
  alternatives = [],
  onClose,
  onSubmit,
}) => {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [reason, setReason] = useState(REASONS[0]);
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const selectedOption = useMemo(() => alternatives[selectedIndex] || null, [alternatives, selectedIndex]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!recommendedOption || !selectedOption) return;

    setSubmitting(true);
    try {
      await onSubmit({
        recommendedOption,
        chosenOption: selectedOption,
        reason,
        notes,
      });
      onClose();
      setNotes('');
      setReason(REASONS[0]);
      setSelectedIndex(0);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
      <div className="w-full max-w-xl rounded-2xl bg-white p-5 shadow-xl">
        <h3 className="text-lg font-semibold text-slate-900">Override Recommendation</h3>
        <p className="mt-1 text-sm text-slate-600">Log human override for audit and analytics. No automatic schedule changes are applied.</p>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-600">Recommended Option</label>
            <div className="mt-1 rounded-lg border border-slate-200 bg-slate-50 p-2 text-sm text-slate-700">{optionLabel(recommendedOption)}</div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600">Chosen Option</label>
            <select
              value={selectedIndex}
              onChange={(e) => setSelectedIndex(Number(e.target.value))}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            >
              {alternatives.map((item, idx) => (
                <option key={`${idx}-${item.start_time || ''}`} value={idx}>{optionLabel(item)}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600">Override Reason</label>
            <select value={reason} onChange={(e) => setReason(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
              {REASONS.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600">Notes</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              placeholder="Add context for this override"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </div>

          <div className="flex justify-end gap-2">
            <button type="button" onClick={onClose} className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700">Cancel</button>
            <button type="submit" disabled={submitting || !selectedOption} className="rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-50">
              {submitting ? 'Logging...' : 'Log Override'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default OverrideModal;
