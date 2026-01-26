# FastAPI 项目创建指南

本指南详细介绍如何从零开始创建一个适用于 CloudBase 部署的 FastAPI 项目。

## 📋 目录导航

- [环境准备](#环境准备)
- [创建项目](#创建项目)
- [基础配置](#基础配置)
- [创建应用](#创建应用)
- [数据模型](#数据模型)
- [安装依赖](#安装依赖)
- [本地测试](#本地测试)
- [下一步](#下一步)

---

## 环境准备

### 1. 检查 Python 版本

```bash
# 检查 Python 版本（推荐 3.8+）
python --version
# 或
python3 --version
```

### 2. 创建项目目录

```bash
# 创建项目根目录
mkdir cloudrun-fastapi && cd cloudrun-fastapi

# 创建虚拟环境
python -m venv env

# 激活虚拟环境
# Windows
env\Scripts\activate
# macOS/Linux
source env/bin/activate
```

## 创建项目

### 1. 安装 FastAPI

```bash
# 安装 FastAPI 和相关依赖
pip install fastapi
pip install uvicorn[standard]
pip install pydantic[email]

# 验证安装
python -c "import fastapi; print(fastapi.__version__)"
```

### 2. 创建主应用文件

创建 `main.py` 文件：

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

# 数据模型
class User(BaseModel):
    id: Optional[int] = None
    name: str
    email: EmailStr

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

class UserResponse(BaseModel):
    success: bool
    data: Optional[User] = None
    message: Optional[str] = None

class UsersResponse(BaseModel):
    success: bool
    data: Optional[dict] = None

# 模拟数据
users = [
    {"id": 1, "name": "张三", "email": "zhangsan@example.com"},
    {"id": 2, "name": "李四", "email": "lisi@example.com"},
    {"id": 3, "name": "王五", "email": "wangwu@example.com"}
]

@app.get("/")
async def hello():
    """根路径处理函数"""
    return {
        "message": "Hello from FastAPI on CloudBase!",
        "framework": "FastAPI",
        "version": "0.104.0"
    }

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "framework": "FastAPI",
        "python_version": sys.version
    }

@app.get("/api/users", response_model=UsersResponse)
async def get_users(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(10, ge=1, le=100, description="每页数量")
):
    """获取用户列表（支持分页）"""
    start_index = (page - 1) * limit
    end_index = start_index + limit
    paginated_users = users[start_index:end_index]
    
    return UsersResponse(
        success=True,
        data={
            "total": len(users),
            "page": page,
            "limit": limit,
            "items": paginated_users
        }
    )

@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """根据 ID 获取用户"""
    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(success=True, data=User(**user))

@app.post("/api/users", response_model=UserResponse, status_code=201)
async def create_user(user: User):
    """创建新用户"""
    # 检查邮箱是否已存在
    if any(u["email"] == user.email for u in users):
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # 创建新用户
    new_user = {
        "id": max(u["id"] for u in users) + 1 if users else 1,
        "name": user.name,
        "email": user.email
    }
    users.append(new_user)
    
    return UserResponse(success=True, data=User(**new_user))

@app.put("/api/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_update: UserUpdate):
    """更新用户信息"""
    user_index = next((i for i, u in enumerate(users) if u["id"] == user_id), None)
    if user_index is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 检查邮箱是否被其他用户使用
    if user_update.email and any(u["email"] == user_update.email and u["id"] != user_id for u in users):
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # 更新用户信息
    if user_update.name is not None:
        users[user_index]["name"] = user_update.name
    if user_update.email is not None:
        users[user_index]["email"] = user_update.email
    
    return UserResponse(success=True, data=User(**users[user_index]))

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int):
    """删除用户"""
    user_index = next((i for i, u in enumerate(users) if u["id"] == user_id), None)
    if user_index is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    deleted_user = users.pop(user_index)
    return {
        "success": True,
        "message": f"User {deleted_user['name']} deleted successfully"
    }

# 错误处理
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"success": False, "message": "Resource not found"}

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"success": False, "message": "Internal server error"}

if __name__ == "__main__":
    # 默认端口 8080，HTTP 云函数通过环境变量设置为 9000
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

## 基础配置

### 1. 项目结构

```
cloudrun-fastapi/
├── main.py                 # 主应用文件
├── requirements.txt        # Python 依赖
├── .gitignore             # Git 忽略文件
└── env/                   # 虚拟环境
```

### 2. 环境变量配置

FastAPI 应用支持通过环境变量进行配置：

```bash
# 设置端口（可选）
export PORT=8080

# 设置调试模式（可选）
export DEBUG=true
```

## 创建应用

### 1. API 接口说明

FastAPI 自动生成 API 文档，包含以下接口：

- **根路径**：`GET /` - 应用欢迎信息
- **健康检查**：`GET /health` - 应用健康状态
- **用户列表**：`GET /api/users` - 获取用户列表（支持分页）
- **用户详情**：`GET /api/users/{user_id}` - 获取特定用户
- **创建用户**：`POST /api/users` - 创建新用户
- **更新用户**：`PUT /api/users/{user_id}` - 更新用户信息
- **删除用户**：`DELETE /api/users/{user_id}` - 删除用户

### 2. 自动文档

FastAPI 提供自动生成的 API 文档：

- **Swagger UI**：`/docs` - 交互式 API 文档
- **ReDoc**：`/redoc` - 另一种风格的 API 文档

## 数据模型

### 1. Pydantic 模型

FastAPI 使用 Pydantic 进行数据验证和序列化：

```python
from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    id: Optional[int] = None
    name: str
    email: EmailStr

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
```

### 2. 数据验证

Pydantic 自动处理：
- 类型验证
- 邮箱格式验证
- 必填字段检查
- 数据序列化

## 安装依赖

### 1. 基础依赖

```bash
# 安装基础依赖（与项目 requirements.txt 一致）
pip install fastapi==0.104.1
pip install uvicorn[standard]==0.24.0
pip install pydantic[email]==2.5.0

# 生产服务器（可选）
pip install gunicorn
```

### 2. 生成依赖文件

```bash
# 生成 requirements.txt
pip freeze > requirements.txt

# 查看生成的依赖（应该包含以下内容）
cat requirements.txt
# fastapi==0.104.1
# uvicorn==0.24.0
# pydantic==2.5.0
# pydantic-core==2.14.5
# email-validator==2.1.0
```

### 3. 创建 .gitignore

```bash
cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# 虚拟环境
env/
venv/
.venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# 操作系统
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# 环境变量
.env
.env.local
.env.production

# 部署文件
deployment.zip
*.tar.gz

# CloudBase
.cloudbaserc.json
cloudbaserc.json
EOF
```

## 本地测试

### 1. 启动开发服务器

```bash
# 使用 uvicorn 启动开发服务器
uvicorn main:app --host 0.0.0.0 --port 8080 --reload

# 或者直接运行 main.py
python main.py

# 服务器启动后，访问以下地址测试：
# http://127.0.0.1:8080/          - 首页
# http://127.0.0.1:8080/health    - 健康检查
# http://127.0.0.1:8080/docs      - Swagger API 文档
# http://127.0.0.1:8080/redoc     - ReDoc API 文档
```

### 2. API 测试

```bash
# 测试基础接口
curl http://127.0.0.1:8080/
# 返回: {"message": "Hello from FastAPI on CloudBase!", "framework": "FastAPI", "version": "0.104.0"}

curl http://127.0.0.1:8080/health
# 返回: {"status": "healthy", "framework": "FastAPI", "python_version": "..."}

# 测试用户 API
# 获取用户列表
curl http://127.0.0.1:8080/api/users
curl "http://127.0.0.1:8080/api/users?page=1&limit=2"

# 创建用户
curl -X POST http://127.0.0.1:8080/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "测试用户", "email": "test@example.com"}'

# 获取单个用户
curl http://127.0.0.1:8080/api/users/1

# 更新用户
curl -X PUT http://127.0.0.1:8080/api/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "更新用户", "email": "updated@example.com"}'

# 删除用户
curl -X DELETE http://127.0.0.1:8080/api/users/1
```

### 3. 交互式测试

访问 `http://127.0.0.1:8080/docs` 使用 Swagger UI 进行交互式 API 测试。

## 下一步

项目创建完成后，根据您的部署需求选择相应的部署指南：

### 🚀 部署选择

| 部署方式 | 适用场景 | 详细指南 |
|----------|----------|----------|
| **HTTP 云函数** | 轻量级 API、间歇性访问 | [HTTP 云函数部署指南](./http-function.md) |
| **云托管** | 企业应用、高并发、持续运行 | [云托管部署指南](./cloud-run.md) |

### 📚 相关文档

- [返回主文档](../README.md)
- [HTTP 云函数部署指南](./http-function.md)
- [云托管部署指南](./cloud-run.md)

### 🔧 进一步开发

1. **数据库集成**：集成 SQLAlchemy 或 Tortoise ORM
2. **用户认证**：添加 JWT 认证系统
3. **API 版本控制**：实现 API 版本管理
4. **中间件**：添加日志、CORS、限流等中间件
5. **测试**：使用 pytest 编写单元测试和集成测试

---

**提示**：FastAPI 提供了出色的自动文档生成和类型检查功能，确保在开发过程中充分利用这些特性。