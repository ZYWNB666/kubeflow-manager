from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # Kubernetes 配置
    kubeconfig_path: Optional[str] = None  # 为 None 时使用集群内配置
    
    # Dex 配置
    dex_namespace: str = "auth"
    dex_configmap_name: str = "dex"
    dex_secret_name: str = "dex-passwords"
    dex_deployment_name: str = "dex"
    
    # Kubeflow 配置
    kubeflow_domain: str = "kubeflow.id.gametech.garenanow.com"
    
    # 默认资源配额
    default_cpu_limit: str = "2"
    default_memory_limit: str = "4"
    default_gpu_limit: str = "0"  # NVIDIA L4 GPU
    default_storage_size: str = "10"
    
    # GPU 资源键列表（更新时如果设置了任何 GPU，其他 GPU 自动设为 0）
    gpu_resource_keys: list = [
        "requests.nvidia.com/gpu",
        "requests.nvidia.com/l4",
        "requests.nvidia.com/t4",
    ]
    
    # API 配置
    api_title: str = "Kubeflow User Management API"
    api_version: str = "1.0.0"
    api_port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

