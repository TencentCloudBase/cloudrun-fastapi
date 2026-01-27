import os
import uvicorn
import aiomysql
import asyncio
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import json

# 创建 FastAPI 应用实例
app = FastAPI(
    title="CloudRun FastAPI MySQL 应用",
    description="一个使用 MySQL 数据库的 FastAPI 示例应用（云函数兼容版）",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 数据模型（使用 Pydantic 1.x 兼容语法）
class User(BaseModel):
    id: Optional[int] = None
    name: str
    email: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

class UserResponse(BaseModel):
    success: bool
    data: Optional[User] = None
    message: Optional[str] = None

class UsersResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None

# MySQL 数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'db': os.getenv('DB_NAME', 'fastapi_demo'),
    'charset': 'utf8mb4'
}

# 全局数据库连接池
db_pool = None

async def init_db():
    """初始化数据库连接池"""
    global db_pool
    try:
        db_pool = await aiomysql.create_pool(**DB_CONFIG)
        
        # 创建用户表
        async with db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                """)
                
                # 插入示例数据（如果表为空）
                await cursor.execute("SELECT COUNT(*) FROM users")
                count = await cursor.fetchone()
                if count[0] == 0:
                    sample_users = [
                        ("张三", "zhangsan@example.com"),
                        ("李四", "lisi@example.com"),
                        ("王五", "wangwu@example.com")
                    ]
                    await cursor.executemany(
                        "INSERT INTO users (name, email) VALUES (%s, %s)",
                        sample_users
                    )
                await conn.commit()
                
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        # 如果数据库连接失败，使用内存数据
        global fallback_users
        fallback_users = [
            {"id": 1, "name": "张三", "email": "zhangsan@example.com"},
            {"id": 2, "name": "李四", "email": "lisi@example.com"},
            {"id": 3, "name": "王五", "email": "wangwu@example.com"}
        ]

async def close_db():
    """关闭数据库连接池"""
    global db_pool
    if db_pool:
        db_pool.close()
        await db_pool.wait_closed()

# 启动和关闭事件
@app.on_event("startup")
async def startup_event():
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    await close_db()

# 数据库操作函数
async def get_db_connection():
    """获取数据库连接"""
    if db_pool:
        return await db_pool.acquire()
    return None

def validate_user_data(data: Dict[str, Any]) -> Dict[str, str]:
    """验证用户数据"""
    errors = {}
    
    if 'name' in data:
        if not data['name'] or not isinstance(data['name'], str):
            errors['name'] = "姓名不能为空且必须是字符串"
        elif len(data['name']) > 100:
            errors['name'] = "姓名长度不能超过100个字符"
    
    if 'email' in data:
        if not data['email'] or not isinstance(data['email'], str):
            errors['email'] = "邮箱不能为空且必须是字符串"
        elif '@' not in data['email'] or len(data['email']) > 255:
            errors['email'] = "邮箱格式不正确或长度超过255个字符"
    
    return errors

@app.get("/")
async def hello():
    """根路径处理函数"""
    return {
        "message": "Hello from FastAPI with MySQL on CloudBase!",
        "framework": "FastAPI",
        "database": "MySQL",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """健康检查接口"""
    db_status = "connected" if db_pool else "disconnected"
    return {
        "status": "healthy",
        "framework": "FastAPI",
        "database": db_status,
        "python_version": sys.version
    }

@app.get("/api/users", response_model=UsersResponse)
async def get_users(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(10, ge=1, le=100, description="每页数量")
):
    """获取用户列表（支持分页）"""
    try:
        conn = await get_db_connection()
        if conn:
            async with conn.cursor() as cursor:
                # 获取总数
                await cursor.execute("SELECT COUNT(*) FROM users")
                total = (await cursor.fetchone())[0]
                
                # 获取分页数据
                offset = (page - 1) * limit
                await cursor.execute(
                    "SELECT id, name, email, created_at FROM users LIMIT %s OFFSET %s",
                    (limit, offset)
                )
                rows = await cursor.fetchall()
                
                users = []
                for row in rows:
                    users.append({
                        "id": row[0],
                        "name": row[1],
                        "email": row[2],
                        "created_at": row[3].isoformat() if row[3] else None
                    })
                
                conn.close()
                
                return UsersResponse(
                    success=True,
                    data={
                        "total": total,
                        "page": page,
                        "limit": limit,
                        "items": users
                    }
                )
        else:
            # 使用备用内存数据
            start_index = (page - 1) * limit
            end_index = start_index + limit
            paginated_users = fallback_users[start_index:end_index]
            
            return UsersResponse(
                success=True,
                data={
                    "total": len(fallback_users),
                    "page": page,
                    "limit": limit,
                    "items": paginated_users
                }
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")

@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """根据 ID 获取用户"""
    try:
        conn = await get_db_connection()
        if conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "SELECT id, name, email, created_at FROM users WHERE id = %s",
                    (user_id,)
                )
                row = await cursor.fetchone()
                conn.close()
                
                if not row:
                    raise HTTPException(status_code=404, detail="用户不存在")
                
                user = User(
                    id=row[0],
                    name=row[1],
                    email=row[2]
                )
                
                return UserResponse(success=True, data=user)
        else:
            # 使用备用内存数据
            user = next((u for u in fallback_users if u["id"] == user_id), None)
            if not user:
                raise HTTPException(status_code=404, detail="用户不存在")
            return UserResponse(success=True, data=User(**user))
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)}")

@app.post("/api/users", response_model=UserResponse, status_code=201)
async def create_user(user: User):
    """创建新用户"""
    try:
        conn = await get_db_connection()
        if conn:
            async with conn.cursor() as cursor:
                # 检查邮箱是否已存在
                await cursor.execute("SELECT id FROM users WHERE email = %s", (user.email,))
                if await cursor.fetchone():
                    conn.close()
                    raise HTTPException(status_code=400, detail="邮箱已存在")
                
                # 插入新用户
                await cursor.execute(
                    "INSERT INTO users (name, email) VALUES (%s, %s)",
                    (user.name, user.email)
                )
                user_id = cursor.lastrowid
                await conn.commit()
                
                # 获取创建的用户
                await cursor.execute(
                    "SELECT id, name, email, created_at FROM users WHERE id = %s",
                    (user_id,)
                )
                row = await cursor.fetchone()
                conn.close()
                
                new_user = User(
                    id=row[0],
                    name=row[1],
                    email=row[2]
                )
                
                return UserResponse(success=True, data=new_user)
        else:
            # 使用备用内存数据
            if any(u["email"] == user.email for u in fallback_users):
                raise HTTPException(status_code=400, detail="邮箱已存在")
            
            new_user_dict = {
                "id": max(u["id"] for u in fallback_users) + 1 if fallback_users else 1,
                "name": user.name,
                "email": user.email
            }
            fallback_users.append(new_user_dict)
            return UserResponse(success=True, data=User(**new_user_dict))
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建用户失败: {str(e)}")

@app.put("/api/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_update: UserUpdate):
    """更新用户信息"""
    try:
        conn = await get_db_connection()
        if conn:
            async with conn.cursor() as cursor:
                # 检查用户是否存在
                await cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                if not await cursor.fetchone():
                    conn.close()
                    raise HTTPException(status_code=404, detail="用户不存在")
                
                # 检查邮箱是否被其他用户使用
                if user_update.email:
                    await cursor.execute(
                        "SELECT id FROM users WHERE email = %s AND id != %s",
                        (user_update.email, user_id)
                    )
                    if await cursor.fetchone():
                        conn.close()
                        raise HTTPException(status_code=400, detail="邮箱已被其他用户使用")
                
                # 构建更新语句
                update_fields = []
                update_values = []
                
                if user_update.name is not None:
                    update_fields.append("name = %s")
                    update_values.append(user_update.name)
                
                if user_update.email is not None:
                    update_fields.append("email = %s")
                    update_values.append(user_update.email)
                
                if update_fields:
                    update_values.append(user_id)
                    await cursor.execute(
                        f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s",
                        update_values
                    )
                    await conn.commit()
                
                # 获取更新后的用户
                await cursor.execute(
                    "SELECT id, name, email, created_at FROM users WHERE id = %s",
                    (user_id,)
                )
                row = await cursor.fetchone()
                conn.close()
                
                updated_user = User(
                    id=row[0],
                    name=row[1],
                    email=row[2]
                )
                
                return UserResponse(success=True, data=updated_user)
        else:
            # 使用备用内存数据
            user_index = next((i for i, u in enumerate(fallback_users) if u["id"] == user_id), None)
            if user_index is None:
                raise HTTPException(status_code=404, detail="用户不存在")
            
            if user_update.email and any(u["email"] == user_update.email and u["id"] != user_id for u in fallback_users):
                raise HTTPException(status_code=400, detail="邮箱已被其他用户使用")
            
            if user_update.name is not None:
                fallback_users[user_index]["name"] = user_update.name
            if user_update.email is not None:
                fallback_users[user_index]["email"] = user_update.email
            
            return UserResponse(success=True, data=User(**fallback_users[user_index]))
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新用户失败: {str(e)}")

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int):
    """删除用户"""
    try:
        conn = await get_db_connection()
        if conn:
            async with conn.cursor() as cursor:
                # 检查用户是否存在
                await cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
                row = await cursor.fetchone()
                if not row:
                    conn.close()
                    raise HTTPException(status_code=404, detail="用户不存在")
                
                user_name = row[0]
                
                # 删除用户
                await cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                await conn.commit()
                conn.close()
                
                return {
                    "success": True,
                    "message": f"用户 {user_name} 删除成功"
                }
        else:
            # 使用备用内存数据
            user_index = next((i for i, u in enumerate(fallback_users) if u["id"] == user_id), None)
            if user_index is None:
                raise HTTPException(status_code=404, detail="用户不存在")
            
            deleted_user = fallback_users.pop(user_index)
            return {
                "success": True,
                "message": f"用户 {deleted_user['name']} 删除成功"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除用户失败: {str(e)}")

# 错误处理
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"success": False, "message": "资源不存在"}

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"success": False, "message": "服务器内部错误"}

if __name__ == "__main__":
    # 默认端口 8080，HTTP 云函数通过环境变量设置为 9000
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)


