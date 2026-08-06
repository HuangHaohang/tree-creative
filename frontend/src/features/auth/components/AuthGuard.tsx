import { Navigate, useLocation, useModel } from '@umijs/max';

import { buildLoginPath } from '../navigation';

interface AuthGuardProps {
  children: React.ReactNode;
}

export default function AuthGuard({ children }: AuthGuardProps) {
  const location = useLocation();
  const { initialState } = useModel('@@initialState');

  if (initialState?.authenticationStatus === 'authenticated') {
    return <>{children}</>;
  }

  return <Navigate replace to={buildLoginPath(location)} />;
}
