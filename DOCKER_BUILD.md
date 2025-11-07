# Docker 镜像构建指南

## 概述

本项目提供了自动化的 Docker **多架构**镜像构建和推送脚本，可将应用打包成支持 **amd64** 和 **arm64** 架构的 Docker 镜像并推送到腾讯云镜像仓库。

**支持的架构：**
- ✅ linux/amd64 (x86_64) - 适用于 Intel/AMD 处理器
- ✅ linux/arm64 (aarch64) - 适用于 ARM 处理器（如树莓派、Apple Silicon Mac 等）

## 文件说明

- `Dockerfile` - Docker 镜像定义文件
- `build.sh` - 镜像构建和推送脚本
- `.dockerignore` - Docker 构建时忽略的文件列表

## 快速开始

### 前置要求

- **Docker 19.03+** （需支持 buildx）
- **Git**

检查 Docker Buildx 是否可用：
```bash
docker buildx version
```

如果未安装 buildx，请升级 Docker 到最新版本。

### 1. 登录腾讯云镜像仓库

#### 方式一：手动登录（推荐用于开发环境）

```bash
docker login ccr.ccs.tencentyun.com
```

输入你的腾讯云镜像仓库用户名和密码。

#### 方式二：使用环境变量登录（推荐用于 CI/CD）

```bash
export DOCKER_USERNAME="your_username"
export DOCKER_PASSWORD="your_password"
```

### 2. 执行构建脚本

```bash
./build.sh
```

脚本会自动完成以下操作：
1. ✅ 检查依赖（Docker、Git）
2. 📋 获取版本信息（Git SHA、Tag）
3. 🔐 登录镜像仓库
4. 🔨 构建 Docker 镜像（支持多标签）
5. 📤 推送镜像到腾讯云
6. 📊 显示镜像信息

### 3. 查看帮助

```bash
./build.sh --help
```

## 镜像标签说明

每次构建会生成 3 个标签：

1. **版本标签** - `ccr.ccs.tencentyun.com/cone387/quark-auto-save:<git-tag>`
   - 例如：`v1.0.0`
   - 用于生产环境的稳定版本

2. **提交标签** - `ccr.ccs.tencentyun.com/cone387/quark-auto-save:<git-sha-short>`
   - 例如：`a1b2c3d`
   - 用于追踪具体的代码提交

3. **最新标签** - `ccr.ccs.tencentyun.com/cone387/quark-auto-save:latest`
   - 始终指向最新构建的镜像

## 高级用法

### 构建后清理本地镜像

```bash
./build.sh --cleanup
```

这会在推送成功后自动删除本地构建的镜像，节省磁盘空间。

### 使用环境变量一键构建

```bash
DOCKER_USERNAME=myuser DOCKER_PASSWORD=mypass ./build.sh
```

### 在 GitHub Actions 中使用

```yaml
- name: Build and Push Docker Image
  env:
    DOCKER_USERNAME: ${{ secrets.DOCKER_USERNAME }}
    DOCKER_PASSWORD: ${{ secrets.DOCKER_PASSWORD }}
  run: |
    chmod +x build.sh
    ./build.sh
```

## 拉取和运行镜像

### 拉取镜像

```bash
# 拉取最新版本
docker pull ccr.ccs.tencentyun.com/cone387/quark-auto-save:latest

# 拉取指定版本
docker pull ccr.ccs.tencentyun.com/cone387/quark-auto-save:v1.0.0
```

### 运行容器

```bash
docker run -d \
  --name quark-auto-save \
  -p 5005:5005 \
  -e WEBUI_USERNAME=admin \
  -e WEBUI_PASSWORD=admin123 \
  -e QUARK_COOKIE="your_cookie" \
  -e ARK_API_KEY="your_api_key" \
  -e ARK_MODEL_ID="your_model_id" \
  -v /path/to/config:/app/config \
  -v /etc/localtime:/etc/localtime:ro \
  ccr.ccs.tencentyun.com/cone387/quark-auto-save:latest
```

### 使用 Docker Compose

```yaml
version: '3.8'

services:
  quark-auto-save:
    image: ccr.ccs.tencentyun.com/cone387/quark-auto-save:latest
    container_name: quark-auto-save
    ports:
      - "5005:5005"
    environment:
      - WEBUI_USERNAME=admin
      - WEBUI_PASSWORD=admin123
      - QUARK_COOKIE=your_cookie
      - ARK_API_KEY=your_api_key
      - ARK_MODEL_ID=your_model_id
    volumes:
      - ./config:/app/config
      - /etc/localtime:/etc/localtime:ro
    restart: unless-stopped
```

## 构建过程说明

### 构建参数

脚本会自动传递以下构建参数到 Docker：

- `BUILD_SHA` - 完整的 Git commit SHA
- `BUILD_TAG` - Git tag 或 "latest"

这些参数可以在应用中通过环境变量访问，用于版本追踪。

### 平台支持

**默认构建多架构镜像**，支持以下平台：
- `linux/amd64` - Intel/AMD x86_64 处理器
- `linux/arm64` - ARM 64位处理器（Apple Silicon、树莓派等）

Docker 会自动为你的平台选择正确的镜像架构。你可以使用以下命令查看镜像支持的所有架构：

```bash
docker buildx imagetools inspect ccr.ccs.tencentyun.com/cone387/quark-auto-save:latest
```

## 故障排除

### 问题：无法连接到 Docker daemon

**解决方案**：确保 Docker 服务正在运行

```bash
# macOS
open -a Docker

# Linux
sudo systemctl start docker
```

### 问题：登录失败 "unauthorized"

**解决方案**：检查用户名和密码是否正确，或检查是否有权限推送到该命名空间

### 问题：构建失败 "no space left on device"

**解决方案**：清理 Docker 缓存

```bash
docker system prune -a
```

### 问题：推送超时

**解决方案**：检查网络连接，或使用代理

```bash
# 设置代理
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
```

### 问题：buildx 构建失败 "multiple platforms feature is currently not supported"

**解决方案**：确保使用 docker-container 驱动的 builder

```bash
# 删除旧的 builder
docker buildx rm multiarch-builder

# 重新运行脚本，会自动创建正确的 builder
./build.sh
```

### 问题：QEMU 模拟器未安装（ARM 架构构建失败）

**解决方案**：安装 QEMU 用户模式模拟器

```bash
# macOS
brew install qemu

# Linux (Ubuntu/Debian)
sudo apt-get install qemu-user-static

# 然后重新运行构建
docker run --privileged --rm tonistiigi/binfmt --install all
```

### 问题：查看镜像架构时提示 "manifest unknown"

**解决方案**：确保镜像已成功推送到仓库

```bash
# 检查构建日志，确认推送步骤成功
# 等待几分钟后重试查看
docker buildx imagetools inspect ccr.ccs.tencentyun.com/cone387/quark-auto-save:latest
```

## 最佳实践

1. **版本管理**
   - 每次发布前打 Git tag
   - 使用语义化版本号（如 v1.2.3）

2. **安全**
   - 不要在代码中硬编码密码
   - 使用环境变量或 Secrets 管理敏感信息
   - 定期更新基础镜像

3. **镜像优化**
   - 使用 `.dockerignore` 减小镜像大小
   - 使用 Alpine 作为基础镜像
   - 合并 RUN 命令减少层数

4. **CI/CD 集成**
   - 在 CI/CD 流程中自动构建和推送
   - 为不同分支使用不同的标签策略
   - 构建前运行测试

## 相关链接

- [腾讯云容器镜像服务文档](https://cloud.tencent.com/document/product/1141)
- [Docker 官方文档](https://docs.docker.com/)
- [Dockerfile 最佳实践](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)

## 技术支持

如遇到问题，请查看：
- 项目 Issue：提交问题和建议
- 构建日志：`build.sh` 会输出详细的构建信息
