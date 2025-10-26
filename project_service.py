import re
from typing import Dict, Any, Optional
from k8s_client import k8s_client
from config import settings


class ProjectService:
    """项目（Profile/Namespace）管理服务"""
    
    @staticmethod
    def email_to_profile_name(email: str) -> str:
        """将邮箱转换为 Profile 名称"""
        return re.sub(r'[.@]', '-', email)
    
    def create_project(
        self,
        owner_email: str,
        cpu_limit: Optional[str] = None,
        memory_limit: Optional[str] = None,
        gpu_limit: Optional[str] = None,
        storage_size: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建项目（Profile）
        """
        profile_name = self.email_to_profile_name(owner_email)
        
        # 检查 Profile 是否已存在
        if k8s_client.get_profile(profile_name):
            raise ValueError(f"项目 {profile_name} 已存在")
        
        # 使用默认值或提供的值
        cpu = cpu_limit or settings.default_cpu_limit
        memory = f"{memory_limit or settings.default_memory_limit}Gi"
        gpu = gpu_limit or settings.default_gpu_limit
        storage = f"{storage_size or settings.default_storage_size}Gi"
        
        # 创建 ConfigMap
        configmap_data = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": f"default-install-config-9h2h2b6hbk",
                "namespace": profile_name
            },
            "data": {
                "profile-name": profile_name,
                "user": owner_email
            }
        }
        
        # 创建 Profile
        profile_data = {
            "apiVersion": "kubeflow.org/v1beta1",
            "kind": "Profile",
            "metadata": {
                "name": profile_name
            },
            "spec": {
                "owner": {
                    "kind": "User",
                    "name": owner_email
                },
                "resourceQuotaSpec": {
                    "hard": {
                        "cpu": cpu,
                        "memory": memory,
                        "requests.nvidia.com/l4": gpu,
                        "requests.storage": storage
                    }
                }
            }
        }
        
        result = k8s_client.create_profile(profile_data)
        
        # 等待命名空间创建
        import time
        max_retries = 30
        for i in range(max_retries):
            if k8s_client.namespace_exists(profile_name):
                break
            time.sleep(1)
        else:
            raise TimeoutError(f"等待命名空间 {profile_name} 创建超时")
        
        # 创建 AuthorizationPolicy
        try:
            k8s_client.create_authorization_policy(profile_name)
        except Exception as e:
            print(f"警告：创建 AuthorizationPolicy 失败: {e}")
        
        return {
            "name": profile_name,
            "owner": owner_email,
            "namespace": profile_name,
            "resources": {
                "cpu": cpu,
                "memory": memory,
                "gpu": gpu,
                "storage": storage
            }
        }
    
    def update_project_resources(
        self,
        profile_name: str,
        cpu_limit: Optional[str] = None,
        memory_limit: Optional[str] = None,
        gpu_limit: Optional[str] = None,
        storage_size: Optional[str] = None
    ) -> Dict[str, Any]:
        """更新项目资源限制"""
        profile = k8s_client.get_profile(profile_name)
        if not profile:
            raise ValueError(f"项目 {profile_name} 不存在")
        
        # 更新资源配额
        hard = profile['spec'].get('resourceQuotaSpec', {}).get('hard', {})
        
        if cpu_limit:
            hard['cpu'] = cpu_limit
        if memory_limit:
            hard['memory'] = f"{memory_limit}Gi" if not memory_limit.endswith('Gi') else memory_limit
        if gpu_limit:
            hard['requests.nvidia.com/l4'] = gpu_limit
        if storage_size:
            hard['requests.storage'] = f"{storage_size}Gi" if not storage_size.endswith('Gi') else storage_size
        
        if 'resourceQuotaSpec' not in profile['spec']:
            profile['spec']['resourceQuotaSpec'] = {}
        profile['spec']['resourceQuotaSpec']['hard'] = hard
        
        result = k8s_client.update_profile(profile_name, profile)
        
        return {
            "name": profile_name,
            "owner": profile['spec']['owner']['name'],
            "namespace": profile_name,
            "resources": hard
        }
    
    def delete_project(self, profile_name: str) -> Dict[str, str]:
        """删除项目（Profile）"""
        profile = k8s_client.get_profile(profile_name)
        if not profile:
            raise ValueError(f"项目 {profile_name} 不存在")
        
        k8s_client.delete_profile(profile_name)
        
        return {
            "name": profile_name,
            "message": "项目删除成功"
        }
    
    def get_project(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """获取项目信息"""
        profile = k8s_client.get_profile(profile_name)
        if not profile:
            return None
        
        hard = profile['spec'].get('resourceQuotaSpec', {}).get('hard', {})
        
        return {
            "name": profile_name,
            "owner": profile['spec']['owner']['name'],
            "namespace": profile_name,
            "resources": hard
        }
    
    def get_project_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """根据邮箱获取项目"""
        profile_name = self.email_to_profile_name(email)
        return self.get_project(profile_name)


project_service = ProjectService()

