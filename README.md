# 快速部署 FastAPI MySQL 应用

一个完整的 FastAPI + MySQL 应用模板，支持快速部署到 CloudBase 平台。

## 📚 文档导航

| 文档 | 描述 | 适用场景 |
|------|------|----------|
| [项目创建指南](./docs/project-setup.md) | 从零开始创建 FastAPI 项目的详细步骤 | 新手入门、项目初始化 |
| [HTTP 云函数部署](./docs/http-function.md) | 部署到 CloudBase HTTP 云函数的完整指南 | 轻量级 API、按需计费 |
| [云托管部署](./docs/cloud-run.md) | 部署到 CloudBase 云托管的完整指南 | 企业应用、持续运行 |
| [腾讯云函数专用指南](./docs/scf-deployment.md) | 解决云函数环境中 pydantic_core 问题 | 云函数部署故障排除 |

### 🎯 快速选择指南

- **🆕 新手开发者** → 先看 [项目创建指南](./docs/project-setup.md)
- **☁️ 轻量级部署** → 使用 [HTTP 云函数部署](./docs/http-function.md)
- **🏢 企业级部署** → 使用 [云托管部署](./docs/cloud-run.md)
- **🔧 遇到部署问题** → 查看 [腾讯云函数专用指南](./docs/scf-deployment.md)

## 🚀 快速开始

### 前置条件

- [Python 3.8](https://www.python.org/downloads/) 或更高版本
- MySQL 5.7+ 或 MariaDB 10.3+
- 了解基本的 Python 虚拟环境使用
- 腾讯云账号并开通了 CloudBase 服务
- 基本的 Python 和 FastAPI 开发知识

### 创建应用

```bash
# 快速创建（基础步骤）
mkdir cloudrun-fastapi && cd cloudrun-fastapi
python -m venv env
source env/bin/activate  # Windows: env\Scripts\activate
pip install fastapi==0.104.1 uvicorn==0.24.0 aiomysql==0.2.0 PyMySQL==1.1.0
```

### 数据库设置

1. **创建数据库**：
```bash
# 连接到 MySQL
mysql -u root -p

# 执行初始化脚本
source init_db.sql
```

2. **配置环境变量**：
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，设置数据库连接信息
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=fastapi_demo
```

### 本地测试

```bash
# 启动开发服务器
python main.py
# 或者使用 uvicorn
uvicorn main:app --host 0.0.0.0 --port 8080 --reload

# 访问应用
open http://localhost:8080
# API 文档
open http://localhost:8080/docs
```

## 📦 项目结构

```
cloudrun-fastapi/
├── main.py                  # FastAPI 主应用文件（MySQL 版本）
├── requirements.txt         # Python 依赖文件（云函数兼容版本）
├── requirements-no-pydantic.txt # 无 Pydantic 依赖版本
├── init_db.sql             # 数据库初始化脚本
├── .env.example            # 环境变量模板
├── .gitignore              # Git 忽略文件
├── docs/                   # 📚 详细文档目录
│   ├── project-setup.md    # 项目创建指南
│   ├── http-function.md    # HTTP 云函数部署指南
│   ├── cloud-run.md        # 云托管部署指南
│   └── scf-deployment.md   # 腾讯云函数专用指南
├── third_party/            # Python 依赖安装目录，HTTP 云函数必须将依赖一同打包，并不会自己下载依赖
├── scf_bootstrap           # HTTP 云函数启动脚本
├── Dockerfile              # 云托管容器配置
└── .dockerignore           # Docker 忽略文件
```

## 🎯 部署方式

### 部署方式对比

| 特性 | HTTP 云函数 | 云托管 |
|------|------------|--------|
| **计费方式** | 按请求次数和执行时间 | 按资源使用量（CPU/内存） |
| **启动方式** | 冷启动，按需启动 | 持续运行 |
| **适用场景** | API 服务、轻量级应用 | 企业级应用、复杂 Web 应用 |
| **端口要求** | 固定 9000 端口 | 可自定义端口（默认 8080） |
| **扩缩容** | 自动按请求扩缩 | 支持自动扩缩容配置 |
| **Python 环境** | 预配置 Python 运行时 | 完全自定义 Python 环境 |

### 选择部署方式

- **选择 HTTP 云函数**：轻量级 API 服务、间歇性访问、成本敏感
- **选择云托管**：企业级应用、复杂 Web 应用、需要更多控制权

## 📚 详细部署指南

> **💡 提示**：以下是快速概览，详细步骤请查看对应的专门文档。

### 🔥 HTTP 云函数部署

适合轻量级应用和 API 服务，按请求计费，冷启动快。

**特点**：
- ✅ 按请求次数计费，成本低
- ✅ 自动扩缩容，无需管理服务器
- ✅ 冷启动快，适合间歇性访问
- ⚠️ 固定使用 9000 端口

**📖 完整指南**：[HTTP 云函数部署文档](./docs/http-function.md)

**快速部署**：
```bash
# 1. 创建启动脚本
echo '#!/bin/bash
export PORT=9000
export PYTHONPATH="./third_party:$PYTHONPATH"
/var/lang/python310/bin/python3.10 main.py' > scf_bootstrap

# 2. 安装依赖到 third_party 目录
pip install -r requirements.txt -t third_party

# 3. 打包上传到 CloudBase 控制台
```

### 🐳 云托管部署

适合企业级应用，支持更复杂的部署需求，容器化部署。

**特点**：
- ✅ 持续运行，适合企业级应用
- ✅ 完全自定义环境和端口
- ✅ 支持复杂的依赖和配置
- ⚠️ 按资源使用量计费

**📖 完整指南**：[云托管部署文档](./docs/cloud-run.md)

**快速部署**：
```bash
# 1. 构建镜像
docker build -t fastapi-app .

# 2. 推送到 CloudBase 镜像仓库
# 3. 通过控制台或 CLI 部署
```

### 🔧 故障排除

遇到部署问题？查看专门的故障排除文档：

- **pydantic_core 错误** → [腾讯云函数专用指南](./docs/scf-deployment.md)
- **项目创建问题** → [项目创建指南](./docs/project-setup.md)
- **其他部署问题** → 查看对应的部署文档

## 🔧 API 接口

本模板包含以下 RESTful API 接口：

### 基础接口
```bash
GET /                        # 欢迎页面
GET /health                  # 健康检查
GET /docs                    # Swagger API 文档
GET /redoc                   # ReDoc API 文档
```

### 用户管理
```bash
GET /api/users               # 获取用户列表（支持分页）
GET /api/users/{user_id}     # 获取单个用户
POST /api/users              # 创建用户
PUT /api/users/{user_id}     # 更新用户
DELETE /api/users/{user_id}  # 删除用户
```

### 示例请求

```bash
# 健康检查
curl https://your-app-url/health

# 获取用户列表（分页）
curl "https://your-app-url/api/users?page=1&limit=5"

# 创建新用户
curl -X POST https://your-app-url/api/users \
  -H "Content-Type: application/json" \
  -d '{"name":"测试用户","email":"test@example.com"}'

# 更新用户
curl -X PUT https://your-app-url/api/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"更新用户","email":"updated@example.com"}'

# 删除用户
curl -X DELETE https://your-app-url/api/users/1
```

## ❓ 常见问题

### 🚨 部署相关问题

**Q: 遇到 pydantic_core 模块错误怎么办？**
A: 这是腾讯云函数环境的常见问题，查看 [腾讯云函数专用指南](./docs/scf-deployment.md) 获取详细解决方案。

**Q: 如何选择部署方式？**
A: 
- **轻量级 API** → [HTTP 云函数部署](./docs/http-function.md)
- **企业级应用** → [云托管部署](./docs/cloud-run.md)
- **新手入门** → [项目创建指南](./docs/project-setup.md)

### ⚙️ 配置相关

**端口配置**：
- **HTTP 云函数**：必须使用 9000 端口
- **云托管**：推荐使用 8080 端口，支持自定义

**文件要求**：
- **HTTP 云函数**：需要 `scf_bootstrap` 启动脚本和 `env` 目录
- **云托管**：需要 `Dockerfile` 和 `.dockerignore`

### 💾 数据库相关

**MySQL 连接**：
- 本项目支持 MySQL 数据库集成
- 数据库连接失败时自动降级为内存存储
- 详细配置请查看各部署文档

**环境变量配置**：
```bash
DB_HOST=your_mysql_host
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_NAME=fastapi_demo
```

### 📖 更多帮助

如需更详细的帮助，请查看：
- [项目创建指南](./docs/project-setup.md) - 完整的项目创建流程
- [HTTP 云函数部署](./docs/http-function.md) - 云函数部署详细步骤
- [云托管部署](./docs/cloud-run.md) - 云托管部署详细步骤
- [腾讯云函数专用指南](./docs/scf-deployment.md) - 云函数故障排除

## 🛠️ 开发工具

### 推荐的开发依赖

```bash
# 核心框架
pip install fastapi==0.128.0 uvicorn==0.40.0

# 数据验证
pip install pydantic==2.12.5 email-validator==2.3.0

# 数据库支持
pip install sqlalchemy psycopg2-binary

# 环境变量
pip install python-dotenv==1.2.1

# 文件上传
pip install python-multipart==0.0.22
```

### 环境变量配置

创建 `.env` 文件：

```env
# 应用配置
DEBUG=True
PORT=8080

# 数据库配置（可选）
DATABASE_URL=postgresql://user:password@localhost/dbname

# API 配置
API_TITLE=CloudRun FastAPI 应用
API_VERSION=1.0.0
```

## 📖 进阶功能

- **自动 API 文档**：Swagger UI 和 ReDoc 支持
- **数据验证**：Pydantic 模型自动验证
- **异步支持**：原生异步 I/O 支持
- **类型提示**：完整的 Python 类型提示
- **中间件支持**：CORS、认证、日志等中间件
- **WebSocket 支持**：实时通信功能

## 🔗 相关链接

### 📚 项目文档
- [项目创建指南](./docs/project-setup.md) - 从零开始创建 FastAPI 项目
- [HTTP 云函数部署](./docs/http-function.md) - 轻量级云函数部署方案
- [云托管部署](./docs/cloud-run.md) - 企业级容器化部署方案
- [腾讯云函数专用指南](./docs/scf-deployment.md) - 云函数环境故障排除

### 🌐 官方文档
- [CloudBase 官方文档](https://docs.cloudbase.net/)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Python 官方文档](https://docs.python.org/)

## 📄 许可证

本项目采用 MIT 许可证。详情请查看 [LICENSE](./LICENSE) 文件。

---

**需要帮助？** 

- 🆕 **新手入门** → [项目创建指南](./docs/project-setup.md)
- ☁️ **云函数部署** → [HTTP 云函数部署](./docs/http-function.md)
- 🐳 **容器部署** → [云托管部署](./docs/cloud-run.md)
- 🔧 **故障排除** → [腾讯云函数专用指南](./docs/scf-deployment.md)
- 📖 **API 文档** → 访问 `/docs` 或 `/redoc` 路径