import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import LoginPage from './index';

const beginWpsLoginMock = vi.fn();
const useModelMock = vi.fn();

vi.mock('@umijs/max', () => ({
  Navigate: ({ to }: { to: string }) => <span data-testid="redirect">{to}</span>,
  useLocation: () => ({ search: '?returnTo=%2Forganization' }),
  useModel: () => useModelMock(),
}));

vi.mock('../../features/auth/services/auth', () => ({
  beginWpsLogin: (returnTo: string) => beginWpsLoginMock(returnTo),
}));

describe('LoginPage', () => {
  beforeEach(() => {
    beginWpsLoginMock.mockReset();
    useModelMock.mockReturnValue({
      initialState: { authenticationStatus: 'unauthenticated' },
    });
  });

  it('shows a dedicated WPS login entry and keeps the requested route', () => {
    render(<LoginPage />);

    fireEvent.click(screen.getByRole('button', { name: '使用 WPS 企业账号登录' }));

    expect(screen.getByRole('heading', { name: '欢迎回来' })).toBeInTheDocument();
    expect(beginWpsLoginMock).toHaveBeenCalledWith('/organization');
  });

  it('redirects an existing session away from the login page', () => {
    useModelMock.mockReturnValue({
      initialState: { authenticationStatus: 'authenticated' },
    });

    render(<LoginPage />);

    expect(screen.getByTestId('redirect')).toHaveTextContent('/organization');
  });
});
