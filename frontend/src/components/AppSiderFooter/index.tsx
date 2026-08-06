import { LoginOutlined, LogoutOutlined, UserOutlined } from '@ant-design/icons';
import { Avatar, Button, Tooltip } from 'antd';
import { useState } from 'react';

import type { CurrentUser } from '@/types/auth';

import styles from './index.less';

interface AppSiderFooterProps {
  collapsed?: boolean;
  currentUser: CurrentUser | null;
  onLogin: () => void;
  onLogout: () => Promise<void>;
}

const FALLBACK_USER_NAME = '访客用户';
const FALLBACK_ORGANIZATION = '用户信息待接入';

export default function AppSiderFooter({
  collapsed = false,
  currentUser,
  onLogin,
  onLogout,
}: AppSiderFooterProps) {
  const [loggingOut, setLoggingOut] = useState(false);
  const authenticated = currentUser !== null;
  const actionLabel = authenticated ? '退出登录' : 'WPS 登录';
  const displayName = currentUser?.displayName ?? FALLBACK_USER_NAME;
  const organizationName = currentUser?.organizationName ?? FALLBACK_ORGANIZATION;
  const footerClassName = collapsed ? `${styles.footer} ${styles.collapsed}` : styles.footer;

  const handleAction = async () => {
    if (!authenticated) {
      onLogin();
      return;
    }
    setLoggingOut(true);
    try {
      await onLogout();
    } finally {
      setLoggingOut(false);
    }
  };

  return (
    <div className={footerClassName} data-testid="app-sider-footer">
      <Tooltip placement="right" title={collapsed ? actionLabel : undefined}>
        <Button
          aria-label={actionLabel}
          className={styles.logoutButton}
          icon={authenticated ? <LogoutOutlined /> : <LoginOutlined />}
          loading={loggingOut}
          onClick={() => void handleAction()}
          type="text"
        >
          {collapsed ? null : actionLabel}
        </Button>
      </Tooltip>

      <Tooltip
        placement="right"
        title={collapsed ? `${displayName} · ${organizationName}` : undefined}
      >
        <div className={styles.profile} aria-label={`${displayName}，${organizationName}`}>
          <Avatar
            className={styles.avatar}
            icon={currentUser?.avatarUrl ? undefined : <UserOutlined />}
            size={34}
            src={currentUser?.avatarUrl}
          />
          {collapsed ? null : (
            <div className={styles.profileMeta}>
              <span className={styles.userName}>{displayName}</span>
              <span className={styles.organizationName}>{organizationName}</span>
            </div>
          )}
        </div>
      </Tooltip>
    </div>
  );
}
