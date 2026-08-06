export const AUTHENTICATION_REQUIRED_EVENT = 'tree-creative:authentication-required';

export function notifyAuthenticationRequired(): void {
  window.dispatchEvent(new Event(AUTHENTICATION_REQUIRED_EVENT));
}
