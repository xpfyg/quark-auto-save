# Docker Compose 部署指南

本文档介绍如何使用 Docker Compose 快速部署夸克自动转存系统。

## 服务说明

该 Docker Compose 配置包含两个服务：

1. **quark-auto-save** - 夸克自动转存服务
   - 镜像：`ccr.ccs.tencentyun.com/cone387/quark-auto-save:latest`
   - 本地端口：8887
   - 容器端口：5005
   - 功能：自动签到、转存、重命名、通知、Emby刷新等

2. **pansou-web** - 网盘资源搜索服务
   - 镜像：`ghcr.io/fish2018/pansou-web:latest`
   - 本地端口：8888
   - 容器端口：80
   - 功能：提供网盘资源搜索API

两个服务通过 `quark-network` 网络连接，可以相互访问。

## 快速开始

### 1. 准备配置文件

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件，填入你的实际配置
vim .env
```

**必需配置**：
- `QUARK_COOKIE` - 夸克网盘Cookie（必需）
- `WEBUI_USERNAME` - WebUI登录用户名
- `WEBUI_PASSWORD` - WebUI登录密码

**可选配置**（根据需要填写）：
- `ARK_API_KEY`、`ARK_MODEL_ID` - 豆包AI配置（自动收集热门电影）
- `TMDB_API_KEY` - TMDB配置（获取电影元数据）
- `DB_*` - 数据库配置（资源管理功能）
- `TELEGRAM_BOT_TOKEN`、`PUSH_KEY` 等 - 推送通知配置

### 2. 创建必要的目录

```bash
# 创建配置和日志目录
mkdir -p config logs temp_posters
```

### 3. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 查看指定服务的日志
docker-compose logs -f quark-auto-save
docker-compose logs -f pansou-web
```

### 4. 访问服务

- **夸克自动转存 WebUI**：http://localhost:8887
- **网盘搜索服务**：http://localhost:8888

## 常用命令

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f [service_name]

# 更新镜像并重启
docker-compose pull
docker-compose up -d

# 进入容器
docker-compose exec quark-auto-save bash
```

## 目录挂载说明

以下目录会挂载到宿主机当前目录：

- `./config` → `/app/config` - 配置文件目录
  - `quark_config.json` - 主配置文件
- `./logs` → `/app/logs` - 日志文件目录
- `./temp_posters` → `/app/temp_posters` - 临时海报目录

## 服务间网络通信

两个服务在同一个 Docker 网络（`quark-network`）中，可以通过**服务名**相互访问：

- `quark-auto-save` 可以通过 `http://pansou-web/api/search` 访问搜索服务
- 在 docker-compose.yml 中已配置环境变量 `SEARCH_API_URL=http://pansou-web/api/search`

## 配置示例

### 最小化配置（.env）

```bash
# 仅需夸克Cookie即可运行基本功能
QUARK_COOKIE=你的完整Cookie

WEBUI_USERNAME=admin
WEBUI_PASSWORD=admin123
```

### 完整配置（.env）

```bash
# WebUI
WEBUI_USERNAME=admin
WEBUI_PASSWORD=admin123

# 夸克Cookie
QUARK_COOKIE=你的完整Cookie

# 豆包AI（自动收集热门电影）
ARK_API_KEY=your_ark_api_key
ARK_MODEL_ID=your_model_id

# TMDB（电影元数据）
TMDB_API_KEY=your_tmdb_api_key

# 数据库（资源管理）
DB_HOST=your_mysql_host
DB_PORT=3306
DB_USERNAME=your_db_user
DB_PASSWORD=your_db_password
DB_DATABASE=your_db_name

# Server酱推送通知
PUSH_KEY=your_server_chan_key

# Telegram Bot推送
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## 故障排除

### 问题：容器启动失败

**解决方案**：检查日志查看错误信息

```bash
docker-compose logs quark-auto-save
```

常见原因：
- Cookie未配置或格式错误
- 端口被占用（8887、8888）
- 目录权限问题

### 问题：无法访问 WebUI

**解决方案**：

1. 检查容器是否正常运行
```bash
docker-compose ps
```

2. 检查端口是否被占用
```bash
# macOS/Linux
lsof -i :8887

# 或使用其他端口，修改 docker-compose.yml
ports:
  - "9999:5005"  # 改用9999端口
```

### 问题：搜索功能无法使用

**解决方案**：确保 pansou-web 服务正常运行

```bash
# 检查服务状态
docker-compose ps pansou-web

# 测试搜索API
curl http://localhost:8888/api/search?keyword=test

# 检查网络连接
docker-compose exec quark-auto-save ping pansou-web
```

### 问题：配置修改后未生效

**解决方案**：重启服务

```bash
# 重启指定服务
docker-compose restart quark-auto-save

# 或完全重建
docker-compose down
docker-compose up -d
```

### 问题：日志文件过大

**解决方案**：配置日志轮转或定期清理

```bash
# 清理日志
rm -rf logs/*.log

# 或在 docker-compose.yml 中配置日志限制
services:
  quark-auto-save:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## 数据持久化

### 配置文件持久化

配置文件通过卷挂载已经持久化到宿主机：

- `./config/quark_config.json` - 主配置文件
- 修改此文件后，在 WebUI 中刷新即可生效

### 数据库持久化（可选）

如果使用数据库功能，建议添加数据库服务到 docker-compose.yml：

```yaml
services:
  mysql:
    image: mysql:8.0
    container_name: quark-mysql
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_PASSWORD}
      MYSQL_DATABASE: ${DB_DATABASE}
    volumes:
      - mysql_data:/var/lib/mysql
    networks:
      - quark-network
    restart: unless-stopped

volumes:
  mysql_data:
```

然后在 .env 中配置：
```bash
DB_HOST=mysql
DB_PORT=3306
DB_USERNAME=root
DB_PASSWORD=your_password
DB_DATABASE=pan_library
```

## 安全建议

1. **修改默认密码**
   - 修改 `WEBUI_USERNAME` 和 `WEBUI_PASSWORD`

2. **保护敏感信息**
   - 不要将 `.env` 文件提交到 Git
   - `.env` 已在 `.gitignore` 中

3. **网络安全**
   - 如果部署在公网，建议使用反向代理（Nginx）并配置HTTPS
   - 限制服务仅监听 127.0.0.1

4. **定期更新镜像**
```bash
docker-compose pull
docker-compose up -d
```

## 多架构支持

镜像支持以下架构：
- ✅ linux/amd64 (x86_64)
- ✅ linux/arm64 (ARM64/aarch64)

Docker 会自动拉取适合当前系统架构的镜像。

## 参考链接

- [项目主页](https://github.com/your-repo)
- [Docker 镜像构建文档](./DOCKER_BUILD.md)
- [完整配置说明](./CLAUDE.md)
