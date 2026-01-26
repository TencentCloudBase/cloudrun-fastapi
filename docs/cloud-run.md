# FastAPI 云托管部署指南

本指南详细介绍如何将 FastAPI 应用部署到 CloudBase 云托管服务。

> **📋 前置要求**：如果您还没有创建 FastAPI 项目，请先阅读 [FastAPI 项目创建指南](./project-setup.md)。

## 📋 目录导航

- [部署特性](#部署特性)
- [准备部署文件](#准备部署文件)
- [项目结构](#项目结构)
- [部署步骤](#部署步骤)
- [访问应用](#访问应用)
- [常见问题](#常见问题)
- [最佳实践](#最佳实践)
- [高级配置](#高级配置)

---

## 部署特性

云托管适合以下场景：

- **企业级应用**：复杂的 API 服务和管理系统
- **高并发**：需要处理大量并发请求
- **自定义环境**：需要特定的运行时环境
- **微服务架构**：容器化部署和管理

### 技术特点

| 特性 | 说明 |
|------|------|
| **计费方式** | 按资源使用量（CPU/内存） |
| **启动方式** | 持续运行 |
| **端口配置** | 可自定义端口（默认 8080） |
| **扩缩容** | 支持自动扩缩容配置 |
| **Python 环境** | 完全自定义 Python 环境 |

## 准备部署文件

### 1. 创建 Dockerfile

创建 `Dockerfile` 文件：

```dockerfile
# 使用官方 Python 运行时作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 设置 pip 镜像源以提高下载速度
RUN pip config set global.index-url https://mirrors.cloud.tencent.com/pypi/simple/ \
    && pip config set global.trusted-host mirrors.cloud.tencent.com

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8080

# 设置环境变量
ENV PORT=8080
ENV PYTHONPATH=/app

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 2. 创建 .dockerignore 文件

创建 `.dockerignore` 文件以优化构建性能：

```
env/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
.git
.gitignore
README.md
.env
.DS_Store
*.log
.pytest_cache/
.coverage
scf_bootstrap
.vscode/
.idea/
docs/
```

### 3. 优化 main.py

确保 `main.py` 支持云托管环境：

```python
import os
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import sys

# 创建 FastAPI 应用实例
app = FastAPI(
    title="CloudRun FastAPI 应用",
    description="一个部署在 CloudBase 上的 FastAPI 示例应用",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ... 其他代码保持不变 ...

if __name__ == "__main__":
    # 默认端口 8080，HTTP 云函数通过环境变量设置为 9000
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

### 4. 依赖管理

确保 `requirements.txt` 包含所有必要依赖：

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic[email]==2.5.0
python-dotenv>=1.0.0
```

## 项目结构

```
cloudrun-fastapi/
├── main.py                 # FastAPI 主应用文件
├── requirements.txt        # Python 依赖
├── Dockerfile              # 🔑 容器配置文件
├── .dockerignore           # Docker 忽略文件
└── .gitignore             # Git 忽略文件
```

> 💡 **说明**：
> - 云托管支持自定义端口，默认使用 8080 端口
> - 使用 uvicorn ASGI 服务器启动应用
> - Docker 容器提供了完整的 Python 环境控制

## 部署步骤

### 通过控制台部署

1. 登录 [CloudBase 控制台](https://console.cloud.tencent.com/tcb)
2. 选择您的环境，进入「云托管」页面
3. 点击「新建服务」
4. 填写服务名称（如：`cloudrun-fastapi-service`）
5. 选择「本地代码」上传方式
6. 上传包含 `Dockerfile` 的项目目录
7. 配置服务参数：
   - **端口**：8080（或您在应用中配置的端口）
   - **CPU**：0.25 核
   - **内存**：0.5 GB
   - **实例数量**：1-10（根据需求调整）
8. 点击「创建」按钮等待部署完成

### 通过 CLI 部署

```bash
# 安装 CloudBase CLI
npm install -g @cloudbase/cli

# 登录
tcb login

# 初始化云托管配置
tcb run init

# 部署云托管服务
tcb run deploy --port 8080
```

### 配置文件部署

创建 `cloudbaserc.json` 配置文件：

```json
{
  "envId": "your-env-id",
  "framework": {
    "name": "fastapi",
    "plugins": {
      "run": {
        "name": "@cloudbase/framework-plugin-run",
        "options": {
          "serviceName": "cloudrun-fastapi-service",
          "servicePath": "/",
          "localPath": "./",
          "dockerfile": "./Dockerfile",
          "buildDir": "./",
          "cpu": 0.25,
          "mem": 0.5,
          "minNum": 1,
          "maxNum": 10,
          "policyType": "cpu",
          "policyThreshold": 60,
          "containerPort": 8080,
          "envVariables": {
            "DEBUG": "False"
          }
        }
      }
    }
  }
}
```

然后执行部署：

```bash
tcb framework deploy
```

### 模板部署（快速开始）

1. 登录 [腾讯云托管控制台](https://tcb.cloud.tencent.com/dev#/platform-run/service/create?type=image)
2. 点击「通过模板部署」，选择 **FastAPI 模板**
3. 输入自定义服务名称，点击部署
4. 等待部署完成后，点击左上角箭头，返回到服务详情页
5. 点击概述，获取默认域名并访问

## 访问应用

### 获取访问地址

云托管部署成功后，系统会自动分配访问地址。您也可以绑定自定义域名。

访问地址格式：`https://your-service-url/`

### 测试接口

- **根路径**：`/` - FastAPI 欢迎页面
- **健康检查**：`/health` - 查看应用状态
- **API 文档**：`/docs` - Swagger UI 文档
- **ReDoc 文档**：`/redoc` - ReDoc 风格文档
- **用户列表**：`/api/users` - 获取用户列表
- **用户详情**：`/api/users/1` - 获取特定用户
- **创建用户**：`POST /api/users` - 创建新用户
- **更新用户**：`PUT /api/users/1` - 更新用户信息
- **删除用户**：`DELETE /api/users/1` - 删除用户

### 示例请求

```bash
# 健康检查
curl https://your-service-url/health

# 获取用户列表
curl https://your-service-url/api/users

# 分页查询
curl "https://your-service-url/api/users?page=1&limit=2"

# 创建新用户
curl -X POST https://your-service-url/api/users \
  -H "Content-Type: application/json" \
  -d '{"name":"测试用户","email":"test@example.com"}'

# 访问 API 文档
# 在浏览器中打开：https://your-service-url/docs
```

## 常见问题

### Q: 云托管支持哪些端口？
A: 云托管支持自定义端口，FastAPI 应用默认使用 8080 端口，也可以根据需要配置其他端口。

### Q: 如何配置生产环境设置？
A: 通过环境变量控制应用配置：

```python
# main.py
import os
from functools import lru_cache

class Settings:
    app_name: str = "CloudRun FastAPI"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    port: int = int(os.getenv("PORT", 8080))

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    debug=settings.debug
)
```

### Q: 如何配置环境变量？
A: 可以通过以下方式配置：
- 控制台服务配置页面
- `cloudbaserc.json` 配置文件
- Dockerfile 中的 ENV 指令

### Q: FastAPI 自动文档在云托管中能正常访问吗？
A: 是的，FastAPI 的 `/docs` 和 `/redoc` 文档页面在云托管环境中完全可用。

### Q: 如何查看云托管日志？
A: 在云托管服务详情页面可以查看：
- 实例日志
- 构建日志
- 访问日志
- 错误日志

## 最佳实践

### 1. 多阶段构建优化

```dockerfile
# 构建阶段
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# 运行阶段
FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

# 确保 Python 用户包在 PATH 中
ENV PATH=/root/.local/bin:$PATH

EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 2. 使用 Gunicorn 生产服务器

```dockerfile
# Dockerfile 中使用 Gunicorn
CMD ["gunicorn", "main:app", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080"]
```

```python
# gunicorn.conf.py
bind = "0.0.0.0:8080"
workers = 2
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
```

### 3. 环境变量管理

```python
# config.py
import os
from functools import lru_cache
from pydantic import BaseSettings

class Settings(BaseSettings):
    app_name: str = "CloudRun FastAPI"
    debug: bool = False
    port: int = 8080
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
```

### 4. 健康检查增强

```python
# main.py
import sys
import os
from fastapi import FastAPI

@app.get("/health")
async def health_check():
    """增强的健康检查接口"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "framework": "FastAPI",
        "deployment": "云托管",
        "version": "0.104.0",
        "python_version": sys.version,
        "environment": os.environ.get("ENV", "production")
    }
```

### 5. 日志配置

```python
# logging_config.py
import logging
import sys

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

# main.py
from logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    return response
```

### 6. CORS 配置

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该设置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 7. 部署前检查清单

- [ ] `Dockerfile` 文件存在且配置正确
- [ ] `.dockerignore` 文件配置合理
- [ ] 端口配置灵活（支持环境变量）
- [ ] 容器启动命令正确
- [ ] **排除 `env` 目录**（云托管使用 Docker 容器内的 Python 环境）
- [ ] **排除 `scf_bootstrap` 文件**（仅用于云函数）
- [ ] 本地 Docker 构建测试通过
- [ ] API 文档路径配置正确

## 高级配置

### 1. 负载均衡配置

```json
{
  "run": {
    "name": "@cloudbase/framework-plugin-run",
    "options": {
      "serviceName": "cloudrun-fastapi-service",
      "cpu": 1,
      "mem": 2,
      "minNum": 2,
      "maxNum": 20,
      "policyType": "cpu",
      "policyThreshold": 70,
      "containerPort": 8080,
      "customLogs": "stdout",
      "initialDelaySeconds": 2
    }
  }
}
```

### 2. 数据库集成

```python
# database.py
from databases import Database
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
database = Database(DATABASE_URL)

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
```

### 3. Redis 缓存配置

```python
# cache.py
import aioredis
import os

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
redis = aioredis.from_url(redis_url)

@app.on_event("startup")
async def startup():
    global redis
    redis = aioredis.from_url(redis_url)

@app.on_event("shutdown")
async def shutdown():
    await redis.close()
```

### 4. 监控和告警

```python
# middleware.py
import time
import logging
from fastapi import Request

logger = logging.getLogger(__name__)

@app.middleware("http")
async def monitor_performance(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # 记录慢请求
    if process_time > 1.0:
        logger.warning(f"Slow request: {request.method} {request.url.path} - {process_time:.3f}s")
    
    return response
```

---

## 相关文档

- [返回主文档](../README.md)
- [HTTP 云函数部署指南](./http-function.md)
- [CloudBase 官方文档](https://docs.cloudbase.net/)