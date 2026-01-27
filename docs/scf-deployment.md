# 腾讯云函数 FastAPI 部署指南

本指南专门解决 FastAPI 在腾讯云函数中的 `pydantic_core` 模块问题。

## 🚨 问题描述

在腾讯云函数环境中，FastAPI 可能遇到以下错误：
```
ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'
```

这是因为 `pydantic_core` 是一个 C 扩展模块，在云函数的 Linux 环境中可能因为架构不匹配而无法加载。

## 🔧 解决方案

### 方案 1：使用兼容版本（推荐）

使用 Pydantic 1.x 版本，避免 `pydantic_core` 依赖：

```txt
# requirements.txt
fastapi==0.95.2
uvicorn==0.22.0
pydantic==1.10.12
python-multipart==0.0.6
```

### 方案 2：完全无 Pydantic 版本

如果仍有问题，使用纯 Starlette：

```txt
# requirements-no-pydantic.txt
starlette==0.27.0
uvicorn==0.22.0
orjson==3.9.10
```

### 方案 3：指定平台构建

在 `requirements.txt` 中指定平台：

```txt
fastapi==0.95.2
uvicorn==0.22.0
pydantic==1.10.12 --platform linux_x86_64
```

## 📦 部署步骤

### 1. 准备依赖文件

```bash
# 使用兼容版本
cp requirements.txt requirements-scf.txt

# 或使用无 Pydantic 版本
cp requirements-no-pydantic.txt requirements.txt
```

### 2. 创建启动脚本

创建 `scf_bootstrap` 文件：

```bash
#!/bin/bash
export PORT=9000
export PYTHONPATH="./env/lib/python3.10/site-packages:$PYTHONPATH"

# 设置 Python 路径
export PATH="/var/lang/python310/bin:$PATH"

# 启动应用
python3.10 -m uvicorn main:app --host 0.0.0.0 --port 9000
```

### 3. 环境变量配置

在云函数控制台设置以下环境变量：

```bash
# 数据库配置（如果使用 MySQL）
DB_HOST=your_mysql_host
DB_USER=your_mysql_user  
DB_PASSWORD=your_mysql_password
DB_NAME=fastapi_demo

# Python 配置
PYTHONPATH=/var/user/env/lib/python3.10/site-packages
```

### 4. 打包部署

```bash
# 创建部署包
zip -r fastapi-scf.zip main.py scf_bootstrap requirements.txt

# 或使用 CLI 部署
scf deploy --name fastapi-app --runtime Python3.10
```

## 🔍 故障排除

### 问题 1：仍然报 pydantic_core 错误

**解决方案**：
1. 确认使用 `pydantic==1.10.12`
2. 删除所有 `pydantic_core` 相关依赖
3. 使用 `requirements-no-pydantic.txt`

### 问题 2：导入错误

**解决方案**：
```bash
# 在 scf_bootstrap 中添加
export PYTHONPATH="/var/user:/var/user/env/lib/python3.10/site-packages:$PYTHONPATH"
```

### 问题 3：启动超时

**解决方案**：
1. 增加函数超时时间到 30 秒
2. 优化代码，减少启动时间
3. 使用预置并发

## 📋 最佳实践

### 1. 依赖管理
- 使用固定版本号
- 避免使用 `[standard]` 等可选依赖
- 定期测试依赖兼容性

### 2. 代码优化
```python
# 延迟导入
import os
if os.getenv('SCF_RUNTIME'):
    # 云函数环境特殊处理
    pass

# 条件依赖
try:
    from pydantic import BaseModel
except ImportError:
    # 降级处理
    BaseModel = dict
```

### 3. 监控告警
- 设置函数执行监控
- 配置错误告警
- 定期检查日志

## 🚀 部署验证

部署成功后，访问以下端点验证：

```bash
# 健康检查
curl https://your-function-url/health

# API 文档
curl https://your-function-url/docs

# 测试接口
curl https://your-function-url/api/users
```

## 📚 相关文档

- [腾讯云函数 Python 运行时](https://cloud.tencent.com/document/product/583/56051)
- [FastAPI 部署指南](https://fastapi.tiangolo.com/deployment/)
- [Pydantic 版本兼容性](https://pydantic-docs.helpmanual.io/)