import React, { useState } from 'react';

const basePill = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: 6,
  borderRadius: 999,
  padding: '4px 10px',
  fontSize: 12,
  fontWeight: 700,
  border: '1px solid transparent',
  cursor: 'default',
};

const ComplianceFlag = ({ compliant = true, reasons = [] }) => {
  const [tooltipVisible, setTooltipVisible] = useState(false);

  if (compliant) {
    return (
      <span
        style={{
          ...basePill,
          backgroundColor: '#DCFCE7',
          color: '#166534',
          borderColor: '#86EFAC',
        }}
      >
        <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
          <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 0 1 .143 1.052l-8 10.5a.75.75 0 0 1-1.127.075l-4.5-4.5a.75.75 0 0 1 1.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 0 1 1.05-.143Z" clipRule="evenodd" />
        </svg>
        Compliant
      </span>
    );
  }

  return (
    <span style={{ position: 'relative', display: 'inline-flex', alignItems: 'center' }}>
      <button
        type="button"
        onMouseEnter={() => setTooltipVisible(true)}
        onMouseLeave={() => setTooltipVisible(false)}
        onFocus={() => setTooltipVisible(true)}
        onBlur={() => setTooltipVisible(false)}
        style={{
          ...basePill,
          backgroundColor: '#FEE2E2',
          color: '#991B1B',
          borderColor: '#FCA5A5',
          cursor: 'help',
        }}
        aria-label={`Non-compliant: ${reasons.join('; ')}`}
      >
        <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
          <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
        </svg>
        Non-Compliant
      </button>
      {tooltipVisible && reasons.length > 0 && (
        <div
          role="tooltip"
          style={{
            position: 'absolute',
            bottom: 'calc(100% + 8px)',
            left: 0,
            zIndex: 50,
            width: 260,
            borderRadius: 8,
            border: '1px solid #FCA5A5',
            backgroundColor: '#FFFFFF',
            padding: 10,
            boxShadow: '0 8px 22px rgba(15, 23, 42, 0.16)',
          }}
        >
          <p style={{ margin: '0 0 6px', fontSize: 12, fontWeight: 700, color: '#991B1B' }}>Compliance Issues</p>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: '#334155' }}>
            {reasons.map((reason, idx) => (
              <li key={idx} style={{ marginBottom: 3 }}>{reason}</li>
            ))}
          </ul>
          <div
            style={{
              position: 'absolute',
              bottom: -7,
              left: 16,
              width: 12,
              height: 12,
              transform: 'rotate(45deg)',
              borderRight: '1px solid #FCA5A5',
              borderBottom: '1px solid #FCA5A5',
              backgroundColor: '#FFFFFF',
            }}
          />
        </div>
      )}
    </span>
  );
};

export default ComplianceFlag;
