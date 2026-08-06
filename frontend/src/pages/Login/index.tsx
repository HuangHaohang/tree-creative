import {
  ArrowRightOutlined,
  CheckCircleFilled,
  LockOutlined,
  SafetyCertificateOutlined,
} from '@ant-design/icons';
import { Navigate, useLocation, useModel } from '@umijs/max';
import { Alert, Button, Space, Typography } from 'antd';

import { getLoginReturnPath } from '../../features/auth/navigation';
import { beginWpsLogin } from '../../features/auth/services/auth';

import styles from './index.less';

const LoginPage: React.FC = () => {
  const location = useLocation();
  const { initialState } = useModel('@@initialState');
  const returnTo = getLoginReturnPath(location.search);
  const unavailable = initialState?.authenticationStatus === 'unavailable';

  if (initialState?.authenticationStatus === 'authenticated') {
    return <Navigate replace to={returnTo} />;
  }

  return (
    <div className={styles.page}>
      <div className={styles.glowOne} />
      <div className={styles.glowTwo} />
      <main className={styles.shell}>
        <section className={styles.brandPanel} aria-label="Tree Creative 产品介绍">
          <div className={styles.brand}>
            <span className={styles.brandMark} aria-hidden="true">
              <span />
            </span>
            <span>Tree Creative</span>
          </div>

          <div className={styles.brandContent}>
            <Typography.Text className={styles.eyebrow}>CREATIVE INTELLIGENCE</Typography.Text>
            <Typography.Title className={styles.heroTitle} level={1}>
              让创意与数据，
              <br />
              在同一处生长。
            </Typography.Title>
            <Typography.Paragraph className={styles.heroDescription}>
              面向团队的智能内容工作台，连接组织、流程与创意资产。
            </Typography.Paragraph>
          </div>

          <div className={styles.trustList}>
            <span>
              <CheckCircleFilled /> 企业级统一身份认证
            </span>
            <span>
              <CheckCircleFilled /> 服务端安全会话
            </span>
            <span>
              <CheckCircleFilled /> 组织权限集中管理
            </span>
          </div>
        </section>

        <section className={styles.loginPanel} aria-labelledby="login-title">
          <div className={styles.mobileBrand}>
            <span className={styles.brandMark} aria-hidden="true">
              <span />
            </span>
            <span>Tree Creative</span>
          </div>

          <div className={styles.loginBox}>
            <div className={styles.securityIcon} aria-hidden="true">
              <LockOutlined />
            </div>
            <Typography.Title id="login-title" level={2} className={styles.loginTitle}>
              欢迎回来
            </Typography.Title>
            <Typography.Paragraph className={styles.loginDescription}>
              使用企业 WPS 账号登录 Tree Creative
            </Typography.Paragraph>

            {unavailable ? (
              <Alert
                className={styles.alert}
                showIcon
                type="warning"
                message="登录服务暂不可用"
                description="无法确认当前会话，请检查服务后重试。"
              />
            ) : null}

            <Button
              aria-label="使用 WPS 企业账号登录"
              block
              className={styles.loginButton}
              disabled={unavailable}
              icon={<SafetyCertificateOutlined />}
              onClick={() => beginWpsLogin(returnTo)}
              size="large"
              type="primary"
            >
              <Space>
                WPS 企业账号登录
                <ArrowRightOutlined />
              </Space>
            </Button>

            {unavailable ? (
              <Button block className={styles.retryButton} onClick={() => window.location.reload()}>
                重新检测服务
              </Button>
            ) : null}

            <div className={styles.securityNote}>
              <SafetyCertificateOutlined />
              <span>登录由企业统一身份服务安全保护</span>
            </div>
          </div>

          <Typography.Text className={styles.copyright}>
            © 2026 Tree Creative · Enterprise Workspace
          </Typography.Text>
        </section>
      </main>
    </div>
  );
};

export default LoginPage;
