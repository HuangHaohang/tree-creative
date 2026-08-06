import { describe, expect, it } from 'vitest';

import { buildLoginPath, getLoginReturnPath, normalizeReturnPath } from './navigation';

describe('authentication navigation', () => {
  it('preserves an internal route while building the login URL', () => {
    expect(buildLoginPath({ pathname: '/organization', search: '?departmentId=product' })).toBe(
      '/login?returnTo=%2Forganization%3FdepartmentId%3Dproduct',
    );
  });

  it('accepts only internal non-login return paths', () => {
    expect(normalizeReturnPath('/organization')).toBe('/organization');
    expect(normalizeReturnPath('https://evil.example.test')).toBe('/home');
    expect(normalizeReturnPath('//evil.example.test')).toBe('/home');
    expect(normalizeReturnPath('/\\evil.example.test')).toBe('/home');
    expect(normalizeReturnPath('/login')).toBe('/home');
  });

  it('reads a safe return path from the login query', () => {
    expect(getLoginReturnPath('?returnTo=%2Forganization')).toBe('/organization');
  });
});
