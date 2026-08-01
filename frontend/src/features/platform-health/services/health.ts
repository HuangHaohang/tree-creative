import { request } from '@umijs/max';

import type { ReadinessResponse } from '../types';

export async function getReadiness(): Promise<ReadinessResponse> {
  return request<ReadinessResponse>('/api/v1/health/ready', {
    method: 'GET',
    skipErrorHandler: true,
  });
}
