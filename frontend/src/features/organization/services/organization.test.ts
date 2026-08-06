import { request } from '@umijs/max';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  getOrganizationMembers,
  getOrganizationTree,
  searchOrganizationMembers,
} from './organization';

vi.mock('@umijs/max', () => ({ request: vi.fn() }));

const requestMock = vi.mocked(request);

describe('organization services', () => {
  beforeEach(() => requestMock.mockReset());

  it('loads the masked organization tree', async () => {
    requestMock.mockResolvedValueOnce({ tree: { id: 'root' } });

    await getOrganizationTree();

    expect(requestMock).toHaveBeenCalledWith('/api/organization/tree', {
      method: 'GET',
      skipErrorHandler: true,
    });
  });

  it('filters and searches personnel through the server', async () => {
    requestMock.mockResolvedValue({ items: [], page: { pageSize: 20, hasMore: false } });

    await getOrganizationMembers({ departmentId: 'dept-1', pageSize: 20 });
    await searchOrganizationMembers('张', { departmentId: 'dept-1' });

    expect(requestMock).toHaveBeenNthCalledWith(1, '/api/organization/members', {
      method: 'GET',
      params: { departmentId: 'dept-1', pageSize: 20 },
      skipErrorHandler: true,
    });
    expect(requestMock).toHaveBeenNthCalledWith(2, '/api/organization/members/search', {
      method: 'GET',
      params: { departmentId: 'dept-1', keyword: '张' },
      skipErrorHandler: true,
    });
  });
});
