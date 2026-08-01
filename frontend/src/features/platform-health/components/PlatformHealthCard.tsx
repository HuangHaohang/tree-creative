import { CheckCircleOutlined, ReloadOutlined, WarningOutlined } from '@ant-design/icons';
import { Button, Card, Descriptions, Empty, Tag } from 'antd';

import type { DependencyStatus, ReadinessResponse } from '../types';

interface PlatformHealthCardProps {
  health?: ReadinessResponse;
  loading: boolean;
  onRefresh: () => void;
}

const statusColor: Record<DependencyStatus, string> = {
  ok: 'success',
  degraded: 'warning',
  unavailable: 'error',
};

const statusIcon = (status: ReadinessResponse['status']) =>
  status === 'ok' ? <CheckCircleOutlined /> : <WarningOutlined />;

const PlatformHealthCard: React.FC<PlatformHealthCardProps> = ({ health, loading, onRefresh }) => (
  <Card
    title="平台健康状态"
    loading={loading && !health}
    extra={
      <Button type="text" icon={<ReloadOutlined />} onClick={onRefresh} loading={loading}>
        刷新
      </Button>
    }
  >
    {health ? (
      <Descriptions column={1} size="small">
        <Descriptions.Item label="服务">{health.service}</Descriptions.Item>
        <Descriptions.Item label="版本">{health.version}</Descriptions.Item>
        <Descriptions.Item label="状态">
          <Tag
            icon={statusIcon(health.status)}
            color={health.status === 'ok' ? 'success' : 'warning'}
          >
            {health.status}
          </Tag>
        </Descriptions.Item>
        {Object.entries(health.dependencies).map(([name, status]) => (
          <Descriptions.Item label={name} key={name}>
            <Tag color={statusColor[status]}>{status}</Tag>
          </Descriptions.Item>
        ))}
      </Descriptions>
    ) : (
      <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无健康状态" />
    )}
  </Card>
);

export default PlatformHealthCard;
