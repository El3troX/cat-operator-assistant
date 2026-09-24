import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import BandBadge from './BandBadge';

describe('BandBadge component', () => {
  it('renders Good band badge', () => {
    render(<BandBadge band="Good" />);
    expect(screen.getByText('Good')).toBeInTheDocument();
  });

  it('renders Watch band badge', () => {
    render(<BandBadge band="Watch" />);
    expect(screen.getByText('Watch')).toBeInTheDocument();
  });

  it('renders At risk band badge', () => {
    render(<BandBadge band="At risk" />);
    expect(screen.getByText('At risk')).toBeInTheDocument();
  });
});
