# 资源介绍页生成系统

## 功能概述

这是一个完整的资源介绍页生成系统，支持：

- ✅ 从数据库自动生成 SEO 优化的资源介绍页面
- ✅ 自动生成 sitemap.xml 和 robots.txt
- ✅ 自动提交到 GitHub Pages
- ✅ 自动提交百度收录
- ✅ 点击统计和数据分析
- ✅ 结构化数据（Schema.org JSON-LD）
- ✅ Open Graph 和 Twitter Card 支持

## 文件结构

```
quark-auto-save/
├── generate_pages.py           # 主生成脚本
├── templates/
│   └── resource_page.md        # Markdown 模板
├── public/templates/
│   └── stats.html              # 数据统计页面
├── run.py                      # Flask 应用（含统计 API）
└── .github/workflows/
    └── generate-pages.yml      # GitHub Actions 自动化
```

## 快速开始

### 1. 环境变量配置

在 `.env` 文件中配置以下环境变量：

```bash
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USERNAME=your_username
DB_PASSWORD=your_password
DB_DATABASE=your_database

# 站点配置
SITE_URL=https://yourdomain.com
PAGES_OUTPUT_DIR=./docs/resources
SITEMAP_DIR=./docs

# 百度推送（可选）
BAIDU_PUSH_TOKEN=your_baidu_token
```

### 2. 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 生成所有资源页面
python3 generate_pages.py

# 只生成10个页面（测试用）
python3 generate_pages.py --limit 10

# 不推送到 GitHub
python3 generate_pages.py --no-push

# 不提交百度收录
python3 generate_pages.py --no-baidu

# 指定输出目录
python3 generate_pages.py --output ./custom_output --sitemap-dir ./custom_sitemap
```

### 3. 启动 Web 服务

```bash
# 启动 Flask 应用
python3 run.py

# 访问管理后台
open http://localhost:5005

# 访问数据统计页面
open http://localhost:5005/stats
```

## 功能详解

### 📄 页面生成

#### SEO 优化

每个生成的页面都包含完整的 SEO 元数据：

```markdown
---
title: 资源名称 - 免费夸克网盘资源分享
description: SEO 优化的描述（150字以内）
keywords: 资源名称,分类,网盘类型,免费下载,在线观看
og:title: Open Graph 标题
og:description: Open Graph 描述
og:image: TMDB 海报图片
twitter:card: Twitter Card 类型
---
```

#### 结构化数据（JSON-LD）

页面包含 Schema.org 结构化数据，帮助搜索引擎理解内容：

```json
{
  "@context": "https://schema.org",
  "@type": "Movie",  // 或 TVSeries、MediaObject
  "name": "资源名称",
  "description": "资源描述",
  "image": "海报URL",
  "datePublished": "发布年份",
  "url": "页面URL",
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "CNY"
  }
}
```

#### 页面优先级计算

系统根据以下因素自动计算页面优先级（0.0-1.0）：

- 浏览量和点击量（越高优先级越高）
- 更新时间（最近7天的资源提高优先级）

### 🗺️ Sitemap 生成

#### sitemap.xml

自动生成符合 Google 标准的 sitemap.xml：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://yourdomain.com/resources/resource-1-name.html</loc>
    <lastmod>2025-01-12</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>
  <!-- 更多页面... -->
</urlset>
```

#### robots.txt

自动生成 robots.txt 文件：

```
User-agent: *
Allow: /

Sitemap: https://yourdomain.com/sitemap.xml

Disallow: /api/
Disallow: /admin/
Disallow: /login

Crawl-delay: 1
```

### 📊 数据统计

#### 点击统计 API

- `POST /api/track_click/<resource_id>` - 记录点击
- `POST /api/track_view/<resource_id>` - 记录浏览
- `GET /link/<resource_id>` - 跳转并统计

#### 统计数据 API

- `GET /api/stats/overview` - 总览统计
- `GET /api/stats/hot_resources` - 热门资源
- `GET /api/stats/category` - 分类统计
- `GET /api/stats/drive_type` - 网盘类型统计

#### 数据统计页面

访问 `/stats` 查看可视化数据统计：

- 总资源数、有效资源数
- 总浏览量、总点击量
- 热门资源排行榜
- 分类和网盘类型分布

### 🚀 自动化部署

#### GitHub Actions

`.github/workflows/generate-pages.yml` 配置了自动化流程：

- 每天凌晨 2 点自动运行
- 可手动触发
- 代码变更时自动运行
- 自动部署到 GitHub Pages

#### 配置 GitHub Secrets

在 GitHub 仓库的 Settings > Secrets 中添加：

- `DB_HOST` - 数据库主机
- `DB_PORT` - 数据库端口
- `DB_USERNAME` - 数据库用户名
- `DB_PASSWORD` - 数据库密码
- `DB_DATABASE` - 数据库名
- `SITE_URL` - 网站 URL
- `BAIDU_PUSH_TOKEN` - 百度推送 Token（可选）

### 🔍 SEO 最佳实践

#### 1. 页面标题优化

格式：`资源名称 - 免费网盘类型资源分享`

示例：`新世纪福音战士 - 免费夸克网盘资源分享`

#### 2. 描述优化

- 长度控制在 150-160 字符
- 包含主要关键词
- 描述清晰，吸引点击

#### 3. 关键词策略

- 资源名称
- 分类（电影、剧集等）
- 网盘类型
- 通用词（免费下载、在线观看）
- TMDB 标题和年份

#### 4. 图片优化

- 使用 TMDB 高质量海报
- Alt 属性包含资源名称
- 支持 Open Graph 图片

#### 5. 内部链接

- 相关推荐链接
- 分类页面链接
- 面包屑导航

### 📈 提交到搜索引擎

#### Google Search Console

1. 访问 [Google Search Console](https://search.google.com/search-console)
2. 添加你的网站
3. 提交 sitemap：`https://yourdomain.com/sitemap.xml`

#### 百度搜索资源平台

系统自动提交，无需手动操作（需配置 `BAIDU_PUSH_TOKEN`）

#### Bing Webmaster Tools

1. 访问 [Bing Webmaster Tools](https://www.bing.com/webmasters)
2. 添加你的网站
3. 提交 sitemap：`https://yourdomain.com/sitemap.xml`

## API 文档

### 统计 API

#### 记录点击

```http
POST /api/track_click/{resource_id}
```

响应：
```json
{
  "success": true,
  "share_count": 10
}
```

#### 获取热门资源

```http
GET /api/stats/hot_resources?limit=20&days=30
```

响应：
```json
{
  "success": true,
  "days": 30,
  "data": [
    {
      "id": 1,
      "drama_name": "资源名称",
      "share_count": 100,
      "view_count": 500,
      "total_count": 600
    }
  ]
}
```

## 常见问题

### Q: 如何修改页面模板？

A: 编辑 `templates/resource_page.md` 文件，使用 Jinja2 语法。

### Q: 如何自定义 SEO 规则？

A: 修改 `generate_pages.py` 中的以下方法：
- `_generate_seo_description()` - 描述生成
- `_generate_keywords()` - 关键词生成
- `_calculate_priority()` - 优先级计算

### Q: sitemap.xml 太大怎么办？

A: 考虑使用 sitemap 索引文件，将 sitemap 拆分成多个文件。

### Q: 如何禁用某些页面的索引？

A: 在页面 frontmatter 中添加 `robots: noindex`。

## 性能优化

### 1. 图片优化

- 使用 CDN 加速 TMDB 图片
- 考虑使用 WebP 格式
- 添加懒加载

### 2. 缓存策略

- 静态资源设置长期缓存
- HTML 页面设置适当缓存
- 使用 CDN

### 3. 页面压缩

- 启用 Gzip/Brotli 压缩
- 压缩 HTML、CSS、JS

## 许可证

MIT License

## 支持

如有问题，请提交 Issue 或 Pull Request。
