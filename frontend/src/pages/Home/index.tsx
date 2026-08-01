import PlatformHealthCard from '@/features/platform-health/components/PlatformHealthCard';
import { getReadiness } from '@/features/platform-health/services/health';
import { PageContainer } from '@ant-design/pro-components';
import { useRequest } from '@umijs/max';
import { Alert, Card, Col, Row, Space, Tag, Typography } from 'antd';
import styles from './index.less';

const HomePage: React.FC = () => {
  const { data, error, loading, refresh } = useRequest<
    Awaited<ReturnType<typeof getReadiness>>,
    [],
    Awaited<ReturnType<typeof getReadiness>>,
    Awaited<ReturnType<typeof getReadiness>>
  >(getReadiness, {
    pollingInterval: 30_000,
    formatResult: (health) => health,
  });

  return (
    <PageContainer
      header={{
        title: 'Tree Creative',
        subTitle: 'Production-grade application foundation',
      }}
    >
      <Space direction="vertical" size="large" className={styles.container}>
        {error ? (
          <Alert
            type="warning"
            showIcon
            message="后端暂不可达"
            description="前端已正常运行；启动后端或 Docker Compose 后可恢复健康检查。"
          />
        ) : null}

        <Row gutter={[16, 16]}>
          <Col xs={24} xl={12}>
            <PlatformHealthCard health={data} loading={loading} onRefresh={refresh} />
          </Col>
          <Col xs={24} xl={12}>
            <Card title="工程基线" className={styles.card}>
              <Space direction="vertical" size="middle">
                <Typography.Text>
                  前后端分治、模块化设计、自动化验证与容器化交付已纳入基础框架。
                </Typography.Text>
                <Space wrap>
                  <Tag color="blue">Umi Max</Tag>
                  <Tag color="cyan">React</Tag>
                  <Tag color="purple">Ant Design Pro</Tag>
                  <Tag color="geekblue">FastAPI</Tag>
                  <Tag color="red">Redis Workers</Tag>
                </Space>
              </Space>
            </Card>
          </Col>
        </Row>
      </Space>
    </PageContainer>
  );
};

export default HomePage;
