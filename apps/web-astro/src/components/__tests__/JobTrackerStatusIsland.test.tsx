import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';

import { JobTrackerStatusIsland } from '../JobTrackerStatusIsland';

describe('JobTrackerStatusIsland', () => {
  it('renders the initial connection status', () => {
    render(<JobTrackerStatusIsland />);

    expect(screen.getByRole('heading', { name: 'Verbindungsstatus & Event-Replay' })).toBeInTheDocument();
    expect(screen.getByText('Aktueller Status: Offline')).toBeInTheDocument();
  });
});
