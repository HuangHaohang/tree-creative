export interface CurrentUser {
  id: string;
  displayName: string;
  avatarUrl?: string;
  organizationName?: string;
  title?: string;
  employeeId?: string;
  status: string;
  permissions: string[];
}

export type AuthenticationStatus = 'authenticated' | 'unauthenticated' | 'unavailable';

export interface AppInitialState {
  currentUser: CurrentUser | null;
  csrfToken: string | null;
  authenticationStatus: AuthenticationStatus;
}
