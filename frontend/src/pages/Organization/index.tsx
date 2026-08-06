import { ApartmentOutlined, SearchOutlined, UserOutlined } from '@ant-design/icons';
import { PageContainer } from '@ant-design/pro-components';
import { useModel } from '@umijs/max';
import {
  Alert,
  Avatar,
  Button,
  Card,
  Col,
  Empty,
  Input,
  List,
  Row,
  Space,
  Spin,
  Tag,
  Tree,
  Typography,
} from 'antd';
import type { DataNode } from 'antd/es/tree';
import { useCallback, useEffect, useMemo, useState } from 'react';

import {
  getOrganizationMembers,
  getOrganizationTree,
  searchOrganizationMembers,
} from '@/features/organization/services/organization';
import type {
  DepartmentNode,
  DirectoryMember,
  OrganizationMembersResponse,
  OrganizationTreeResponse,
} from '@/features/organization/types';

import styles from './index.less';

function toTreeData(node: DepartmentNode): DataNode {
  return {
    key: node.id,
    title: (
      <Space size={6}>
        <span>{node.name}</span>
        {node.users.length > 0 ? (
          <Typography.Text type="secondary">{node.users.length}</Typography.Text>
        ) : null}
      </Space>
    ),
    children: node.children.map(toTreeData),
  };
}

const OrganizationPage: React.FC = () => {
  const { initialState } = useModel('@@initialState');
  const [tree, setTree] = useState<OrganizationTreeResponse>();
  const [members, setMembers] = useState<OrganizationMembersResponse>();
  const [selectedDepartmentId, setSelectedDepartmentId] = useState<string>();
  const [keyword, setKeyword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>();

  const loadMembers = useCallback(
    async (searchKeyword = '', cursor?: string, departmentId?: string) => {
      setLoading(true);
      setError(undefined);
      try {
        const params = {
          departmentId,
          includeSubdepartments: true,
          pageSize: 50,
          cursor,
        };
        const result = searchKeyword
          ? await searchOrganizationMembers(searchKeyword, params)
          : await getOrganizationMembers(params);
        setMembers((current) =>
          cursor && current ? { ...result, items: [...current.items, ...result.items] } : result,
        );
      } catch {
        setError('人员数据加载失败，请稍后重试。');
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    if (initialState?.authenticationStatus !== 'authenticated') return;
    let active = true;
    setLoading(true);
    setError(undefined);
    void Promise.all([getOrganizationTree(), getOrganizationMembers({ pageSize: 50 })])
      .then(([treeResult, membersResult]) => {
        if (!active) return;
        setTree(treeResult);
        setMembers(membersResult);
      })
      .catch(() => {
        if (active) setError('组织通讯录加载失败，请稍后重试。');
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [initialState?.authenticationStatus]);

  useEffect(() => {
    if (initialState?.authenticationStatus === 'authenticated' && selectedDepartmentId) {
      void loadMembers('', undefined, selectedDepartmentId);
    }
  }, [initialState?.authenticationStatus, loadMembers, selectedDepartmentId]);

  const treeData = useMemo(() => (tree ? [toTreeData(tree.tree)] : []), [tree]);

  const renderMember = (member: DirectoryMember) => (
    <List.Item key={member.id}>
      <List.Item.Meta
        avatar={
          <Avatar src={member.avatarUrl} icon={member.avatarUrl ? undefined : <UserOutlined />} />
        }
        title={
          <Space>
            <span>{member.displayName}</span>
            {member.enabled && !member.departed ? <Tag color="green">在职</Tag> : <Tag>停用</Tag>}
          </Space>
        }
        description={
          (member.primaryDepartment?.name ??
            member.departments.map((item) => item.name).join(' / ')) ||
          '未分配部门'
        }
      />
    </List.Item>
  );

  return (
    <PageContainer
      header={{
        title: '组织通讯录',
        subTitle: tree ? `共 ${tree.users.total} 人` : undefined,
      }}
    >
      <Space direction="vertical" size="middle" className={styles.container}>
        {error ? <Alert showIcon type="error" message={error} /> : null}
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={8} xl={7}>
            <Card
              title={
                <Space>
                  <ApartmentOutlined />
                  部门
                </Space>
              }
              className={styles.panel}
            >
              <Spin spinning={loading && !tree}>
                {treeData.length > 0 ? (
                  <Tree
                    blockNode
                    defaultExpandAll
                    selectedKeys={selectedDepartmentId ? [selectedDepartmentId] : []}
                    treeData={treeData}
                    onSelect={(keys) => {
                      setKeyword('');
                      const departmentId = keys[0]?.toString();
                      setSelectedDepartmentId(departmentId);
                      if (!departmentId) void loadMembers();
                    }}
                  />
                ) : (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无部门" />
                )}
              </Spin>
            </Card>
          </Col>
          <Col xs={24} lg={16} xl={17}>
            <Card
              className={styles.panel}
              title="人员"
              extra={
                <Input.Search
                  allowClear
                  value={keyword}
                  prefix={<SearchOutlined />}
                  placeholder="搜索姓名"
                  onChange={(event) => setKeyword(event.target.value)}
                  onSearch={(value) =>
                    void loadMembers(value.trim(), undefined, selectedDepartmentId)
                  }
                  className={styles.search}
                />
              }
            >
              <List
                dataSource={members?.items ?? []}
                loading={loading}
                locale={{ emptyText: '暂无人员' }}
                renderItem={renderMember}
                footer={
                  members?.page.hasMore ? (
                    <div className={styles.loadMore}>
                      <Button
                        onClick={() =>
                          void loadMembers(
                            keyword.trim(),
                            members.page.nextCursor,
                            selectedDepartmentId,
                          )
                        }
                      >
                        加载更多
                      </Button>
                    </div>
                  ) : null
                }
              />
            </Card>
          </Col>
        </Row>
      </Space>
    </PageContainer>
  );
};

export default OrganizationPage;
