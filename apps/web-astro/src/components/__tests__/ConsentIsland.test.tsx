import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';

import { ConsentIsland } from '../ConsentIsland';

describe('ConsentIsland', () => {
  it('renders the consent form controls', () => {
    render(<ConsentIsland clientId="client-1" token="" tenantId="" />);

    expect(screen.getByRole('heading', { name: 'Consent dokumentieren und prüfen' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Consent dokumentieren' })).toBeInTheDocument();
  });
});
