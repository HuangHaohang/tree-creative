import { defineConfig } from '@umijs/max';

export default defineConfig({
  antd: {},
  access: {},
  model: {},
  initialState: {},
  request: {},
  layout: {
    title: 'Tree Creative',
    locale: false,
  },
  routes: [
    {
      path: '/login',
      component: './Login',
      layout: false,
    },
    {
      path: '/',
      redirect: '/home',
    },
    {
      name: '首页',
      icon: 'home',
      path: '/home',
      component: './Home',
      wrappers: ['@/features/auth/components/AuthGuard'],
    },
    {
      name: '组织通讯录',
      icon: 'team',
      path: '/organization',
      component: './Organization',
      wrappers: ['@/features/auth/components/AuthGuard'],
    },
  ],
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:8000',
      changeOrigin: true,
    },
  },
  esbuildMinifyIIFE: true,
  title: 'Tree Creative',
  npmClient: 'pnpm',
});
