import { request } from '@umijs/max';

import type { MembersQuery, OrganizationMembersResponse, OrganizationTreeResponse } from '../types';

export async function getOrganizationTree(): Promise<OrganizationTreeResponse> {
  return request<OrganizationTreeResponse>('/api/organization/tree', {
    method: 'GET',
    skipErrorHandler: true,
  });
}

export async function getOrganizationMembers(
  params: MembersQuery = {},
): Promise<OrganizationMembersResponse> {
  return request<OrganizationMembersResponse>('/api/organization/members', {
    method: 'GET',
    params,
    skipErrorHandler: true,
  });
}

export async function searchOrganizationMembers(
  keyword: string,
  params: MembersQuery = {},
): Promise<OrganizationMembersResponse> {
  return request<OrganizationMembersResponse>('/api/organization/members/search', {
    method: 'GET',
    params: { ...params, keyword },
    skipErrorHandler: true,
  });
}
