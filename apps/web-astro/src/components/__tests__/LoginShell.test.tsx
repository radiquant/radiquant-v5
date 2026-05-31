import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';

import { LoginShell } from '../LoginShell';

describe('LoginShell', () => {
  it('renders the login shell heading', () => {
    render(<LoginShell />);

    expect(screen.getByRole('heading', { name: 'Sicher anmelden' })).toBeInTheDocument();
  });
});
