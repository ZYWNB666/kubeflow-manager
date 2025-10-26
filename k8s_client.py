import base64
import os
import re
import yaml
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from typing import Optional, Dict, Any
from config import settings


class KubernetesClient:
    """Kubernetes 客户端封装"""
    
    def __init__(self):
        """初始化 Kubernetes 客户端"""
        try:
            if settings.kubeconfig_path:
                config.load_kube_config(config_file=settings.kubeconfig_path)
            else:
                config.load_incluster_config()
        except Exception:
            config.load_kube_config()
        
        self.core_v1 = client.CoreV1Api()
        self.custom_objects = client.CustomObjectsApi()
        self.apps_v1 = client.AppsV1Api()
    
    def get_configmap(self, name: str, namespace: str) -> Optional[client.V1ConfigMap]:
        """获取 ConfigMap"""
        try:
            return self.core_v1.read_namespaced_config_map(name, namespace)
        except ApiException as e:
            if e.status == 404:
                return None
            raise
    
    def update_configmap(self, name: str, namespace: str, configmap: client.V1ConfigMap) -> client.V1ConfigMap:
        """更新 ConfigMap"""
        return self.core_v1.replace_namespaced_config_map(name, namespace, configmap)
    
    def get_secret(self, name: str, namespace: str) -> Optional[client.V1Secret]:
        """获取 Secret"""
        try:
            return self.core_v1.read_namespaced_secret(name, namespace)
        except ApiException as e:
            if e.status == 404:
                return None
            raise
    
    def patch_secret(self, name: str, namespace: str, data: Dict[str, str]) -> client.V1Secret:
        """更新 Secret"""
        body = {"data": data}
        return self.core_v1.patch_namespaced_secret(name, namespace, body)
    
    def create_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建 Kubeflow Profile"""
        return self.custom_objects.create_cluster_custom_object(
            group="kubeflow.org",
            version="v1beta1",
            plural="profiles",
            body=profile_data
        )
    
    def get_profile(self, name: str) -> Optional[Dict[str, Any]]:
        """获取 Kubeflow Profile"""
        try:
            return self.custom_objects.get_cluster_custom_object(
                group="kubeflow.org",
                version="v1beta1",
                plural="profiles",
                name=name
            )
        except ApiException as e:
            if e.status == 404:
                return None
            raise
    
    def update_profile(self, name: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新 Kubeflow Profile"""
        return self.custom_objects.replace_cluster_custom_object(
            group="kubeflow.org",
            version="v1beta1",
            plural="profiles",
            name=name,
            body=profile_data
        )
    
    def delete_profile(self, name: str) -> Dict[str, Any]:
        """删除 Kubeflow Profile"""
        return self.custom_objects.delete_cluster_custom_object(
            group="kubeflow.org",
            version="v1beta1",
            plural="profiles",
            name=name
        )
    
    def create_authorization_policy(self, namespace: str) -> Dict[str, Any]:
        """创建 Istio AuthorizationPolicy"""
        policy_data = {
            "apiVersion": "security.istio.io/v1beta1",
            "kind": "AuthorizationPolicy",
            "metadata": {
                "name": "allow-all",
                "namespace": namespace
            },
            "spec": {
                "action": "ALLOW",
                "rules": [{}]
            }
        }
        
        return self.custom_objects.create_namespaced_custom_object(
            group="security.istio.io",
            version="v1beta1",
            namespace=namespace,
            plural="authorizationpolicies",
            body=policy_data
        )
    
    def restart_deployment(self, name: str, namespace: str) -> client.V1Deployment:
        """重启 Deployment"""
        deployment = self.apps_v1.read_namespaced_deployment(name, namespace)
        
        if deployment.spec.template.metadata.annotations is None:
            deployment.spec.template.metadata.annotations = {}
        
        from datetime import datetime
        deployment.spec.template.metadata.annotations['kubectl.kubernetes.io/restartedAt'] = datetime.utcnow().isoformat()
        
        return self.apps_v1.patch_namespaced_deployment(name, namespace, deployment)
    
    def namespace_exists(self, namespace: str) -> bool:
        """检查命名空间是否存在"""
        try:
            self.core_v1.read_namespace(namespace)
            return True
        except ApiException as e:
            if e.status == 404:
                return False
            raise


k8s_client = KubernetesClient()

