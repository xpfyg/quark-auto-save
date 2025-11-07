#!/bin/bash

# 快速构建脚本（仅构建，不推送）
# 用于本地开发和测试

set -e

IMAGE_NAME="quark-auto-save"
TAG="dev"

echo "🔨 开始本地构建..."

docker build -t ${IMAGE_NAME}:${TAG} .

echo "✅ 构建完成！"
echo ""
echo "运行容器："
echo "  docker run -d -v $(pwd)/.env:/app/.env -v $(pwd)/quark_config.json:/app/quark_config.json -v $(pwd)/resource:/app/resource -v $(pwd)/logs:/app/logs  -p 5005:5005 ${IMAGE_NAME}:${TAG}"
echo ""
echo "查看日志："
echo "  docker logs -f \$(docker ps -q --filter ancestor=${IMAGE_NAME}:${TAG})"
