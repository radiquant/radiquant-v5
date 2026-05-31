import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';

import { ClientListIsland } from '../ClientListIsland';

describe('ClientListIsland', () => {
  it('renders the initial empty client state', () => {
    render(<ClientListIsland />);

    expect(screen.getByText('Noch keine Klienten geladen.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Klienten laden' })).toBeInTheDocument();
  });
});
