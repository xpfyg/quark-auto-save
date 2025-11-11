#!/bin/bash

# Docker 镜像构建和推送脚本
# 用于将项目打包成 Docker 镜像并推送到腾讯云镜像仓库

set -e  # 遇到错误立即退出

# ============================================================================
# 配置变量
# ============================================================================

# 镜像仓库地址
REGISTRY="ccr.ccs.tencentyun.com"
# 命名空间
NAMESPACE="cone387"
# 镜像名称
IMAGE_NAME="quark-auto-save"
# 完整镜像地址
IMAGE_PATH="${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# 辅助函数
# ============================================================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# ============================================================================
# 检查依赖
# ============================================================================

check_dependencies() {
    log_step "检查依赖..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装或未添加到 PATH"
        exit 1
    fi

    if ! command -v git &> /dev/null; then
        log_error "Git 未安装或未添加到 PATH"
        exit 1
    fi

    # 检查 docker buildx 是否可用
    if ! docker buildx version &> /dev/null; then
        log_error "Docker Buildx 未安装或不可用"
        log_info "请升级到 Docker 19.03+ 或安装 buildx 插件"
        exit 1
    fi

    log_info "依赖检查通过"
}

# ============================================================================
# 设置 buildx 构建器
# ============================================================================

setup_buildx() {
    log_step "设置 Docker Buildx..."

    # 创建并使用新的 builder 实例（如果不存在）
    if ! docker buildx inspect multiarch-builder &> /dev/null; then
        log_info "创建多架构构建器: multiarch-builder"
        docker buildx create --name multiarch-builder --driver docker-container --use
    else
        log_info "使用现有构建器: multiarch-builder"
        docker buildx use multiarch-builder
    fi

    # 启动构建器
    docker buildx inspect --bootstrap

    log_info "Buildx 设置完成"
}

# ============================================================================
# 获取版本信息
# ============================================================================

get_version_info() {
    log_step "获取版本信息..."

    # 获取 git commit SHA
    BUILD_SHA=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    BUILD_SHA_SHORT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

    # 获取 git tag
    BUILD_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "latest")

    # 获取当前分支
    GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

    # 获取当前时间戳
    BUILD_TIME=$(date '+%Y%m%d%H%M%S')

    log_info "Git SHA: ${BUILD_SHA_SHORT}"
    log_info "Git Tag: ${BUILD_TAG}"
    log_info "Git Branch: ${GIT_BRANCH}"
    log_info "Build Time: ${BUILD_TIME}"
}

# ============================================================================
# 登录镜像仓库
# ============================================================================

docker_login() {
    log_step "登录腾讯云镜像仓库..."

    if [ -z "${DOCKER_USERNAME}" ] || [ -z "${DOCKER_PASSWORD}" ]; then
        log_warn "未设置环境变量 DOCKER_USERNAME 或 DOCKER_PASSWORD"
        log_info "请手动登录: docker login ${REGISTRY}"

        if ! docker login ${REGISTRY}; then
            log_error "登录失败"
            exit 1
        fi
    else
        log_info "使用环境变量登录"
        echo "${DOCKER_PASSWORD}" | docker login ${REGISTRY} --username "${DOCKER_USERNAME}" --password-stdin
    fi

    log_info "登录成功"
}

# ============================================================================
# 构建镜像
# ============================================================================

build_image() {
    log_step "开始构建多架构 Docker 镜像..."

    # 定义镜像标签
    TAGS=(
        "${IMAGE_PATH}:${BUILD_TAG}"
        "${IMAGE_PATH}:${BUILD_SHA_SHORT}"
        "${IMAGE_PATH}:latest"
    )

    # 构建标签参数
    TAG_ARGS=""
    for tag in "${TAGS[@]}"; do
        TAG_ARGS="${TAG_ARGS} -t ${tag}"
    done

    log_info "目标架构: linux/amd64, linux/arm64"
    log_info "镜像标签: ${TAGS[@]}"

    # 使用 buildx 构建多架构镜像并推送
    docker buildx build \
        ${TAG_ARGS} \
        --build-arg BUILD_SHA="${BUILD_SHA}" \
        --build-arg BUILD_TAG="${BUILD_TAG}" \
        --platform linux/amd64,linux/arm64 \
        --pull=false \
        --push \
        -f Dockerfile \
        .

    if [ $? -eq 0 ]; then
        log_info "多架构镜像构建并推送成功"
    else
        log_error "镜像构建失败"
        exit 1
    fi
}

# ============================================================================
# 推送镜像（使用 buildx 时此步骤已在构建中完成）
# ============================================================================

push_image() {
    log_step "镜像已在构建过程中推送完成"
    log_info "支持的架构: linux/amd64, linux/arm64"
}

# ============================================================================
# 清理本地镜像（可选）
# ============================================================================

cleanup_images() {
    if [ "${CLEANUP}" = "true" ]; then
        log_step "清理 buildx 缓存..."

        # 清理 buildx 缓存
        docker buildx prune -f

        log_info "清理完成"
    else
        log_info "提示: 使用 'docker buildx prune' 可清理构建缓存"
    fi
}

# ============================================================================
# 显示镜像信息
# ============================================================================

show_image_info() {
    log_step "镜像信息："
    echo ""
    echo "==========================================="
    echo "  多架构镜像已成功构建并推送"
    echo "==========================================="
    echo ""
    echo "🏗️  支持架构："
    echo "   • linux/amd64 (x86_64)"
    echo "   • linux/arm64 (ARM64/aarch64)"
    echo ""
    echo "📦 镜像地址："
    for tag in "${TAGS[@]}"; do
        echo "   ${tag}"
    done
    echo ""
    echo "🚀 使用方法："
    echo "   # 拉取镜像（自动选择架构）"
    echo "   docker pull ${IMAGE_PATH}:latest"
    echo ""
    echo "   # 运行容器"
    echo "   docker run -d -p 5005:5005 ${IMAGE_PATH}:latest"
    echo ""
    echo "   # 查看镜像支持的架构"
    echo "   docker buildx imagetools inspect ${IMAGE_PATH}:latest"
    echo ""
    echo "==========================================="
}

# ============================================================================
# 主函数
# ============================================================================

main() {
    echo ""
    echo "==========================================="
    echo "  Quark Auto Save - 多架构镜像构建"
    echo "==========================================="
    echo ""

    # 检查依赖
    check_dependencies

    # 获取版本信息
    get_version_info

    # 设置 buildx
    setup_buildx

    # 登录镜像仓库
    docker_login

    # 构建并推送镜像（buildx 会同时完成构建和推送）
    build_image

    # 确认推送完成
    push_image

    # 清理构建缓存（可选）
    cleanup_images

    # 显示镜像信息
    show_image_info

    log_info "✅ 所有操作完成"
}

# ============================================================================
# 执行
# ============================================================================

# 显示帮助信息
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    echo "使用方法: ./build.sh [选项]"
    echo ""
    echo "功能: 构建多架构 Docker 镜像并推送到腾讯云镜像仓库"
    echo ""
    echo "支持架构:"
    echo "  • linux/amd64 (x86_64)"
    echo "  • linux/arm64 (ARM64/aarch64)"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示帮助信息"
    echo "  --cleanup      构建后清理 buildx 缓存"
    echo ""
    echo "环境变量:"
    echo "  DOCKER_USERNAME  腾讯云镜像仓库用户名"
    echo "  DOCKER_PASSWORD  腾讯云镜像仓库密码"
    echo ""
    echo "依赖:"
    echo "  • Docker 19.03+ (需支持 buildx)"
    echo "  • Git"
    echo ""
    echo "示例:"
    echo "  ./build.sh"
    echo "  ./build.sh --cleanup"
    echo "  DOCKER_USERNAME=xxx DOCKER_PASSWORD=xxx ./build.sh"
    echo ""
    echo "查看镜像支持的架构:"
    echo "  docker buildx imagetools inspect ccr.ccs.tencentyun.com/cone387/quark-auto-save:latest"
    exit 0
fi

# 解析参数
if [ "$1" = "--cleanup" ]; then
    CLEANUP="true"
fi

# 执行主函数
main
