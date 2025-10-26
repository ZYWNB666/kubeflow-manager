#!/bin/bash
# 本脚本用于在 kubeflow 中创建用户，并为其分配命名空间和资源限制
# 使用方法：./create_user.sh <email>
# 需要安装的工具：kubectl、python3、passlib
# 资源限制：CPU、内存、存储、GPU
# 默认资源限制：CPU 2 核、内存 4 GiB、存储 10 GiB、GPU 0
# 资源限制变量参数：CPU_LIMIT、MEM_LIMIT、GPU_LIMIT
# 资源限制参数示例：CPU_LIMIT=2 MEM_LIMIT=4  GPU_LIMIT=0

# 配置命名空间和 ConfigMap 名称
NAMESPACE="auth"
CONFIGMAP_NAME="dex"
SECRET_NAME="dex-passwords"

# 获取用户输入的邮箱
EMAIL="${gmail}"
if [ -z "${EMAIL}" ]; then
  echo "Usage: $0 <email>"
  exit 1
fi

# 提取用户名
USERNAME=$(echo "${EMAIL}" | awk -F '@' '{print $1}')

# 检查命名空间是否存在
if ! kubectl get ns "${NAMESPACE}" > /dev/null 2>&1; then
  echo "Namespace ${NAMESPACE} does not exist. Please create it first."
  exit 1
fi

# 检查 ConfigMap 是否存在
if ! kubectl get cm -n "${NAMESPACE}" "${CONFIGMAP_NAME}" > /dev/null 2>&1; then
  echo "ConfigMap ${CONFIGMAP_NAME} does not exist in namespace ${NAMESPACE}. Please create it first."
  exit 1
fi

# 检查 Secret 是否存在
if ! kubectl get secret -n "${NAMESPACE}" "${SECRET_NAME}" > /dev/null 2>&1; then
  echo "Secret ${SECRET_NAME} does not exist in namespace ${NAMESPACE}. Please create it first."
  exit 1
fi

# 拉取现存的 ConfigMap
kubectl get cm -n "${NAMESPACE}" "${CONFIGMAP_NAME}" -o yaml > original_configmap.yaml

if [ $? -ne 0 ]; then
  echo "Failed to fetch ConfigMap. Please check the namespace and ConfigMap name."
  exit 1
fi

# 使用 Python 生成随机密码、Base64 哈希值和环境变量名
output=$(python3 <<EOF
import os
import base64
from passlib.hash import bcrypt

# 生成随机10位密码
random_password = ''.join(
    chr(os.urandom(1)[0] % 26 + ord('a')) for _ in range(10)
)

# 打印原始密码和大写密码
print(f"Random Password: {random_password}")
print(f"Random Password (Uppercase): {random_password.upper()}")

# 使用 bcrypt 生成哈希
hashed_password = bcrypt.using(rounds=12, ident="2y").hash(random_password)

# 将哈希结果转换为 Base64
hashed_password_base64 = base64.b64encode(hashed_password.encode()).decode()

print(f"Base64 Hashed Password: {hashed_password_base64}")
EOF
)

# 提取生成的密码和哈希值
PASSWD=$(echo "$output" | grep "Random Password:" | awk '{print $3}')
PASSWD_HASH_ENV_NAME=$(echo "$output" | grep "Random Password (Uppercase):" | awk '{print $4}')
PASSWD_BASE64=$(echo "$output" | grep "Base64 Hashed Password:" | awk '{print $4}')

# # 打印生成的结果
# echo "Generated Password: ${PASSWD}"
# echo "Generated Password BASE64: ${PASSWD_BASE64}"
# echo "Generated Password Hash Environment Variable Name: ${PASSWD_HASH_ENV_NAME}"

# 更新 Secret
PATCH_JSON=$(printf '{"data":{"%s":"%s"}}' "USER_${PASSWD_HASH_ENV_NAME}" "${PASSWD_BASE64}")
kubectl patch secret "${SECRET_NAME}" -n "${NAMESPACE}" \
    --type='merge' \
    -p="${PATCH_JSON}" --dry-run=client

if [ $? -ne 0 ]; then
  echo "Failed to patch the secret. Please check the input values."
  exit 1
fi

# 更新 ConfigMap
# 使用sed命令删除多余的行
sed -i '/kubectl.kubernetes.io\/last-applied-configuration/d' original_configmap.yaml
sed -i '/Updated ConfigMap/d' original_configmap.yaml
sed -i '/creationTimestamp:/d' original_configmap.yaml
sed -i '/resourceVersion:/d' original_configmap.yaml
sed -i '/selfLink:/d' original_configmap.yaml
sed -i '/uid:/d' original_configmap.yaml
sed -i '/\\n/d' original_configmap.yaml

sed -i "/staticPasswords:/a\    - email: ${EMAIL}\n      hashFromEnv: USER_${PASSWD_HASH_ENV_NAME}\n      username: ${USERNAME}" original_configmap.yaml

echo "Updated ConfigMap:"
# cat original_configmap.yaml

# 如果需要，可以自动应用更新后的 ConfigMap
kubectl apply -f original_configmap.yaml --dry-run=client
if [ $? -ne 0 ]; then
  echo "Failed to apply the updated ConfigMap. Please check the input values."
  exit 1
fi

kubectl patch secret "${SECRET_NAME}" -n "${NAMESPACE}" \
    --type='merge' \
    -p="${PATCH_JSON}"

kubectl apply -f original_configmap.yaml

# 新增用户命名空间

PROFILE_NAME=$(echo "${EMAIL}" | sed 's/[.@]/-/g')

# 创建命名空间和资源限制
if [ -z "${CPU_LIMIT}" ]; then
  CPU_LIMIT=2
fi
if [ -z "${MEM_LIMIT}" ]; then
  MEM_LIMIT=4
fi
if [ -z "${L4_GPU_LIMIT}" ]; then
  L4_GPU_LIMIT=0
fi
# if [ -z "${PVC_NUMBER}" ]; then
#   PVC_NUMBER="1"
# fi
if [ -z "${STORAGE_SIZE}" ]; then
  STORAGE_SIZE="10"
fi

kubectl apply -f - <<EOF
apiVersion: v1
data:
  profile-name: ${PROFILE_NAME}
  user: ${EMAIL}
kind: ConfigMap
metadata:
  name: default-install-config-9h2h2b6hbk
---
apiVersion: kubeflow.org/v1beta1
kind: Profile
metadata:
  name: ${PROFILE_NAME}
spec:
  owner:
    kind: User
    name: ${EMAIL}
  resourceQuotaSpec:    # resource quota can be set optionally
    hard:
      cpu: "${CPU_LIMIT}"
      memory: "${MEM_LIMIT}Gi"
      # requests.nvidia.com/l4: "${L4_GPU_LIMIT}"
      requests.nvidia.com/gpu: "${L4_GPU_LIMIT}"
      # persistentvolumeclaims: "${PVC_NUMBER}"
      requests.storage: "${STORAGE_SIZE}Gi"
EOF
if [ $? -ne 0 ]; then
  echo "Failed to create user namespace. Please check the input values."
  exit 1
fi
echo "User namespace ${PROFILE_NAME} created successfully."

# 重启 Dex
kubectl rollout restart deployment dex -n auth
if [ $? -ne 0 ]; then
  echo "Failed to restart Dex deployment. Please check the input values."
  exit 1
fi
echo "Dex deployment restarted successfully."

# # sleep 5
# sleep 5
# # 创建命名空间和资源限制
# if [ -z "${CPU_LIMIT}" ]; then
#   CPU_LIMIT="2"
# fi
# if [ -z "${MEM_LIMIT}" ]; then
#   MEM_LIMIT="4"
# fi
# if [ -z "${GPU_LIMIT}" ]; then
#   GPU_LIMIT="0"
# fi
# kubectl apply -f - <<EOF
# apiVersion: v1
# kind: LimitRange
# metadata:
#   name: profile-limit-range
#   namespace: ${PROFILE_NAME}
# spec:
#   limits:
#   - default:
#       cpu: 200m
#       memory: 500Mi
#       nvidia.com/gpu: "0"
#     defaultRequest:
#       cpu: 20m
#       memory: 50Mi
#       nvidia.com/gpu: "0"
#     type: Container
# ---
# apiVersion: v1
# kind: ResourceQuota
# metadata:
#   name: profile-resource-quota
#   namespace: ${PROFILE_NAME}
# spec:
#   hard:
#     limits.cpu: "${CPU_LIMIT}"
#     limits.memory: ${MEM_LIMIT}Gi
#     requests.nvidia.com/gpu: "${GPU_LIMIT}"
# EOF

# 创建 AuthorizationPolicy 文件 允许所有流量
kubectl apply -f - <<EOF
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: allow-all
  namespace: ${PROFILE_NAME}
spec:
  action: ALLOW
  rules:
    - {}
EOF

# 清理临时文件
rm -f original_configmap.yaml
echo -e "清理临时文件\n\n\n\n"
echo " 登录链接：https://kubeflow.id.gametech.garenanow.com/?ns=${PROFILE_NAME}"
echo " 用户名：${EMAIL}"
echo " 密码：${PASSWD}"


