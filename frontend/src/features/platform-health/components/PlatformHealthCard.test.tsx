import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import PlatformHealthCard from './PlatformHealthCard';

describe('PlatformHealthCard', () => {
  it('renders service and dependency health', () => {
    render(
      <PlatformHealthCard
        loading={false}
        onRefresh={vi.fn()}
        health={{
          service: 'tree-creative-api',
          version: '0.1.0',
          status: 'ok',
          dependencies: { mysql: 'ok', redis: 'ok', minio: 'ok' },
        }}
      />,
    );

    expect(screen.getByText('tree-creative-api')).toBeInTheDocument();
    expect(screen.getAllByText('ok')).toHaveLength(4);
  });
});
