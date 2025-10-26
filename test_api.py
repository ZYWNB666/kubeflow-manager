"""
Kubeflow 用户管理平台测试脚本

使用方法：
1. 确保服务已启动：python main.py
2. 运行测试：python test_api.py
"""

import requests
import json
from typing import Dict, Any


class KubeflowManagerClient:
    """Kubeflow Manager API 客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def create_user(self, email: str, password: str = None, username: str = None) -> Dict[str, Any]:
        """创建用户"""
        data = {"email": email}
        if password:
            data["password"] = password
        if username:
            data["username"] = username
        
        response = requests.post(f"{self.base_url}/api/users", json=data)
        response.raise_for_status()
        return response.json()
    
    def get_user(self, email: str) -> Dict[str, Any]:
        """获取用户信息"""
        response = requests.get(f"{self.base_url}/api/users/{email}")
        response.raise_for_status()
        return response.json()
    
    def reset_password(self, email: str, new_password: str = None) -> Dict[str, Any]:
        """重置密码"""
        data = {"email": email}
        if new_password:
            data["new_password"] = new_password
        
        response = requests.put(f"{self.base_url}/api/users/password", json=data)
        response.raise_for_status()
        return response.json()
    
    def delete_user(self, email: str) -> Dict[str, Any]:
        """删除用户"""
        response = requests.delete(f"{self.base_url}/api/users/{email}")
        response.raise_for_status()
        return response.json()
    
    def create_project(
        self,
        owner_email: str,
        cpu_limit: str = None,
        memory_limit: str = None,
        gpu_limit: str = None,
        storage_size: str = None
    ) -> Dict[str, Any]:
        """创建项目"""
        data = {"owner_email": owner_email}
        if cpu_limit:
            data["cpu_limit"] = cpu_limit
        if memory_limit:
            data["memory_limit"] = memory_limit
        if gpu_limit:
            data["gpu_limit"] = gpu_limit
        if storage_size:
            data["storage_size"] = storage_size
        
        response = requests.post(f"{self.base_url}/api/projects", json=data)
        response.raise_for_status()
        return response.json()
    
    def get_project(self, profile_name: str) -> Dict[str, Any]:
        """获取项目信息"""
        response = requests.get(f"{self.base_url}/api/projects/{profile_name}")
        response.raise_for_status()
        return response.json()
    
    def get_project_by_email(self, email: str) -> Dict[str, Any]:
        """根据邮箱获取项目"""
        response = requests.get(f"{self.base_url}/api/projects/by-email/{email}")
        response.raise_for_status()
        return response.json()
    
    def update_project(
        self,
        profile_name: str,
        cpu_limit: str = None,
        memory_limit: str = None,
        gpu_limit: str = None,
        storage_size: str = None
    ) -> Dict[str, Any]:
        """更新项目资源"""
        data = {}
        if cpu_limit:
            data["cpu_limit"] = cpu_limit
        if memory_limit:
            data["memory_limit"] = memory_limit
        if gpu_limit:
            data["gpu_limit"] = gpu_limit
        if storage_size:
            data["storage_size"] = storage_size
        
        response = requests.put(f"{self.base_url}/api/projects/{profile_name}", json=data)
        response.raise_for_status()
        return response.json()
    
    def delete_project(self, profile_name: str) -> Dict[str, Any]:
        """删除项目"""
        response = requests.delete(f"{self.base_url}/api/projects/{profile_name}")
        response.raise_for_status()
        return response.json()


def test_user_management():
    """测试用户管理功能"""
    client = KubeflowManagerClient()
    test_email = "testuser@example.com"
    
    print("=" * 60)
    print("测试用户管理功能")
    print("=" * 60)
    
    try:
        # 1. 创建用户（自动生成密码）
        print("\n1. 创建用户（自动生成密码）...")
        user = client.create_user(test_email)
        print(f"✓ 用户创建成功: {user['email']}")
        print(f"  用户名: {user['username']}")
        print(f"  密码: {user['password']}")
        print(f"  登录链接: {user['login_url']}")
        
        # 2. 查询用户
        print("\n2. 查询用户信息...")
        user_info = client.get_user(test_email)
        print(f"✓ 查询成功: {user_info['email']}, 用户名: {user_info['username']}")
        
        # 3. 重置密码
        print("\n3. 重置密码...")
        reset_result = client.reset_password(test_email, "newpassword123")
        print(f"✓ 密码重置成功")
        print(f"  新密码: {reset_result['password']}")
        
        # 4. 删除用户
        print("\n4. 删除用户...")
        delete_result = client.delete_user(test_email)
        print(f"✓ 用户删除成功: {delete_result['message']}")
        
        print("\n✓ 所有用户管理测试通过！")
        
    except requests.exceptions.HTTPError as e:
        print(f"✗ 测试失败: {e}")
        print(f"  响应: {e.response.text}")
    except Exception as e:
        print(f"✗ 测试失败: {e}")


def test_project_management():
    """测试项目管理功能"""
    client = KubeflowManagerClient()
    test_email = "projectowner@example.com"
    
    print("\n" + "=" * 60)
    print("测试项目管理功能")
    print("=" * 60)
    
    try:
        # 1. 先创建用户
        print("\n1. 创建用户...")
        user = client.create_user(test_email)
        print(f"✓ 用户创建成功: {user['email']}")
        
        # 2. 创建项目
        print("\n2. 创建项目...")
        project = client.create_project(
            owner_email=test_email,
            cpu_limit="4",
            memory_limit="8",
            gpu_limit="1",
            storage_size="20"
        )
        print(f"✓ 项目创建成功")
        print(f"  项目名: {project['name']}")
        print(f"  所有者: {project['owner']}")
        print(f"  资源配额: {json.dumps(project['resources'], indent=2)}")
        
        profile_name = project['name']
        
        # 3. 查询项目
        print("\n3. 查询项目...")
        project_info = client.get_project(profile_name)
        print(f"✓ 查询成功: {project_info['name']}")
        
        # 4. 根据邮箱查询项目
        print("\n4. 根据邮箱查询项目...")
        project_by_email = client.get_project_by_email(test_email)
        print(f"✓ 查询成功: {project_by_email['name']}")
        
        # 5. 更新项目资源
        print("\n5. 更新项目资源...")
        updated_project = client.update_project(
            profile_name=profile_name,
            cpu_limit="8",
            memory_limit="16"
        )
        print(f"✓ 资源更新成功")
        print(f"  新资源配额: {json.dumps(updated_project['resources'], indent=2)}")
        
        # 6. 删除项目
        print("\n6. 删除项目...")
        delete_result = client.delete_project(profile_name)
        print(f"✓ 项目删除成功: {delete_result['message']}")
        
        # 7. 删除用户
        print("\n7. 删除用户...")
        client.delete_user(test_email)
        print(f"✓ 用户删除成功")
        
        print("\n✓ 所有项目管理测试通过！")
        
    except requests.exceptions.HTTPError as e:
        print(f"✗ 测试失败: {e}")
        print(f"  响应: {e.response.text}")
    except Exception as e:
        print(f"✗ 测试失败: {e}")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Kubeflow 用户管理平台 API 测试")
    print("=" * 60)
    
    # 检查服务是否运行
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"✓ 服务状态: {response.json()['status']}")
    except Exception as e:
        print(f"✗ 服务未启动，请先运行: python main.py")
        return
    
    # 运行测试
    test_user_management()
    test_project_management()
    
    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

