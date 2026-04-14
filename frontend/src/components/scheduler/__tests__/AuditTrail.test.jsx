import React from 'react';
import { render, screen } from '@testing-library/react';
import AuditTrail from '../AuditTrail';

const SUGGEST_ENTRY = {
  event_type: 'suggest_assignment',
  recommended_option: { therapist_id: 'T1', name: 'Dr. Smith' },
  human_choice: null,
  confidence_score: 0.82,
  risks: ['High caseload'],
  override_reason: null,
  timestamp: '2026-04-06T10:00:00',
};

const OVERRIDE_ENTRY = {
  event_type: 'override',
  recommended_option: { therapist_id: 'T1', name: 'Dr. Smith' },
  human_choice: { therapist_id: 'T2', name: 'Dr. Jones' },
  confidence_score: 0.65,
  risks: [],
  override_reason: 'Preferred therapist',
  timestamp: '2026-04-06T11:00:00',
};

describe('AuditTrail', () => {
  test('shows empty state when no entries', () => {
    render(<AuditTrail entries={[]} />);
    expect(screen.getByText(/no actions/i)).toBeInTheDocument();
  });

  test('renders event_type for each entry', () => {
    render(<AuditTrail entries={[SUGGEST_ENTRY]} />);
    expect(screen.getByText('suggest_assignment')).toBeInTheDocument();
  });

  test('sorts entries by timestamp descending — most recent first', () => {
    const earlier = { ...SUGGEST_ENTRY, timestamp: '2026-04-06T09:00:00', event_type: 'earlier_event' };
    const later = { ...SUGGEST_ENTRY, timestamp: '2026-04-06T12:00:00', event_type: 'later_event' };
    render(<AuditTrail entries={[earlier, later]} />);
    const items = screen.getAllByRole('listitem');
    expect(items[0]).toHaveTextContent('later_event');
    expect(items[1]).toHaveTextContent('earlier_event');
  });

  test('override entry shows override_reason', () => {
    render(<AuditTrail entries={[OVERRIDE_ENTRY]} />);
    expect(screen.getByText(/Preferred therapist/)).toBeInTheDocument();
  });

  test('suggest entry shows confidence_score as percentage', () => {
    render(<AuditTrail entries={[SUGGEST_ENTRY]} />);
    expect(screen.getByText(/82%/)).toBeInTheDocument();
  });

  test('suggest entry shows risk items', () => {
    render(<AuditTrail entries={[SUGGEST_ENTRY]} />);
    expect(screen.getByText(/High caseload/)).toBeInTheDocument();
  });

  test('suggest entry does not show Reason row when override_reason is null', () => {
    render(<AuditTrail entries={[SUGGEST_ENTRY]} />);
    expect(screen.queryByText(/^Reason:/)).not.toBeInTheDocument();
  });

  test('override entry shows recommended and human choice options', () => {
    render(<AuditTrail entries={[OVERRIDE_ENTRY]} />);
    expect(screen.getByText(/Dr\. Smith/)).toBeInTheDocument();
    expect(screen.getByText(/Dr\. Jones/)).toBeInTheDocument();
  });
});
