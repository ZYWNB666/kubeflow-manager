import os
import re
import base64
import secrets
import string
import yaml
from passlib.hash import bcrypt
from typing import Optional, Tuple, Dict, Any
from k8s_client import k8s_client
from config import settings


class UserService:
    """用户管理服务"""
    
    @staticmethod
    def generate_password(length: int = 10) -> str:
        """生成随机密码"""
        alphabet = string.ascii_lowercase
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def hash_password(password: str) -> Tuple[str, str]:
        """
        哈希密码并返回 Base64 编码
        返回: (base64_hash, env_name)
        """
        hashed = bcrypt.using(rounds=12, ident="2y").hash(password)
        hashed_base64 = base64.b64encode(hashed.encode()).decode()
        env_name = password.upper()
        return hashed_base64, env_name
    
    @staticmethod
    def extract_username(email: str) -> str:
        """从邮箱提取用户名"""
        return email.split('@')[0]
    
    def create_user(self, email: str, password: Optional[str] = None, username: Optional[str] = None) -> Dict[str, str]:
        """
        创建用户
        返回: {"email": str, "username": str, "password": str}
        """
        if not k8s_client.namespace_exists(settings.dex_namespace):
            raise ValueError(f"命名空间 {settings.dex_namespace} 不存在")
        
        if not username:
            username = self.extract_username(email)
        
        if not password:
            password = self.generate_password()
        
        passwd_base64, passwd_hash_env_name = self.hash_password(password)
        
        # 更新 Secret
        env_key = f"USER_{passwd_hash_env_name}"
        secret_data = {env_key: passwd_base64}
        k8s_client.patch_secret(settings.dex_secret_name, settings.dex_namespace, secret_data)
        
        # 更新 ConfigMap
        configmap = k8s_client.get_configmap(settings.dex_configmap_name, settings.dex_namespace)
        if not configmap:
            raise ValueError(f"ConfigMap {settings.dex_configmap_name} 不存在")
        
        config_data = yaml.safe_load(configmap.data.get('config.yaml', '{}'))
        
        if 'staticPasswords' not in config_data:
            config_data['staticPasswords'] = []
        
        # 检查用户是否已存在
        existing_users = [u for u in config_data['staticPasswords'] if u.get('email') == email]
        if existing_users:
            raise ValueError(f"用户 {email} 已存在")
        
        # 添加新用户
        new_user = {
            'email': email,
            'hashFromEnv': env_key,
            'username': username
        }
        config_data['staticPasswords'].append(new_user)
        
        configmap.data['config.yaml'] = yaml.dump(config_data, default_flow_style=False)
        k8s_client.update_configmap(settings.dex_configmap_name, settings.dex_namespace, configmap)
        
        # 重启 Dex
        k8s_client.restart_deployment(settings.dex_deployment_name, settings.dex_namespace)
        
        return {
            "email": email,
            "username": username,
            "password": password
        }
    
    def reset_password(self, email: str, new_password: Optional[str] = None) -> Dict[str, str]:
        """
        重置用户密码
        返回: {"email": str, "password": str}
        """
        if not new_password:
            new_password = self.generate_password()
        
        passwd_base64, passwd_hash_env_name = self.hash_password(new_password)
        env_key = f"USER_{passwd_hash_env_name}"
        
        # 获取 ConfigMap 并查找用户
        configmap = k8s_client.get_configmap(settings.dex_configmap_name, settings.dex_namespace)
        if not configmap:
            raise ValueError(f"ConfigMap {settings.dex_configmap_name} 不存在")
        
        config_data = yaml.safe_load(configmap.data.get('config.yaml', '{}'))
        
        if 'staticPasswords' not in config_data:
            raise ValueError(f"用户 {email} 不存在")
        
        # 查找并更新用户
        user_found = False
        old_env_key = None
        for user in config_data['staticPasswords']:
            if user.get('email') == email:
                old_env_key = user.get('hashFromEnv')
                user['hashFromEnv'] = env_key
                user_found = True
                break
        
        if not user_found:
            raise ValueError(f"用户 {email} 不存在")
        
        # 更新 Secret（添加新密码，删除旧密码）
        secret_data = {env_key: passwd_base64}
        k8s_client.patch_secret(settings.dex_secret_name, settings.dex_namespace, secret_data)
        
        # 如果有旧的环境变量，从 Secret 中删除
        if old_env_key and old_env_key != env_key:
            try:
                secret = k8s_client.get_secret(settings.dex_secret_name, settings.dex_namespace)
                if secret and secret.data and old_env_key in secret.data:
                    del secret.data[old_env_key]
                    k8s_client.core_v1.replace_namespaced_secret(
                        settings.dex_secret_name, 
                        settings.dex_namespace, 
                        secret
                    )
            except Exception as e:
                print(f"警告：删除旧密码失败: {e}")
        
        # 更新 ConfigMap
        configmap.data['config.yaml'] = yaml.dump(config_data, default_flow_style=False)
        k8s_client.update_configmap(settings.dex_configmap_name, settings.dex_namespace, configmap)
        
        # 重启 Dex
        k8s_client.restart_deployment(settings.dex_deployment_name, settings.dex_namespace)
        
        return {
            "email": email,
            "password": new_password
        }
    
    def delete_user(self, email: str) -> Dict[str, str]:
        """删除用户"""
        configmap = k8s_client.get_configmap(settings.dex_configmap_name, settings.dex_namespace)
        if not configmap:
            raise ValueError(f"ConfigMap {settings.dex_configmap_name} 不存在")
        
        config_data = yaml.safe_load(configmap.data.get('config.yaml', '{}'))
        
        if 'staticPasswords' not in config_data:
            raise ValueError(f"用户 {email} 不存在")
        
        # 查找并删除用户
        env_key_to_delete = None
        new_passwords = []
        for user in config_data['staticPasswords']:
            if user.get('email') == email:
                env_key_to_delete = user.get('hashFromEnv')
            else:
                new_passwords.append(user)
        
        if env_key_to_delete is None:
            raise ValueError(f"用户 {email} 不存在")
        
        config_data['staticPasswords'] = new_passwords
        
        # 从 Secret 中删除密码
        if env_key_to_delete:
            try:
                secret = k8s_client.get_secret(settings.dex_secret_name, settings.dex_namespace)
                if secret and secret.data and env_key_to_delete in secret.data:
                    del secret.data[env_key_to_delete]
                    k8s_client.core_v1.replace_namespaced_secret(
                        settings.dex_secret_name, 
                        settings.dex_namespace, 
                        secret
                    )
            except Exception as e:
                print(f"警告：删除密码失败: {e}")
        
        # 更新 ConfigMap
        configmap.data['config.yaml'] = yaml.dump(config_data, default_flow_style=False)
        k8s_client.update_configmap(settings.dex_configmap_name, settings.dex_namespace, configmap)
        
        # 重启 Dex
        k8s_client.restart_deployment(settings.dex_deployment_name, settings.dex_namespace)
        
        return {"email": email, "message": "用户删除成功"}
    
    def get_user(self, email: str) -> Optional[Dict[str, str]]:
        """获取用户信息"""
        configmap = k8s_client.get_configmap(settings.dex_configmap_name, settings.dex_namespace)
        if not configmap:
            return None
        
        config_data = yaml.safe_load(configmap.data.get('config.yaml', '{}'))
        
        if 'staticPasswords' not in config_data:
            return None
        
        for user in config_data['staticPasswords']:
            if user.get('email') == email:
                return {
                    "email": user.get('email'),
                    "username": user.get('username'),
                    "hashFromEnv": user.get('hashFromEnv')
                }
        
        return None


user_service = UserService()

