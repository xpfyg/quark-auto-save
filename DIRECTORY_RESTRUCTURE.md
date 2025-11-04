# 目录结构调整说明

## 修改内容

将 Flask 应用的静态文件和模板目录从 `app/` 移动到项目根目录的 `public/` 文件夹。

## 修改前的目录结构

```
quark-auto-save/
├── app/
│   ├── run.py              # Flask 应用入口
│   ├── static/             # 静态文件（CSS、JS、图片等）
│   │   ├── css/
│   │   ├── js/
│   │   └── favicon.ico
│   └── templates/          # HTML 模板
│       ├── index.html
│       ├── login.html
│       └── resources.html
└── ...
```

## 修改后的目录结构

```
quark-auto-save/
├── app/
│   ├── run.py              # Flask 应用入口
│   ├── config/             # 配置文件目录
│   ├── resource/           # 资源文件目录
│   └── sessions/           # Telegram session 目录
├── public/                 # 公共资源目录（新增）
│   ├── static/             # 静态文件
│   │   ├── css/
│   │   ├── js/
│   │   └── favicon.ico
│   └── templates/          # HTML 模板
│       ├── index.html
│       ├── login.html
│       └── resources.html
└── ...
```

## 代码修改

### app/run.py

#### 1. Flask 应用初始化

**修改前：**
```python
app = Flask(__name__)
```

**修改后：**
```python
# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")

# 创建 Flask 应用，指定 public 目录
app = Flask(__name__,
            static_folder=os.path.join(PUBLIC_DIR, "static"),
            template_folder=os.path.join(PUBLIC_DIR, "templates"))
```

#### 2. favicon 路由

**修改前：**
```python
@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )
```

**修改后：**
```python
@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        app.static_folder,
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )
```

## 优点

### 1. 更清晰的目录结构
- 将公共访问的资源（静态文件、模板）与应用代码分离
- 符合常见的 Web 项目目录组织规范
- `public/` 目录明确表示这些是对外公开的资源

### 2. 更好的安全性
- 明确区分公共资源和应用代码
- 便于配置 Web 服务器（如 Nginx）直接服务静态文件
- 减少应用代码的暴露风险

### 3. 便于部署
- 可以单独部署 `public/` 目录到 CDN
- 静态资源和应用代码解耦，便于独立扩展
- 符合前后端分离的趋势

### 4. 多项目共享
- 如果有多个 Flask 应用，可以共享同一个 `public/` 目录
- 减少资源重复

## 注意事项

### 1. 启动应用

启动方式不变，仍然在 `app/` 目录下运行：

```bash
cd app
python3 run.py
```

或者从项目根目录运行：

```bash
python3 app/run.py
```

### 2. 静态文件引用

在 HTML 模板中，静态文件的引用方式不变：

```html
<!-- CSS -->
<link rel="stylesheet" href="./static/css/bootstrap.min.css">

<!-- JS -->
<script src="./static/js/vue.min.js"></script>

<!-- 图片 -->
<img src="./static/favicon.ico" alt="icon">
```

### 3. Docker 部署

如果使用 Docker 部署，需要更新 Dockerfile，确保 `public/` 目录也被复制到容器中：

```dockerfile
COPY app/ /app/
COPY public/ /public/
```

### 4. Nginx 配置

如果使用 Nginx 作为反向代理，可以直接服务静态文件：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 静态文件直接由 Nginx 提供
    location /static/ {
        alias /path/to/quark-auto-save/public/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 动态请求转发到 Flask
    location / {
        proxy_pass http://127.0.0.1:5005;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 回滚方案

如果需要回滚到原来的目录结构：

```bash
# 1. 移动文件夹回 app 目录
mv public/static app/
mv public/templates app/

# 2. 删除 public 目录
rmdir public

# 3. 恢复 app/run.py 中的代码
# 将 Flask 初始化改回：
app = Flask(__name__)

# 将 favicon 路由改回：
return send_from_directory(
    os.path.join(app.root_path, "static"),
    "favicon.ico",
    mimetype="image/vnd.microsoft.icon",
)
```

## 测试验证

### 1. 启动应用

```bash
cd app
python3 run.py
```

### 2. 访问页面

- 登录页面：http://localhost:5005/login
- 首页：http://localhost:5005/
- 资源管理：http://localhost:5005/resources

### 3. 检查静态资源

打开浏览器开发者工具（F12），检查 Network 标签：
- CSS 文件是否正常加载
- JS 文件是否正常加载
- 图片是否正常显示
- 无 404 错误

### 4. 检查模板

确认所有页面能正常渲染：
- 登录页面样式正常
- 首页配置表单正常
- 资源管理页面卡片正常显示

## 相关文件

- `app/run.py` - Flask 应用入口（已修改）
- `public/static/` - 静态资源目录（新位置）
- `public/templates/` - 模板目录（新位置）

## 更新日期

2025-11-04
