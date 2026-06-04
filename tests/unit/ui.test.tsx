import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ProgressBar, StatusBadge } from '../../src/components/ui';

describe('shared UI components', () => {
  it('renders a localized status badge for task state', () => {
    render(<StatusBadge status="queued" />);

    expect(screen.getByText('排队')).toBeInTheDocument();
  });

  it('clamps progress bar width to the valid range', () => {
    render(<ProgressBar value={140} />);

    expect(screen.getByLabelText('进度 140%').querySelector('span')).toHaveStyle({ width: '100%' });
  });
});
