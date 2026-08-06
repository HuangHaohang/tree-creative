interface RouteLocation {
  pathname: string;
  search?: string;
  hash?: string;
}

export const DEFAULT_AUTHENTICATED_PATH = '/home';
export const LOGIN_PATH = '/login';

export function normalizeReturnPath(value: string | null | undefined): string {
  if (
    !value ||
    !value.startsWith('/') ||
    value.startsWith('//') ||
    value.includes('\\') ||
    value.split('').some((character) => character.charCodeAt(0) < 32)
  ) {
    return DEFAULT_AUTHENTICATED_PATH;
  }

  try {
    const parsed = new URL(value, window.location.origin);
    if (parsed.origin !== window.location.origin || parsed.pathname === LOGIN_PATH) {
      return DEFAULT_AUTHENTICATED_PATH;
    }
  } catch {
    return DEFAULT_AUTHENTICATED_PATH;
  }

  return value;
}

export function currentRoutePath(location: RouteLocation): string {
  return `${location.pathname}${location.search ?? ''}${location.hash ?? ''}`;
}

export function buildLoginPath(location: RouteLocation): string {
  const returnTo = normalizeReturnPath(currentRoutePath(location));
  return `${LOGIN_PATH}?returnTo=${encodeURIComponent(returnTo)}`;
}

export function getLoginReturnPath(search: string): string {
  return normalizeReturnPath(new URLSearchParams(search).get('returnTo'));
}
