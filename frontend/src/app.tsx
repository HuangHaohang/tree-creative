import type { RequestConfig, RunTimeLayoutConfig } from '@umijs/max';
import { history } from '@umijs/max';

import AppSiderFooter from '@/components/AppSiderFooter';
import AuthSessionBoundary from '@/features/auth/components/AuthSessionBoundary';
import { notifyAuthenticationRequired } from '@/features/auth/events';
import {
  beginWpsLogin,
  getCurrentSession,
  isUnauthorizedError,
  logout,
} from '@/features/auth/services/auth';
import '@/styles/layout.less';
import type { AppInitialState } from '@/types/auth';

export async function getInitialState(): Promise<AppInitialState> {
  try {
    const session = await getCurrentSession();
    return {
      currentUser: session.user,
      csrfToken: session.csrfToken,
      authenticationStatus: 'authenticated',
    };
  } catch (error) {
    if (isUnauthorizedError(error)) {
      return {
        currentUser: null,
        csrfToken: null,
        authenticationStatus: 'unauthenticated',
      };
    }
    return {
      currentUser: null,
      csrfToken: null,
      authenticationStatus: 'unavailable',
    };
  }
}

export const layout: RunTimeLayoutConfig = ({ initialState, setInitialState }) => ({
  title: 'Tree Creative',
  pure: initialState?.authenticationStatus !== 'authenticated',
  menu: { locale: false },
  layout: 'side',
  navTheme: 'light',
  siderWidth: 252,
  headerRender: false,
  rightContentRender: false,
  menuFooterRender: (props) => (
    <AppSiderFooter
      collapsed={props?.collapsed}
      currentUser={initialState?.currentUser ?? null}
      onLogin={beginWpsLogin}
      onLogout={async () => {
        if (!initialState?.csrfToken) return;
        await logout(initialState.csrfToken);
        await setInitialState?.({
          currentUser: null,
          csrfToken: null,
          authenticationStatus: 'unauthenticated',
        });
        history.replace('/login');
      }}
    />
  ),
  childrenRender: (children) =>
    setInitialState ? (
      <AuthSessionBoundary setInitialState={setInitialState}>{children}</AuthSessionBoundary>
    ) : (
      children
    ),
});

export const request: RequestConfig = {
  timeout: 15_000,
  responseInterceptors: [
    [
      (response) => response,
      (error: unknown) => {
        if ((error as { response?: { status?: number } }).response?.status === 401) {
          notifyAuthenticationRequired();
        }
        return Promise.reject(error);
      },
    ],
  ],
};
