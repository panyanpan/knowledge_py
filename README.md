# 知识库管理系统

全栈知识库管理项目。技术栈：Vue 3 + TypeScript + Element Plus / FastAPI + SQLAlchemy / MySQL 8.0。

## 目录结构

```
├── backend/          # FastAPI 后端
│   ├── app/
│   │   ├── api/        # 路由（阶段二起填充）
│   │   ├── core/       # config.py 配置、database.py 连接
│   │   ├── models/     # ORM 模型（阶段二起填充）
│   │   ├── schemas/    # Pydantic 模型（阶段二起填充）
│   │   ├── services/   # 业务逻辑（阶段二起填充）
│   │   └── utils/      # 工具（阶段二起填充）
│   ├── scripts/        # check_db.py 连通性验证 / run_schema.py 执行建表
│   ├── main.py         # FastAPI 入口
│   ├── .env            # 环境变量（不入库）
│   └── requirements.txt
├── frontend/         # Vue 3 + Vite 前端
│   └── src/
└── sql/
    └── schema.sql     # 建表脚本（含初始数据）
```

## 启动步骤

### 1. 数据库初始化

库 `zwfw_zsk` 需已存在（首次执行可用有权限账号创建）：

```bash
cd backend
python -m venv venv
./venv/Scripts/pip install -r requirements.txt   # Windows Git Bash；Linux/macOS 用 venv/bin/pip
./venv/Scripts/python scripts/run_schema.py      # 执行 sql/schema.sql 建表 + 初始数据
```

### 2. 后端启动（http://127.0.0.1:8000，Swagger: /docs）

```bash
cd backend
./venv/Scripts/python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### 3. 前端启动（http://localhost:5173，已代理 /api → 后端 8000）

```bash
cd frontend
npm install
npm run dev
```

## 已实现模块

| 模块 | 说明 |
|---|---|
| 用户认证 | 注册 / 登录(JWT) / 刷新(旋转) / 登出 / RBAC，Swagger 可测 |
| 知识库管理 | 分类树(多级) / 条目 CRUD / 标签 / 附件上传下载 / 关键词搜索 / 可见性权限 |
| 知识门户 | `/portal` 匿名首页：轮播图 / 公告栏 / 最新 / 热门排行 / 分类导航 / 搜索入口 + 搜索结果页 `/portal/search` + 公开详情页 `/portal/entries/:id` |
| 知识元数据 | `/metadata` 元数据字段定义管理：统计卡 / 域与状态筛选 / 搜索 / CRUD / 校验规则检查 / CSV 导出（写操作仅 ADMIN） |
| 知识管理 | `/knowledge` 政务知识管理：类型分布筛选 / 多条件检索 / 详情抽屉 / 新增编辑(富文本) / 发布下架（业务码 25xx） |
| 知识规则管理 | `/rules` 知识质量规则：规则清单(类型/状态筛选) / 新增编辑 / 启用停用 / 试运行（业务码 26xx，写操作仅 ADMIN） |
| 知识服务市场 | `/services` 服务卡片市场：类型/状态筛选 / 卡片网格 / 申请调用(演示回执) / 接口文档抽屉 / 新增编辑上下架（业务码 27xx，写操作仅 ADMIN） |
| 知识溯源 | `/traces` 知识全生命周期溯源：统计条 / 快捷主题与关键词溯源 / 元数据条 / 横向溯源链路(节点联动明细) / 环节明细与存证凭证(演示) / 查询留痕（业务码 28xx，只读） |
| 公告管理 | 管理员维护公告/轮播图（发布/下线/排序/删除），门户即时生效 |
| 前端框架 | 登录 / 注册 / 主布局 / 路由守卫 / Axios 自动携带 token 与 401 自动刷新 |

## 核心接口一览（详见 Swagger /docs）

- 认证：`/api/v1/auth/*`（register / login / refresh / logout / me）
- 分类：`/api/v1/categories`（树 / CRUD）
- 标签：`/api/v1/tags`
- 条目：`/api/v1/entries`（CRUD / 搜索 / 分页）
- 知识：`/api/v1/knowledge`（选项 / 统计 / 列表 / 详情 / CRUD / 发布下架）
- 规则：`/api/v1/rules`（列表 / CRUD / 启停 / 试运行）
- 服务：`/api/v1/services`（选项 / 统计 / 列表 / CRUD / 上下架 / 申请调用演示）
- 溯源：`/api/v1/traces`（统计 / 快捷选项 / 检索 / 详情 / 溯源查询留痕，环节凭证随详情返回）
- 附件：`/api/v1/attachments`（上传 / 下载 / 删除）
- 门户（匿名）：`/api/v1/portal/home`、`/api/v1/portal/entries`、`/api/v1/portal/entries/{id}`
- 公告（ADMIN）：`/api/v1/announcements`（CRUD）
- 元数据：`/api/v1/metadata`（options / stats / fields CRUD / check-rule / export；写操作 ADMIN）

## 环境变量

复制 `backend/.env.example` 为 `backend/.env`，填入 `DB_HOST / DB_PORT / DB_USER / DB_PASSWORD / DB_NAME` 与 JWT 密钥。

## 初始账号

- 用户名 `admin` （bcrypt 存储，首次登录后请修改）
- 角色种子：1=ADMIN、2=USER

## 数据库环境

- MySQL 8.0.42（远程），字符集 utf8mb4，引擎 InnoDB
- 9 张表：sys_role、sys_user、kb_category、kb_entry、kb_tag、kb_entry_tag、kb_attachment、sys_announcement、kb_metadata_field
- 元数据表单独执行：`./venv/Scripts/python scripts/run_metadata.py`（幂等，含 12 条种子字段）
