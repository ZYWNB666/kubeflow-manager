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
- CPU 限制（hard）
- 内存限制（hard）
- GPU 资源限制（支持任意 Kubernetes 资源键）
  - `requests.nvidia.com/l4`
  - `requests.nvidia.com/gpu`
  - 其他自定义资源
- 存储配额（hard）
- 灵活扩展：支持任意 Kubernetes ResourceQuota 资源键

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
  "storage_size": "20",
  "resources": {
    "requests.nvidia.com/l4": "1"
  }
}
```

**注意**：`resources` 字段支持任意 Kubernetes 资源键，可灵活配置各种资源限制。

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
  "resources": {
    "requests.nvidia.com/l4": "2"
  }
}
```

**注意**：只更新提供的字段，未提供的字段保持不变。

#### 删除项目
```http
DELETE /api/projects/{profile_name}
```

## 使用示例

### Python 示例

```python
import requests

API_URL = "http://localhost:8000"

# 1. 创建用户（自动生成密码）
response = requests.post(
    f"{API_URL}/api/users",
    json={"email": "test@example.com"}
)
user = response.json()
print(f"✓ 用户: {user['email']}, 密码: {user['password']}")
print(f"✓ 登录: {user['login_url']}")

# 2. 创建项目（指定资源配额）
response = requests.post(
    f"{API_URL}/api/projects",
    json={
        "owner_email": "test@example.com",
        "cpu_limit": "4",
        "memory_limit": "8",
        "storage_size": "20",
        "resources": {
            "requests.nvidia.com/l4": "1"
        }
    }
)
project = response.json()
print(f"✓ 项目: {project['name']}")
print(f"✓ 资源: {project['resources']}")

# 3. 更新资源限制
response = requests.put(
    f"{API_URL}/api/projects/{project['name']}",
    json={
        "cpu_limit": "8",
        "memory_limit": "16",
        "resources": {
            "requests.nvidia.com/l4": "2"
        }
    }
)
print("✓ 资源限制更新成功")

# 4. 查询项目信息
response = requests.get(f"{API_URL}/api/projects/by-email/test@example.com")
project_info = response.json()
print(f"✓ 当前配额: {project_info['resources']}")

# 5. 重置用户密码
response = requests.put(
    f"{API_URL}/api/users/password",
    json={"email": "test@example.com"}
)
reset = response.json()
print(f"✓ 新密码: {reset['password']}")
```

### cURL 示例

#### 用户管理

```bash
# 创建用户（自动生成密码）
curl -X POST "http://localhost:8000/api/users" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'

# 创建用户（指定密码）
curl -X POST "http://localhost:8000/api/users" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "mypass123"}'

# 查询用户
curl -X GET "http://localhost:8000/api/users/user@example.com"

# 重置密码（自动生成）
curl -X PUT "http://localhost:8000/api/users/password" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'

# 重置密码（指定新密码）
curl -X PUT "http://localhost:8000/api/users/password" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "new_password": "newpass123"}'

# 删除用户
curl -X DELETE "http://localhost:8000/api/users/user@example.com"
```

#### 项目管理

```bash
# 创建项目（使用默认资源配额）
curl -X POST "http://localhost:8000/api/projects" \
  -H "Content-Type: application/json" \
  -d '{"owner_email": "user@example.com"}'

# 创建项目（自定义资源配额）
curl -X POST "http://localhost:8000/api/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "owner_email": "user@example.com",
    "cpu_limit": "8",
    "memory_limit": "16",
    "storage_size": "50",
    "resources": {
      "requests.nvidia.com/l4": "2"
    }
  }'

# 查询项目（通过 profile 名称）
curl -X GET "http://localhost:8000/api/projects/user-example-com"

# 查询项目（通过邮箱）
curl -X GET "http://localhost:8000/api/projects/by-email/user@example.com"

# 更新 CPU 和内存
curl -X PUT "http://localhost:8000/api/projects/user-example-com" \
  -H "Content-Type: application/json" \
  -d '{"cpu_limit": "16", "memory_limit": "32"}'

# 更新 GPU 资源（只设置 L4）
curl -X PUT "http://localhost:8000/api/projects/user-example-com" \
  -H "Content-Type: application/json" \
  -d '{
    "resources": {
      "requests.nvidia.com/l4": "4"
    }
  }'

# 更新多种资源
curl -X PUT "http://localhost:8000/api/projects/user-example-com" \
  -H "Content-Type: application/json" \
  -d '{
    "cpu_limit": "32",
    "memory_limit": "64",
    "resources": {
      "requests.nvidia.com/l4": "8"
    }
  }'

# 删除项目
curl -X DELETE "http://localhost:8000/api/projects/user-example-com"
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

## 高级用法

### 灵活的 GPU 资源配置

系统实现了智能 GPU 资源管理，`resources` 字段支持任意 Kubernetes 资源键。

**GPU 自动清零逻辑**：
当 `resources` 中包含任何 GPU 相关的键时（匹配 `nvidia.com`、`amd.com/gpu`、`gpu` 等模式），系统会：
1. 将配置文件中定义的所有 GPU 键设为 0
2. 将已存在的其他 GPU 键也设为 0  
3. 应用用户提供的值

这确保了不同 GPU 类型之间不会产生资源冲突。

```bash
# 场景1：只使用 L4 GPU（其他 GPU 自动设为 0）
curl -X POST "http://localhost:8000/api/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "owner_email": "user@example.com",
    "resources": {
      "requests.nvidia.com/l4": "2"
    }
  }'
# 结果：gpu=0, l4=2, t4=0（config 中定义的其他 GPU 自动为 0）

# 场景2：使用多种 GPU（明确指定各自的值）
curl -X POST "http://localhost:8000/api/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "owner_email": "user@example.com",
    "resources": {
      "requests.nvidia.com/l4": "2",
      "requests.nvidia.com/h100": "1"
    }
  }'
# 结果：gpu=0, l4=2, t4=0, h100=1

# 场景3：添加其他 Kubernetes 资源限制（不触发 GPU 清零）
curl -X PUT "http://localhost:8000/api/projects/user-example-com" \
  -H "Content-Type: application/json" \
  -d '{
    "resources": {
      "persistentvolumeclaims": "5",
      "services": "10"
    }
  }'
# GPU 配额保持不变（因为没有 GPU 相关的键）
```

### 资源配额说明

- **CPU 限制**：以核心为单位，例如 "4" 表示 4 核
- **内存限制**：以 GiB 为单位，例如 "8" 表示 8 GiB（自动添加 Gi 后缀）
- **存储配额**：以 GiB 为单位，例如 "20" 表示 20 GiB
- **GPU 资源**：
  - `requests.nvidia.com/l4`: NVIDIA L4 GPU 数量
  - `requests.nvidia.com/gpu`: 通用 NVIDIA GPU 数量
  - 可根据集群配置添加其他 GPU 类型

### 默认资源配额

如果创建项目时不指定资源，将使用以下默认值：
- CPU: 2 核
- 内存: 4 GiB
- GPU: 0
- 存储: 10 GiB

可在 `.env` 文件中修改默认值：
```bash
DEFAULT_CPU_LIMIT=4
DEFAULT_MEMORY_LIMIT=8
DEFAULT_GPU_LIMIT=0
DEFAULT_STORAGE_SIZE=20

# GPU 资源键列表（JSON 数组格式）
GPU_RESOURCE_KEYS=["requests.nvidia.com/gpu","requests.nvidia.com/l4"]
```

**注意**：`GPU_RESOURCE_KEYS` 定义了哪些资源键被视为 GPU 资源。

**GPU 资源自动管理逻辑**：
- 创建或更新项目时，如果 `resources` 中包含**任何 GPU 相关的键**（包含 `nvidia.com`、`amd.com/gpu` 或 `gpu` 等模式）
- 系统会自动将 `GPU_RESOURCE_KEYS` 中定义的所有 GPU 键设为 0
- 同时将已存在的其他 GPU 键也设为 0
- 然后应用用户提供的值

**示例**：
```bash
# Config 中定义：gpu_resource_keys = ["requests.nvidia.com/gpu", "requests.nvidia.com/l4"]
# 如果请求包含任何 GPU（如 h100）：
curl -X PUT "http://localhost:8000/api/projects/xxx" \
  -d '{"resources": {"requests.nvidia.com/h100": "1"}}'

# 结果：gpu=0, l4=0, h100=1（config 中的键自动清零，只有 h100 为 1）
```

## 常见问题

### Q: GPU 资源是如何自动管理的？
**A:** 为了避免资源冲突，系统实现了智能 GPU 管理：
- 当请求中包含任何 GPU 相关资源（匹配模式：`nvidia.com`、`amd.com/gpu`、`gpu`）时
- 自动将配置文件中定义的所有 GPU 键设为 0
- 自动将已存在的其他 GPU 键也设为 0
- 最后应用用户提供的值

例如：
```bash
# 配置：gpu_resource_keys = ["requests.nvidia.com/gpu", "requests.nvidia.com/l4", "requests.nvidia.com/t4"]
# 请求只设置 l4
curl -X PUT "http://localhost:8000/api/projects/xxx" \
  -d '{"resources": {"requests.nvidia.com/l4": "2"}}'
# 结果：gpu=0, l4=2, t4=0（其他 GPU 自动清零）
```

### Q: 如何只更新某一个资源而不影响其他资源？
**A:** 
- **非 GPU 资源**：只在请求中包含要更新的字段，未包含的字段保持不变
- **GPU 资源**：由于自动清零机制，更新任何 GPU 都会重置其他 GPU 为 0

```bash
# 只更新 CPU（其他资源不变）
curl -X PUT "http://localhost:8000/api/projects/xxx" \
  -d '{"cpu_limit": "16"}'

# 更新 GPU（会自动清零其他 GPU）
curl -X PUT "http://localhost:8000/api/projects/xxx" \
  -d '{"resources": {"requests.nvidia.com/l4": "2"}}'
```

### Q: 为什么密码查询时返回 null？
**A:** 出于安全考虑，密码经过单向哈希加密，无法还原。只有创建用户和重置密码时才会返回明文密码。

### Q: Profile 名称是如何生成的？
**A:** 将邮箱中的 `.` 和 `@` 替换为 `-`。例如：
- `user@example.com` → `user-example-com`
- `john.doe@company.com` → `john-doe-company-com`

### Q: 如何查看 API 的详细文档？
**A:** 启动服务后访问 `http://localhost:8000/docs`，可以看到交互式 API 文档（Swagger UI）。

### Q: 为什么我需要在 config 中定义 GPU 资源键？
**A:** 配置文件中的 `gpu_resource_keys` 用于：
- 定义哪些资源键应该被视为 GPU 资源
- 在更新 GPU 配置时，自动清零这些键以避免资源冲突
- 便于集中管理和修改 GPU 类型，无需改动代码

## 注意事项

1. **权限要求**：确保有正确的 Kubernetes 集群访问权限
2. **Dex 配置**：Dex 必须已正确配置并运行在 `auth` 命名空间
3. **RBAC 权限**：需要有足够的权限操作 Profiles、ConfigMaps、Secrets 和 Deployments
4. **安全建议**：生产环境中建议添加 API 认证和授权机制
5. **并发控制**：多个并发请求可能导致资源冲突，建议实现乐观锁或分布式锁
6. **资源限制类型**：本系统只设置 ResourceQuota 的 hard 限制（最高资源限制），不设置 LimitRange
7. **GPU 资源管理**：更新任何 GPU 资源时，会自动清零 config 中定义的其他 GPU 资源，这是为了避免资源冲突
8. **配置修改**：修改 `config.py` 或 `.env` 后需要重启服务才能生效

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

## API 参考

### 数据模型

#### UserCreate
```json
{
  "email": "user@example.com",      // 必填
  "password": "mypassword",         // 可选，不提供自动生成
  "username": "myusername"          // 可选，不提供从邮箱提取
}
```

#### ProjectCreate
```json
{
  "owner_email": "user@example.com",  // 必填
  "cpu_limit": "4",                   // 可选，默认 2
  "memory_limit": "8",                // 可选，默认 4（GiB）
  "storage_size": "20",               // 可选，默认 10（GiB）
  "resources": {                      // 可选，支持任意 K8s 资源键
    "requests.nvidia.com/l4": "1"
  }
}
```

#### ProjectUpdate
```json
{
  "cpu_limit": "8",                   // 可选
  "memory_limit": "16",               // 可选（GiB）
  "storage_size": "30",               // 可选（GiB）
  "resources": {                      // 可选
    "requests.nvidia.com/l4": "2"
  }
}
```

### 响应格式

#### 成功响应
```json
{
  "name": "user-example-com",
  "owner": "user@example.com",
  "namespace": "user-example-com",
  "resources": {
    "cpu": "8",
    "memory": "16Gi",
    "requests.nvidia.com/l4": "2",
    "requests.storage": "30Gi"
  }
}
```

#### 错误响应
```json
{
  "detail": "项目 xxx 不存在"
}
```

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

