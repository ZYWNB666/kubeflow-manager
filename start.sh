#!/bin/bash

# 启动 Kubeflow Manager API 服务

echo "启动 Kubeflow User Management API..."

# 检查依赖
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到 python3"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
if [ ! -f "venv/.installed" ]; then
    echo "安装依赖..."
    pip install -r requirements.txt
    touch venv/.installed
fi

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "警告：未找到 .env 文件，使用默认配置"
    echo "建议：复制 .env.example 到 .env 并修改配置"
fi

# 启动服务
echo "启动服务..."
python main.py

