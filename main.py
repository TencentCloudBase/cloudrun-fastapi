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
