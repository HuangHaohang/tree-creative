export type DependencyStatus = 'ok' | 'degraded' | 'unavailable';

export interface ReadinessResponse {
  service: string;
  status: 'ok' | 'degraded';
  version: string;
  dependencies: Record<string, DependencyStatus>;
}
