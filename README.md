# Tufted Typst Blog

一个基于 [Typst](https://typst.app/) 的静态博客模板，支持 HTML、PDF、站内搜索、RSS、Sitemap、深色模式和本地预览。

本项目 fork 自 [Tufted-Blog-Template](https://github.com/Yousa-Mirage/Tufted-Blog-Template)。示例站点：<https://t0fv404.codeberg.page/Tufted_typst_blog/>。

模板相关代码继续遵循 [MIT License](LICENSE)。

## 环境要求

- Python 3.10 或更高版本
- Typst，并确保 `typst` 命令可以直接执行
- 可选：安装 [uv](https://docs.astral.sh/uv/)，用于按脚本声明的环境运行构建命令

## 构建命令

```bash
# 完整构建 HTML、PDF 和静态资源
uv run build.py build

# 强制完整重建
uv run build.py build --force

# 只构建 HTML
uv run build.py html

# 只构建 PDF
uv run build.py pdf

# 只复制 CSS、JavaScript 和图片资源
uv run build.py assets

# 清理 _site 和自动生成的文章元数据
uv run build.py clean

# 启动本地预览，默认访问 http://localhost:8000
uv run build.py preview
uv run build.py preview --port 3000
```

没有安装 uv 时，可以将命令中的 `uv run` 删除，直接使用 `python build.py ...`。构建结果位于 `_site/`，该目录是生成目录，不需要手动编辑。

构建时可以临时覆盖站点 URL：

```bash
uv run build.py build --site-url https://example.com/
```

## 目录结构

```text
config.typ                 全局网站配置
build.py                   构建脚本
content/                   页面和文章源文件
content/posts/              默认文章目录
tufted-lib/                模板内部库，一般不需要修改
css/custom.css             用户自定义 CSS
js/custom.js               用户自定义 JavaScript
assets/                    图片、favicon 等静态资源
_site/                     构建输出
.forgejo/workflows/        Codeberg / Forgejo 部署配置
.github/workflows/         GitHub Pages 部署配置
```

## 全局网站配置

编辑 [`config.typ`](config.typ) 中的 `tufted-web.with(...)` 参数。

### 站点信息

```typst
#let website-url = "https://example.com/"

#let template = tufted.tufted-web.with(
  website-title: "我的博客",
  author: "作者名称",
  description: "我的博客简介",
  lang: "zh",
  website-url: website-url,
)
```

- `website-url`：站点完整根 URL。部署在子路径时需要保留子路径，例如 `https://user.codeberg.page/repo/`。
- `website-title`：网站标题，用于页面标题、SEO 和 RSS。
- `author`：默认作者，可设置为 `none` 隐藏。
- `description`：默认网站描述，也用于 SEO 和社交分享。
- `lang`：默认语言，例如 `zh`、`en`。

### 导航、页眉和页脚

```typst
header-links: (
  "/": "首页",
  "/category/": "分类",
  "/about/": "关于",
),
header-elements: (
  [这里是页眉内容],
),
footer-elements: (
  [© 2026 我的博客],
),
```

`header-links` 的键是页面 URL，值是导航显示文本。添加导航项前，需要在 `content/` 下创建对应页面，例如 `content/about/index.typ`。

`header-elements` 和 `footer-elements` 是 Typst content 数组，可以写普通文本、链接、强调文本或其他 Typst 内容。

### RSS

```typst
feed-dir: ("/posts/",),
```

`feed-dir` 是 RSS 配置项。配置一个或多个 `_site/` 下的内容目录后，构建脚本会扫描这些目录中的文章并生成 `_site/feed.xml`。例如：

```typst
feed-dir: ("/posts/", "/notes/"),
```

如果不需要 RSS，可以设置为空数组：

```typst
feed-dir: (),
```

RSS 的文章目录配置与 `build.py` 中的 `POSTS_DIR` 是两个独立配置：前者控制哪些已生成目录进入 RSS，后者控制哪些源文件参与文章元数据和搜索索引生成。

### 自定义 CSS 和页面脚本

全站自定义 CSS 写入 [`css/custom.css`](css/custom.css)。它会在默认样式之后加载，适合覆盖主题变量或补充页面样式。

全站自定义 JavaScript 写入 [`js/custom.js`](js/custom.js)。它会在默认脚本之后加载，并且会在所有页面执行。

单个页面也可以通过 `js-scripts` 和 `css` 覆盖或追加资源：

```typst
#show: template.with(
  title: "特殊页面",
  css: ("/css/custom.css", "/css/special.css"),
  js-scripts: ("/js/special.js",),
)
```

这些文件放在项目的 `css/` 或 `js/` 目录中，构建时会自动复制到 `_site/`。

## 创建页面和文章

### 普通页面

页面路径由 `content/` 下的文件路径决定：

```text
content/about/index.typ       -> /about/
content/contact.typ           -> /contact.html
```

推荐使用 `index.typ` 创建目录式页面：

```typst
#import "/config.typ": template

#show: template.with(
  title: "关于",
  description: "关于这个博客",
)

= 关于

这里是页面内容。
```

### 文章

默认文章放在 `content/posts/` 下，每篇文章使用一个目录和 `index.typ`：

```text
content/posts/my-first-post/index.typ -> /posts/my-first-post/
```

文章必须在 `#show: template.with(...)` 中声明 `title` 和 `date`，否则不会进入首页文章列表和自动生成的元数据：

```typst
#import "/config.typ": template

#show: template.with(
  title: "我的第一篇文章",
  description: "文章摘要",
  date: datetime(year: 2026, month: 8, day: 18),
  modified: datetime(year: 2026, month: 8, day: 18),
  author: "作者名称",
  category: "技术/Typst",
  lang: "zh",
)

= 我的第一篇文章

正文内容。
```

文章元数据说明：

- `title`：文章标题，必填。
- `description`：文章摘要，用于首页、搜索和 SEO。
- `date`：发布日期，必填，格式为 `datetime(...)`。
- `modified`：更新时间，可选，会显示在文章信息栏。
- `author`：作者，可选。
- `category`：分类，可使用 `/` 表示层级，例如 `技术/Typst`；未填写时归入“未分类”。
- `lang`：文章语言，可覆盖全局语言配置。
- `image-path`：可选的 Open Graph 分享图片路径或完整 URL，例如 `"/assets/cover.png"`。
- `extra-info`：可选的文章附加信息，会显示在文章信息栏。

`content/_meta.typ` 由 `build.py` 自动生成，不要手动编辑。首页和分类页会读取这个文件。

### 配置多个文章目录

如果文章分散在多个目录，修改 [`build.py`](build.py) 顶部的 `POSTS_DIR`：

```python
POSTS_DIR = [
    Path("content/posts"),
    Path("content/notes"),
]
```

这些目录中的 `.typ` 文件都会被用于生成文章元数据和搜索索引。目录应该位于 `content/` 内，生成 URL 会按照它们相对于 `content/` 的路径保持一致。

如果需要改变源文件、样式、脚本或构建输出的位置，也可以修改 `build.py` 顶部的 `CONTENT_DIR`、`SITE_DIR`、`ASSETS_DIR`、`CSS_DIR`、`JS_DIR` 和 `CONFIG_FILE`。这些目录之间存在路径约定，除非确实需要调整构建结构，否则建议只修改 `POSTS_DIR`。

## 资源和主题

- 将图片、字体、favicon 等资源放入 `assets/`，页面中可以使用 `/assets/example.png` 引用。
- 默认主题变量和深色模式样式位于 `css/theme.css`。
- 通用布局与组件样式位于 `css/tufted.css`、`css/search.css` 和 `css/rss.css`。
- 用户修改应优先写入 `css/custom.css`，避免直接修改模板内部样式。
- 默认 JavaScript 位于 `js/`，用户代码应写入 `js/custom.js`；该文件会在模板同步时保留。

模板默认提供代码块处理、标题格式化、主题切换、搜索、边注切换、目录、返回顶部、数学公式复制和代码复制功能。

## 部署

### Codeberg Pages / Forgejo

`.forgejo/workflows/deploy.yml` 会在推送到 `main` 或 `master` 时自动构建并部署到 Codeberg Pages。通常只需要：

1. 将仓库推送到 Codeberg。
2. 确认 `config.typ` 中的 `website-url` 与实际站点 URL 一致。
3. 确认仓库已启用 Forgejo Actions，并允许使用部署 token。

默认 workflow 会根据仓库名自动计算项目页 URL。如使用自定义域名，修改 workflow 中 `Deploy to Codeberg Pages` 步骤的 `site` 值，并同步修改 `config.typ` 的 `website-url`。

### GitHub Pages

`.github/workflows/deploy.yml` 使用 GitHub Pages 官方部署流程。启用仓库的 Pages Actions 后，推送到 `main` 或 `master` 会自动构建和发布。

如果部署到项目页而不是用户页，`config.typ` 的 `website-url` 必须包含仓库名对应的子路径。也可以在本地使用 `--site-url` 临时覆盖，不必修改配置文件。

## 模板同步

项目同时保留了 GitHub Actions 和 Forgejo Actions 的上游同步 workflow，均为手动触发。`.templatesyncignore` 会保护以下用户内容不被上游模板覆盖：

- `content/`
- `config.typ`
- `css/custom.css`
- `js/custom.js`
- `assets/`
- `README.md`、`LICENSE`、`TODO.md`
- 用户自己的同步 workflow

模板内部文件位于 `tufted-lib/`。更新模板时，建议先检查同步 PR，再处理 `tufted-lib/`、默认 CSS 和默认 JS 的变化。

## 生成文件

- `_site/`：HTML、PDF、CSS、JavaScript、资源和 RSS 等构建产物。
- `content/_meta.typ`：由构建脚本生成的文章元数据。
- `_site/search-index.json`：站内搜索索引。
- `_site/feed.xml`：RSS 订阅源。
- `_site/sitemap.xml`：站点地图。
- `_site/robots.txt`：搜索引擎爬虫规则。

这些文件不需要手动修改，修改源文件后重新构建即可。