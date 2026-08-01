import type { RequestConfig, RunTimeLayoutConfig } from '@umijs/max';

import type { AppInitialState } from '@/types/auth';

export async function getInitialState(): Promise<AppInitialState> {
  return { currentUser: null };
}

export const layout: RunTimeLayoutConfig = ({ initialState }) => ({
  title: 'Tree Creative',
  menu: { locale: false },
  avatarProps: initialState?.currentUser
    ? { title: initialState.currentUser.displayName }
    : undefined,
  layout: 'mix',
  splitMenus: false,
});

export const request: RequestConfig = {
  timeout: 15_000,
};
