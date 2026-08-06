# Tree Creative Frontend

Umi Max、React、Ant Design Pro 前端应用。

从仓库根目录执行：

```bash
pnpm install
pnpm dev
```

开发服务默认通过 Umi 代理访问 `http://127.0.0.1:8000/api`。

前端通过 `/api/auth/me` 恢复服务端会话，不保存 WPS 凭据。所有业务路由均由认证守卫保护；未登录、会话过期或无法确认会话时只显示独立登录页，WPS SSO 成功后安全返回登录前的站内页面。组织通讯录页提供部门树、人员筛选和搜索。
