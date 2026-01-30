# FastAPI HTTP 云函数部署指南

本指南详细介绍如何将 FastAPI 应用部署到 CloudBase HTTP 云函数。

> **📋 前置要求**：如果您还没有创建 FastAPI 项目，请先阅读 [FastAPI 项目创建指南](./project-setup.md)。

## 📋 目录导航

- [准备部署文件](#准备部署文件)
- [项目结构](#项目结构)
- [部署步骤](#部署步骤)
- [访问应用](#访问应用)
- [常见问题](#常见问题)
- [最佳实践](#最佳实践)
- [性能优化](#性能优化)

---

## 准备部署文件

### 1. 创建启动脚本

创建 `scf_bootstrap` 文件（无扩展名）：

```bash
#!/bin/bash
export PORT=9000
export PYTHONPATH="./third_party:$PYTHONPATH"
/var/lang/python310/bin/python3.10 -m uvicorn main:app --host 0.0.0.0 --port 9000
```

为启动脚本添加执行权限：

```bash
chmod +x scf_bootstrap
```

### 2. 优化 main.py

确保 `main.py` 支持云函数环境：

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

### 3. 依赖管理

确保 `requirements.txt` 包含必要依赖：

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic[email]==2.5.0
```

安装依赖到 third_party 目录
pip install -r requirements.txt -t third_party

## 项目结构

```
cloudrun-fastapi/
├── main.py                 # FastAPI 主应用文件
├── requirements.txt        # Python 依赖
├── scf_bootstrap          # 🔑 云函数启动脚本
└── third_party/                   # Python 依赖包
```

> 💡 **说明**：
> - `scf_bootstrap` 是 CloudBase 云函数的启动脚本
> - 设置 `PORT=9000` 环境变量确保应用监听云函数要求的端口
> - 设置 `PYTHONPATH` 环境变量确保应用能找到依赖包
> - 使用云函数运行时环境的 Python 解释器启动应用
> - **重要**：HTTP 云函数部署时需要包含 `third_party` 目录及其依赖包

## 部署步骤

### 通过控制台部署

1. 登录 [CloudBase 控制台](https://console.cloud.tencent.com/tcb)
2. 选择您的环境，进入「云函数」页面
3. 点击「新建云函数」
4. 选择「HTTP 云函数」
5. 填写函数名称（如：`cloudrun-fastapi-app`）
6. 选择运行时：**Python 3.10**（或其他支持的版本）
7. 提交方法选择：**本地上传文件夹**
8. 函数代码选择 `cloudrun-fastapi` 目录进行上传
9. **自动安装依赖**：开启此选项
10. 点击「创建」按钮等待部署完成

### 通过 CLI 部署

```bash
# 安装 CloudBase CLI
npm install -g @cloudbase/cli

# 登录
tcb login

# 部署云函数
tcb functions:deploy cloudrun-fastapi-app --dir ./
```

### 打包部署

如果需要手动打包：

```bash
# 创建部署包（包含 env 目录）
zip -r cloudrun-fastapi-app.zip . -x ".git/*" "*.log" "Dockerfile" ".dockerignore" "__pycache__/*" "env/*"
```

## 访问应用

### 获取访问地址

部署成功后，您可以参考[通过 HTTP 访问云函数](https://docs.cloudbase.net/service/access-cloud-function)设置自定义域名访问 HTTP 云函数。

访问地址格式：`https://your-function-url/`

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
curl https://your-function-url/health

# 获取用户列表
curl https://your-function-url/api/users

# 分页查询
curl "https://your-function-url/api/users?page=1&limit=2"

# 创建新用户
curl -X POST https://your-function-url/api/users \
  -H "Content-Type: application/json" \
  -d '{"name":"测试用户","email":"test@example.com"}'

# 访问 API 文档
# 在浏览器中打开：https://your-function-url/docs
```

## 常见问题

### Q: 如何解决腾讯云函数中的 pydantic_core 错误？

**错误信息**：
```
ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'
```

**根本原因**：
- `pydantic_core` 是 C 扩展模块，在云函数 Linux 环境中可能架构不匹配
- FastAPI 新版本依赖 Pydantic 2.x，而 Pydantic 2.x 依赖 `pydantic_core`

**解决方案**：

#### 方案 A：使用 Pydantic 1.x（推荐）
```txt
# requirements.txt - 云函数兼容版本
fastapi==0.95.2
uvicorn==0.22.0
pydantic==1.10.12
python-multipart==0.0.6
```

#### 方案 B：完全避免 Pydantic
```txt
# requirements-no-pydantic.txt
starlette==0.27.0
uvicorn==0.22.0
orjson==3.9.10
```

#### 方案 C：指定构建平台
```bash
pip install pydantic==1.10.12 --platform linux_x86_64 --only-binary=:all:
```

**详细解决指南**：请参考 [腾讯云函数部署指南](./scf-deployment.md)

### Q: 为什么 HTTP 云函数必须使用 9000 端口？
A: CloudBase HTTP 云函数要求应用监听 9000 端口，这是平台的标准配置。通过在 `scf_bootstrap` 中设置 `PORT=9000` 环境变量来控制端口，本地开发时默认使用 8080 端口。

### Q: FastAPI 自动文档在云函数中能正常访问吗？
A: 是的，FastAPI 的 `/docs` 和 `/redoc` 文档页面在云函数环境中完全可用，这是 FastAPI 的一大优势。

### Q: 如何处理 CORS 跨域问题？
A: 在 FastAPI 应用中添加 CORS 中间件：

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

### Q: 虚拟环境依赖如何处理？
A: HTTP 云函数部署时需要包含 `env` 目录及其依赖包。在 `scf_bootstrap` 中通过 `PYTHONPATH` 环境变量指向虚拟环境的 site-packages 目录。

### Q: 如何查看云函数日志？
A: 在 CloudBase 控制台的云函数页面，点击函数名称进入详情页查看运行日志。

### Q: 云函数支持哪些 Python 版本？
A: CloudBase 支持 Python 3.7、3.8、3.9、3.10、3.11 等版本，建议使用最新的稳定版本。

## 最佳实践

### 1. 环境变量管理

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
```

### 2. 优化启动脚本

增强 `scf_bootstrap` 脚本：

```bash
#!/bin/bash
export PORT=9000
export PYTHONPATH="./env/lib/python3.10/site-packages:$PYTHONPATH"

# 检查依赖
if [ ! -d "env" ]; then
    echo "Virtual environment not found"
    exit 1
fi

# 启动应用
/var/lang/python310/bin/python3.10 -m uvicorn main:app --host 0.0.0.0 --port 9000 --workers 1
```

### 3. 异步数据库连接

```python
from databases import Database
import os

# 异步数据库连接
database = Database(os.getenv("DATABASE_URL", "sqlite:///./test.db"))

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
```

### 4. 请求日志中间件

```python
import time
import logging
from fastapi import Request

logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    return response
```

### 5. 错误处理增强

```python
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "status_code": 500
        }
    )
```

### 6. 部署前检查清单

- [ ] `scf_bootstrap` 文件存在且有执行权限
- [ ] 端口配置为 9000
- [ ] `requirements.txt` 包含所有必需依赖
- [ ] **包含 `env` 目录及其依赖包**
- [ ] 排除不必要的文件（如 `Dockerfile`、`.dockerignore`）
- [ ] 测试本地启动是否正常
- [ ] 检查启动脚本语法是否正确
- [ ] FastAPI 文档路径配置正确

## 性能优化

### 1. 减少冷启动时间

```python
# 全局变量缓存
import os
from functools import lru_cache

@lru_cache(maxsize=1)
def get_app_config():
    return {
        "title": "CloudRun FastAPI 应用",
        "version": "1.0.0",
        "debug": os.getenv("DEBUG", "False").lower() == "true"
    }

app = FastAPI(**get_app_config())
```

### 2. 依赖优化

```bash
# 只安装生产依赖
pip install --no-deps -r requirements.txt

# 清理不必要的文件
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +
```

### 3. 内存管理

```python
import psutil
import logging

logger = logging.getLogger(__name__)

@app.middleware("http")
async def monitor_memory(request: Request, call_next):
    response = await call_next(request)
    
    # 监控内存使用
    process = psutil.Process()
    memory_info = process.memory_info()
    logger.info(f'Memory usage: {memory_info.rss / 1024 / 1024:.2f} MB')
    
    return response
```

### 4. 响应优化

```python
from fastapi.responses import ORJSONResponse

# 使用更快的 JSON 序列化
app = FastAPI(default_response_class=ORJSONResponse)

# 或者为特定路由使用
@app.get("/api/users", response_class=ORJSONResponse)
async def get_users():
    return {"users": users}
```

---

## 相关文档

- [返回主文档](../README.md)
- [云托管部署指南](./cloud-run.md)
- [CloudBase 官方文档](https://docs.cloudbase.net/)