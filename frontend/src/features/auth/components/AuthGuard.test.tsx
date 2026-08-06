import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import AuthGuard from './AuthGuard';

const useModelMock = vi.fn();
const useLocationMock = vi.fn();

vi.mock('@umijs/max', () => ({
  Navigate: ({ to }: { to: string }) => <span data-testid="redirect">{to}</span>,
  useLocation: () => useLocationMock(),
  useModel: () => useModelMock(),
}));

describe('AuthGuard', () => {
  beforeEach(() => {
    useLocationMock.mockReturnValue({ pathname: '/organization', search: '', hash: '' });
  });

  it('renders protected content only for an authenticated user', () => {
    useModelMock.mockReturnValue({
      initialState: { authenticationStatus: 'authenticated' },
    });

    render(<AuthGuard>protected content</AuthGuard>);

    expect(screen.getByText('protected content')).toBeInTheDocument();
    expect(screen.queryByTestId('redirect')).not.toBeInTheDocument();
  });

  it('redirects an unauthenticated visitor to the standalone login page', () => {
    useModelMock.mockReturnValue({
      initialState: { authenticationStatus: 'unauthenticated' },
    });

    render(<AuthGuard>protected content</AuthGuard>);

    expect(screen.queryByText('protected content')).not.toBeInTheDocument();
    expect(screen.getByTestId('redirect')).toHaveTextContent('/login?returnTo=%2Forganization');
  });
});
