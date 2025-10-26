from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict


class UserCreate(BaseModel):
    """创建用户请求模型"""
    email: EmailStr = Field(..., description="用户邮箱")
    password: Optional[str] = Field(None, min_length=6, description="用户密码，不提供则自动生成")
    username: Optional[str] = Field(None, description="用户名，不提供则从邮箱提取")


class UserPasswordReset(BaseModel):
    """重置用户密码请求模型"""
    email: EmailStr = Field(..., description="用户邮箱")
    new_password: Optional[str] = Field(None, min_length=6, description="新密码，不提供则自动生成")


class UserResponse(BaseModel):
    """用户响应模型"""
    email: str
    username: str
    password: Optional[str] = None  # 仅在创建或重置密码时返回
    login_url: Optional[str] = None


class ProjectCreate(BaseModel):
    """创建项目请求模型"""
    owner_email: EmailStr = Field(..., description="项目所有者邮箱")
    cpu_limit: Optional[str] = Field(None, description="CPU 限制，例如：2")
    memory_limit: Optional[str] = Field(None, description="内存限制（GiB），例如：4")
    storage_size: Optional[str] = Field(None, description="存储大小（GiB），例如：10")
    
    # GPU 资源配置（使用字典，支持任意 Kubernetes 资源键）
    resources: Optional[Dict[str, str]] = Field(
        None, 
        description="其他资源限制，支持任意 Kubernetes 资源键，例如：{'requests.nvidia.com/l4': '1', 'requests.nvidia.com/gpu': '0'}"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "owner_email": "user@example.com",
                "cpu_limit": "4",
                "memory_limit": "8",
                "storage_size": "20",
                "resources": {
                    "requests.nvidia.com/l4": "1",
                    "requests.nvidia.com/gpu": "0"
                }
            }
        }


class ProjectUpdate(BaseModel):
    """更新项目资源限制请求模型"""
    cpu_limit: Optional[str] = Field(None, description="CPU 限制")
    memory_limit: Optional[str] = Field(None, description="内存限制（GiB）")
    storage_size: Optional[str] = Field(None, description="存储大小（GiB）")
    
    # GPU 资源配置（使用字典，支持任意 Kubernetes 资源键）
    resources: Optional[Dict[str, str]] = Field(
        None,
        description="其他资源限制，支持任意 Kubernetes 资源键，例如：{'requests.nvidia.com/l4': '1'}"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "cpu_limit": "8",
                "memory_limit": "16",
                "resources": {
                    "requests.nvidia.com/l4": "2"
                }
            }
        }


class ProjectResponse(BaseModel):
    """项目响应模型"""
    name: str
    owner: str
    namespace: str
    resources: dict


class ResourceQuota(BaseModel):
    """资源配额模型"""
    cpu: Optional[str] = None
    memory: Optional[str] = None
    gpu: Optional[str] = None
    storage: Optional[str] = None


class ApiResponse(BaseModel):
    """通用 API 响应模型"""
    success: bool
    message: str
    data: Optional[dict] = None

