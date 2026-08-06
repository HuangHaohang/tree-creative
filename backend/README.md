# Tree Creative Backend

FastAPI application with explicit API, core, infrastructure, business-module, and worker boundaries.

```bash
uv sync
uv run uvicorn tree_creative_api.main:app --reload
```

OpenAPI is available at `http://127.0.0.1:8000/docs` in non-production environments.

## WPS SSO

WPS 登录由后端与 SSO 网关交互，浏览器只持有随机的 `HttpOnly` 会话 Cookie。WPS token envelope 仅存在 Redis 服务端会话中。

需要的运行时配置见根目录 `.env.example`，其中 `WPS_GATEWAY_CLIENT_SECRET` 必须通过服务端密钥管理或环境变量注入。

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/api/auth/wps/login` | 创建单次 state 并跳转 WPS |
| POST | `/api/oauth/callback` | 校验回调并创建服务端会话 |
| GET | `/api/auth/me` | 获取当前用户和 CSRF token |
| POST | `/api/auth/logout` | 撤销 Redis 会话并清除 Cookie |
| GET | `/api/organization/tree` | 获取脱敏部门树 |
| GET | `/api/organization/members` | 分页获取人员 |
| GET | `/api/organization/members/search` | 搜索人员 |
