# Kubeflow User Management API

基于 Kubeflow 1.10 的用户和项目管理平台，提供用户创建、密码管理、项目（Profile/Namespace）管理和资源配额管理功能。

## 功能特性

### 用户管理
- ✅ 创建用户（支持自定义或自动生成密码）
- ✅ 查询用户信息
- ✅ 修改/重置用户密码
- ✅ 删除用户

### 项目管理
- ✅ 创建项目（Profile/Namespace）
- ✅ 查询项目信息
- ✅ 修改项目资源限制（CPU、内存、GPU、存储）
- ✅ 删除项目

### 资源配额管理
- CPU 限制
- 内存限制
- GPU 限制（同时设置 `requests.nvidia.com/gpu` 和 `requests.nvidia.com/l4`）
- 存储配额

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并修改配置：

```bash
cp .env.example .env
```

主要配置项：
- `KUBECONFIG_PATH`: Kubernetes 配置文件路径（可选）
- `DEX_NAMESPACE`: Dex 所在命名空间（默认 auth）
- `KUBEFLOW_DOMAIN`: Kubeflow 访问域名

### 3. 运行服务

```bash
python main.py
```

服务将在 `http://localhost:8000` 启动。

### 4. 查看 API 文档

访问 `http://localhost:8000/docs` 查看交互式 API 文档。

## API 接口说明

### 用户管理

#### 创建用户
```http
POST /api/users
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "optional_password",
  "username": "optional_username"
}
```

#### 查询用户
```http
GET /api/users/{email}
```

#### 重置密码
```http
PUT /api/users/password
Content-Type: application/json

{
  "email": "user@example.com",
  "new_password": "optional_new_password"
}
```

#### 删除用户
```http
DELETE /api/users/{email}
```

### 项目管理

#### 创建项目
```http
POST /api/projects
Content-Type: application/json

{
  "owner_email": "user@example.com",
  "cpu_limit": "4",
  "memory_limit": "8",
  "gpu_limit": "1",
  "storage_size": "20"
}
```

#### 查询项目
```http
GET /api/projects/{profile_name}
GET /api/projects/by-email/{email}
```

#### 更新项目资源
```http
PUT /api/projects/{profile_name}
Content-Type: application/json

{
  "cpu_limit": "8",
  "memory_limit": "16",
  "gpu_limit": "2"
}
```

#### 删除项目
```http
DELETE /api/projects/{profile_name}
```

## 使用示例

### Python 示例

```python
import requests

API_URL = "http://localhost:8000"

# 创建用户
response = requests.post(
    f"{API_URL}/api/users",
    json={
        "email": "test@example.com",
        "password": "mypassword123"
    }
)
user = response.json()
print(f"用户创建成功: {user['email']}, 密码: {user['password']}")

# 创建项目
response = requests.post(
    f"{API_URL}/api/projects",
    json={
        "owner_email": "test@example.com",
        "cpu_limit": "4",
        "memory_limit": "8",
        "gpu_limit": "1"
    }
)
project = response.json()
print(f"项目创建成功: {project['name']}")

# 更新资源限制
response = requests.put(
    f"{API_URL}/api/projects/{project['name']}",
    json={
        "cpu_limit": "8",
        "memory_limit": "16"
    }
)
print("资源限制更新成功")
```

### cURL 示例

```bash
# 创建用户
curl -X POST "http://localhost:8000/api/users" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# 创建项目
curl -X POST "http://localhost:8000/api/projects" \
  -H "Content-Type: application/json" \
  -d '{"owner_email": "test@example.com", "cpu_limit": "4", "memory_limit": "8"}'

# 重置密码
curl -X PUT "http://localhost:8000/api/users/password" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

## 项目结构

```
kubeflow-manager/
├── main.py              # FastAPI 主应用
├── config.py            # 配置管理
├── models.py            # 数据模型
├── k8s_client.py        # Kubernetes 客户端封装
├── user_service.py      # 用户管理服务
├── project_service.py   # 项目管理服务
├── requirements.txt     # 依赖列表
├── .env.example         # 环境变量示例
└── README.md           # 项目文档
```

## 技术栈

- **FastAPI**: Web 框架
- **Kubernetes Python Client**: K8s API 交互
- **Passlib**: 密码哈希
- **Pydantic**: 数据验证
- **Uvicorn**: ASGI 服务器

## 注意事项

1. 确保有正确的 Kubernetes 集群访问权限
2. Dex 必须已正确配置并运行
3. 需要有足够的权限操作 Profiles、ConfigMaps 和 Secrets
4. 建议在生产环境中添加认证和授权机制

## 部署建议

### Docker 部署

创建 `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

构建并运行：

```bash
docker build -t kubeflow-manager .
docker run -p 8000:8000 -v ~/.kube:/root/.kube kubeflow-manager
```

### Kubernetes 部署

可以将此服务部署到 Kubernetes 集群中，使用 ServiceAccount 进行认证。

## 许可证

MIT License

