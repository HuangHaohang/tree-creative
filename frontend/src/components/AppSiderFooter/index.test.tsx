import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import AppSiderFooter from './index';

const currentUser = {
  id: 'user-1',
  displayName: '黄浩航',
  organizationName: 'Tree Creative',
  status: 'active',
  permissions: [],
};

describe('AppSiderFooter', () => {
  it('renders logout and user details when expanded', async () => {
    const onLogout = vi.fn(async () => undefined);

    render(<AppSiderFooter currentUser={currentUser} onLogin={vi.fn()} onLogout={onLogout} />);

    expect(screen.getByText('黄浩航')).toBeInTheDocument();
    expect(screen.getByText('Tree Creative')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: '退出登录' }));
    await waitFor(() => expect(onLogout).toHaveBeenCalledOnce());
  });

  it('keeps icon actions accessible when collapsed', () => {
    render(
      <AppSiderFooter
        collapsed
        currentUser={currentUser}
        onLogin={vi.fn()}
        onLogout={vi.fn(async () => undefined)}
      />,
    );

    expect(screen.queryByText('黄浩航')).not.toBeInTheDocument();
    expect(screen.queryByText('Tree Creative')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: '退出登录' })).toBeInTheDocument();
    expect(screen.getByLabelText('黄浩航，Tree Creative')).toBeInTheDocument();
  });

  it('starts WPS login for an unauthenticated visitor', () => {
    const onLogin = vi.fn();

    render(
      <AppSiderFooter
        currentUser={null}
        onLogin={onLogin}
        onLogout={vi.fn(async () => undefined)}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'WPS 登录' }));
    expect(onLogin).toHaveBeenCalledOnce();
  });
});
