import { request } from '@umijs/max';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { buildWpsLoginUrl, getCurrentSession, isUnauthorizedError, logout } from './auth';

vi.mock('@umijs/max', () => ({ request: vi.fn() }));

const requestMock = vi.mocked(request);

describe('authentication services', () => {
  beforeEach(() => requestMock.mockReset());

  it('loads the server session without exposing credentials', async () => {
    requestMock.mockResolvedValueOnce({ user: { id: 'user-1' }, csrfToken: 'csrf' });

    await getCurrentSession();

    expect(requestMock).toHaveBeenCalledWith('/api/auth/me', {
      method: 'GET',
      skipErrorHandler: true,
    });
  });

  it('logs out with the session CSRF token', async () => {
    requestMock.mockResolvedValueOnce(undefined);

    await logout('csrf-token');

    expect(requestMock).toHaveBeenCalledWith('/api/auth/logout', {
      method: 'POST',
      headers: { 'X-CSRF-Token': 'csrf-token' },
      skipErrorHandler: true,
    });
  });

  it('recognizes only 401 responses as an expired login', () => {
    expect(isUnauthorizedError({ response: { status: 401 } })).toBe(true);
    expect(isUnauthorizedError({ response: { status: 503 } })).toBe(false);
    expect(isUnauthorizedError(new Error('offline'))).toBe(false);
  });

  it('starts WPS login with only a safe internal return path', () => {
    expect(buildWpsLoginUrl('/organization?departmentId=product')).toBe(
      '/api/auth/wps/login?returnTo=%2Forganization%3FdepartmentId%3Dproduct',
    );
  });
});
