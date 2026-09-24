import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Badge, SeverityBadge } from './badge';

describe('Badge and SeverityBadge components', () => {
  it('renders standard Badge with children', () => {
    render(<Badge tone="ok">Operational</Badge>);
    expect(screen.getByText('Operational')).toBeInTheDocument();
  });

  it('renders SeverityBadge for High severity with text and icon', () => {
    render(<SeverityBadge severity="High" />);
    expect(screen.getByText('High')).toBeInTheDocument();
  });

  it('renders SeverityBadge for Medium severity', () => {
    render(<SeverityBadge severity="Medium" />);
    expect(screen.getByText('Medium')).toBeInTheDocument();
  });

  it('renders SeverityBadge for Low severity', () => {
    render(<SeverityBadge severity="Low" />);
    expect(screen.getByText('Low')).toBeInTheDocument();
  });
});
