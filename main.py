from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import uvicorn

from config import settings
from models import (
    UserCreate, UserPasswordReset, UserResponse,
    ProjectCreate, ProjectUpdate, ProjectResponse,
    ApiResponse
)
from user_service import user_service
from project_service import project_service


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="基于 Kubeflow 1.10 的用户和项目管理 API"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=ApiResponse)
async def root():
    """API 根路径"""
    return ApiResponse(
        success=True,
        message="Kubeflow User Management API",
        data={
            "version": settings.api_version,
            "endpoints": {
                "users": "/api/users",
                "projects": "/api/projects",
                "docs": "/docs"
            }
        }
    )


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


# ==================== 用户管理接口 ====================

@app.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    """
    创建用户
    
    - email: 用户邮箱（必填）
    - password: 用户密码（可选，不提供则自动生成）
    - username: 用户名（可选，不提供则从邮箱提取）
    """
    try:
        result = user_service.create_user(
            email=user.email,
            password=user.password,
            username=user.username
        )
        
        profile_name = project_service.email_to_profile_name(user.email)
        login_url = f"https://{settings.kubeflow_domain}/?ns={profile_name}"
        
        return UserResponse(
            email=result["email"],
            username=result["username"],
            password=result["password"],
            login_url=login_url
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/users/{email}", response_model=UserResponse)
async def get_user(email: str):
    """获取用户信息"""
    try:
        user_info = user_service.get_user(email)
        if not user_info:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"用户 {email} 不存在")
        
        profile_name = project_service.email_to_profile_name(email)
        login_url = f"https://{settings.kubeflow_domain}/?ns={profile_name}"
        
        return UserResponse(
            email=user_info["email"],
            username=user_info["username"],
            login_url=login_url
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.put("/api/users/password", response_model=UserResponse)
async def reset_password(reset_data: UserPasswordReset):
    """
    重置用户密码
    
    - email: 用户邮箱（必填）
    - new_password: 新密码（可选，不提供则自动生成）
    """
    try:
        result = user_service.reset_password(
            email=reset_data.email,
            new_password=reset_data.new_password
        )
        
        profile_name = project_service.email_to_profile_name(reset_data.email)
        login_url = f"https://{settings.kubeflow_domain}/?ns={profile_name}"
        
        return UserResponse(
            email=result["email"],
            username=user_service.extract_username(result["email"]),
            password=result["password"],
            login_url=login_url
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.delete("/api/users/{email}", response_model=ApiResponse)
async def delete_user(email: str):
    """删除用户"""
    try:
        result = user_service.delete_user(email)
        return ApiResponse(
            success=True,
            message=result["message"],
            data={"email": email}
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ==================== 项目管理接口 ====================

@app.post("/api/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(project: ProjectCreate):
    """
    创建项目（Profile/Namespace）
    
    - owner_email: 项目所有者邮箱（必填）
    - cpu_limit: CPU 限制（可选，默认2）
    - memory_limit: 内存限制 GiB（可选，默认4）
    - gpu_limit: GPU 限制，同时设置 gpu 和 l4（可选，默认0）
    - storage_size: 存储大小 GiB（可选，默认10）
    """
    try:
        result = project_service.create_project(
            owner_email=project.owner_email,
            cpu_limit=project.cpu_limit,
            memory_limit=project.memory_limit,
            gpu_limit=project.gpu_limit,
            storage_size=project.storage_size
        )
        
        return ProjectResponse(
            name=result["name"],
            owner=result["owner"],
            namespace=result["namespace"],
            resources=result["resources"]
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except TimeoutError as e:
        raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/projects/{profile_name}", response_model=ProjectResponse)
async def get_project(profile_name: str):
    """获取项目信息"""
    try:
        project_info = project_service.get_project(profile_name)
        if not project_info:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"项目 {profile_name} 不存在")
        
        return ProjectResponse(
            name=project_info["name"],
            owner=project_info["owner"],
            namespace=project_info["namespace"],
            resources=project_info["resources"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/projects/by-email/{email}", response_model=ProjectResponse)
async def get_project_by_email(email: str):
    """根据邮箱获取项目信息"""
    try:
        project_info = project_service.get_project_by_email(email)
        if not project_info:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"用户 {email} 的项目不存在")
        
        return ProjectResponse(
            name=project_info["name"],
            owner=project_info["owner"],
            namespace=project_info["namespace"],
            resources=project_info["resources"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.put("/api/projects/{profile_name}", response_model=ProjectResponse)
async def update_project(profile_name: str, update_data: ProjectUpdate):
    """
    更新项目资源限制
    
    - cpu_limit: CPU 限制（可选）
    - memory_limit: 内存限制 GiB（可选）
    - gpu_limit: GPU 限制，同时设置 gpu 和 l4（可选）
    - storage_size: 存储大小 GiB（可选）
    """
    try:
        result = project_service.update_project_resources(
            profile_name=profile_name,
            cpu_limit=update_data.cpu_limit,
            memory_limit=update_data.memory_limit,
            gpu_limit=update_data.gpu_limit,
            storage_size=update_data.storage_size
        )
        
        return ProjectResponse(
            name=result["name"],
            owner=result["owner"],
            namespace=result["namespace"],
            resources=result["resources"]
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.delete("/api/projects/{profile_name}", response_model=ApiResponse)
async def delete_project(profile_name: str):
    """删除项目（Profile/Namespace）"""
    try:
        result = project_service.delete_project(profile_name)
        return ApiResponse(
            success=True,
            message=result["message"],
            data={"name": profile_name}
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=True
    )

