import type { AppInitialState } from '@/types/auth';

export default (initialState: AppInitialState | undefined) => {
  const permissions = new Set(initialState?.currentUser?.permissions ?? []);

  return {
    isAuthenticated: Boolean(initialState?.currentUser),
    canManagePlatform: permissions.has('platform:manage'),
  };
};
