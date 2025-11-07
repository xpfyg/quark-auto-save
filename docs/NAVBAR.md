# 通用导航栏使用说明

## 概述

所有页面现在使用统一的导航栏组件 `navbar_component.html`，确保导航栏的一致性和易维护性。

## 导航栏组件位置

```
public/templates/navbar_component.html
```

## 使用方法

### 1. 在模板中引入导航栏

在需要导航栏的页面中，添加以下代码：

```html
<!-- 导航栏 -->
{% include 'navbar_component.html' with context %}
```

### 2. 在路由中传递 active_page 参数

在 `run.py` 中的路由函数中，需要传递 `active_page` 参数来指定当前激活的页面：

```python
@app.route("/")
def index():
    if not is_login():
        return redirect(url_for("login"))
    return render_template("index.html", version=app.config["APP_VERSION"], active_page='home')
```

### 3. active_page 参数值

当前支持的 `active_page` 值：

- `'home'` - 首页（配置管理）
- `'resources'` - 资源管理页面
- `'search'` - 资源查询页面
- `'quark_files'` - 网盘资源页面

## 添加新的导航项

如果需要添加新的导航项，只需修改 `navbar_component.html` 文件：

```html
<li class="nav-item {% if active_page == 'new_page' %}active{% endif %}">
  <a class="nav-link" href="/new_page"><i class="bi bi-icon"></i> 新页面</a>
</li>
```

然后在对应的路由中传递 `active_page='new_page'`：

```python
@app.route("/new_page")
def new_page():
    if not is_login():
        return redirect(url_for("login"))
    return render_template("new_page.html", version=app.config["APP_VERSION"], active_page='new_page')
```

## 当前已使用的页面

- ✅ `index.html` - 首页（配置管理）
- ✅ `resources.html` - 资源管理
- ✅ `search_resources.html` - 资源查询
- ✅ `quark_files.html` - 网盘资源

## 导航栏结构

当前导航栏包含以下链接：

1. **首页** (`/`) - 配置管理
2. **资源管理** (`/resources`) - 查看和管理已收集的资源
3. **资源查询** (`/search_resources`) - 搜索和转存新资源
4. **网盘资源** (`/quark_files`) - 浏览夸克网盘文件
5. **退出** (`/logout`) - 退出登录

## 注意事项

1. **使用 with context**：必须使用 `{% include 'navbar_component.html' with context %}` 来确保 `active_page` 变量能够传递到组件中。

2. **active 状态**：导航栏会根据 `active_page` 参数自动高亮当前页面的导航项。

3. **一致性**：所有页面都应该使用相同的导航栏组件，确保用户体验的一致性。

4. **修改影响**：修改 `navbar_component.html` 会影响所有使用该组件的页面，请谨慎修改。

## 样式说明

导航栏使用 Bootstrap 4 的 navbar 组件，样式类：
- `navbar-dark bg-dark` - 深色主题
- `navbar-expand-lg` - 大屏幕展开
- `active` - 当前页面高亮

如需自定义样式，可以在各个页面的 `<style>` 标签中添加：

```css
.navbar {
  margin-bottom: 20px;
}
```
