import { history } from '@umijs/max';
import { useEffect } from 'react';

import { AUTHENTICATION_REQUIRED_EVENT } from '../events';
import { buildLoginPath } from '../navigation';
import type { AppInitialState } from '@/types/auth';

interface AuthSessionBoundaryProps {
  children: React.ReactNode;
  setInitialState: (state: AppInitialState) => Promise<void>;
}

export default function AuthSessionBoundary({
  children,
  setInitialState,
}: AuthSessionBoundaryProps) {
  useEffect(() => {
    const handleAuthenticationRequired = () => {
      void setInitialState({
        currentUser: null,
        csrfToken: null,
        authenticationStatus: 'unauthenticated',
      });
      history.replace(buildLoginPath(history.location));
    };
    window.addEventListener(AUTHENTICATION_REQUIRED_EVENT, handleAuthenticationRequired);
    return () => {
      window.removeEventListener(AUTHENTICATION_REQUIRED_EVENT, handleAuthenticationRequired);
    };
  }, [setInitialState]);

  return <>{children}</>;
}
