import React from 'react';

const BADGE_STYLES = {
  Low: { background: '#DCFCE7', border: '#86EFAC', text: '#166534', dot: '#22C55E' },
  Medium: { background: '#FEF3C7', border: '#FCD34D', text: '#92400E', dot: '#F59E0B' },
  High: { background: '#FEE2E2', border: '#FCA5A5', text: '#991B1B', dot: '#EF4444' },
};

const RiskBadge = ({ status = 'Low' }) => {
  const palette = BADGE_STYLES[status] || BADGE_STYLES.Low;

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        borderRadius: 999,
        padding: '4px 10px',
        border: `1px solid ${palette.border}`,
        backgroundColor: palette.background,
        color: palette.text,
        fontSize: 12,
        fontWeight: 700,
        lineHeight: 1,
      }}
    >
      <span
        style={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          backgroundColor: palette.dot,
          display: 'inline-block',
        }}
      />
      {status}
    </span>
  );
};

export default RiskBadge;
