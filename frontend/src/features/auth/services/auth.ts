import { request } from '@umijs/max';

import type { CurrentUser } from '@/types/auth';
import { normalizeReturnPath } from '../navigation';

interface CurrentUserResponse {
  user: CurrentUser;
  csrfToken: string;
}

export async function getCurrentSession(): Promise<CurrentUserResponse> {
  return request<CurrentUserResponse>('/api/auth/me', {
    method: 'GET',
    skipErrorHandler: true,
  });
}

export async function logout(csrfToken: string): Promise<void> {
  await request('/api/auth/logout', {
    method: 'POST',
    headers: { 'X-CSRF-Token': csrfToken },
    skipErrorHandler: true,
  });
}

export function buildWpsLoginUrl(returnTo = '/home'): string {
  const query = new URLSearchParams({ returnTo: normalizeReturnPath(returnTo) });
  return `/api/auth/wps/login?${query.toString()}`;
}

export function beginWpsLogin(returnTo = '/home'): void {
  window.location.assign(buildWpsLoginUrl(returnTo));
}

export function isUnauthorizedError(error: unknown): boolean {
  return (
    typeof error === 'object' &&
    error !== null &&
    'response' in error &&
    (error as { response?: { status?: number } }).response?.status === 401
  );
}
