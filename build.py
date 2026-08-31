#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# ///

"""Tufted Blog Template 构建脚本：Typst 编译 + 资源复制 + 预览服务器，支持增量编译。

用法:
    uv run build.py build                        # 完整构建 (HTML + PDF + 资源)
    uv run build.py build --site-url https://example.com/   # 覆盖站点 URL
    uv run build.py build --force                # 强制完整重建
    uv run build.py html|pdf|assets|clean        # 单独执行某一步
    uv run build.py preview [-p PORT] [--no-open]  # 本地 URL 构建 + 预览服务器
    python build.py ...                          # 未安装 uv 时直接运行
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

# ============================================================================
# 配置
# ============================================================================

CONTENT_DIR = Path("content")               # 源文件目录
SITE_DIR = Path("_site")                    # 输出目录
ASSETS_DIR = Path("assets")                 # 字体等静态资源
CSS_DIR = Path("css")
JS_DIR = Path("js")
CONFIG_FILE = Path("config.typ")            # 全局配置
POSTS_DIRS = (Path("content/posts"),)       # 文章目录
POSTS_META_FILE = Path("content/_meta.typ")  # 自动生成的文章元数据
UNCATEGORIZED = "未分类"
MATHML_MIN_TYPST_VERSION = (0, 15, 0)
SITE_URL_STAMP_FILE = SITE_DIR / ".site-url"

# 剔除 Typst 注释：字符串原样保留，// 与 /* */ 注释替换为空
COMMENT_STRIP_RE = re.compile(r'("(?:[^"\\]|\\.)*")|//[^\n]*|/\*.*?\*/', re.DOTALL)
# #import/#include 引用（双引号或单引号）
IMPORT_RE = re.compile(r"""#(import|include)\s+(?:"([^"]+)"|'([^']+)')""")
# 文章元数据（date/modified 为 datetime(...) 形式）
_DATETIME_RE = r"datetime\(\s*year:\s*(\d+)\s*,\s*month:\s*(\d+)\s*,\s*day:\s*(\d+)\s*\)"
POST_META_PATTERNS = {
    "title": re.compile(r'title:\s*"([^"]*)"'),
    "description": re.compile(r'description:\s*"([^"]*)"'),
    "lang": re.compile(r'lang:\s*"([^"]*)"'),
    "category": re.compile(r'category:\s*"([^"]*)"'),
    "date": re.compile(rf"date:\s*{_DATETIME_RE}"),
    "modified": re.compile(rf"modified:\s*{_DATETIME_RE}"),
}


@dataclass
class BuildStats:
    """构建统计信息。"""

    success: int = 0
    skipped: int = 0
    failed: int = 0

    def format_summary(self) -> str:
        parts = []
        if self.success:
            parts.append(f"编译: {self.success}")
        if self.skipped:
            parts.append(f"跳过: {self.skipped}")
        if self.failed:
            parts.append(f"失败: {self.failed}")
        return ", ".join(parts) or "无文件需要处理"

    @property
    def has_failures(self) -> bool:
        return self.failed > 0


class HTMLMetadataParser(HTMLParser):
    """从 HTML 提取 lang/title/description/canonical link/date 元数据。"""

    def __init__(self):
        super().__init__()
        self.metadata = {"title": ""}
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = {k: v for k, v in attrs if v}
        if tag == "html":
            self.metadata["lang"] = a.get("lang", "")
        elif tag == "title":
            self._in_title = True
        elif tag == "meta" and a.get("name") in {"description", "date"}:
            self.metadata[a["name"]] = a.get("content", "")
        elif tag == "link" and a.get("rel") == "canonical":
            self.metadata["link"] = a.get("href", "")

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.metadata["title"] += data


# ============================================================================
# 通用工具
# ============================================================================


def read_stripped(path: Path) -> str | None:
    """读取文件并剔除 Typst 注释，读取失败返回 None。"""
    try:
        return COMMENT_STRIP_RE.sub(r"\1", path.read_text(encoding="utf-8"))
    except Exception:
        return None


def mtime(path: Path) -> float:
    """文件修改时间，不存在返回 0。"""
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def run_typst(args: list[str]) -> bool:
    """运行 typst 命令，成功返回 True。"""
    try:
        result = subprocess.run(
            ["typst", *args], capture_output=True, text=True, encoding="utf-8"
        )
    except FileNotFoundError:
        print("  ❌ 未找到 typst 命令，请安装 Typst 并加入 PATH: https://typst.app/open-source/#download")
        return False
    except Exception as e:
        print(f"  ❌ 执行 typst 命令时出错: {e}")
        return False

    if result.returncode != 0:
        print(f"  ❌ Typst 错误: {result.stderr.strip()}")
        return False
    return True


def get_typst_version() -> tuple[int, ...] | None:
    """返回 Typst CLI 版本号，获取失败返回 None。"""
    try:
        result = subprocess.run(
            ["typst", "--version"], capture_output=True, text=True, encoding="utf-8"
        )
    except OSError:
        return None

    match = re.search(r"typst (\d+)\.(\d+)\.(\d+)", result.stdout)
    if result.returncode != 0 or match is None:
        return None
    return tuple(int(x) for x in match.groups())


def warn_if_typst_version_is_outdated() -> None:
    """低于 MathML 支持基线（Typst 0.15）时输出升级提示。"""
    version = get_typst_version()
    if version is None or version >= MATHML_MIN_TYPST_VERSION:
        return
    current = ".".join(str(x) for x in version)
    required = ".".join(str(x) for x in MATHML_MIN_TYPST_VERSION)
    print(f"  ⚠️ 检测到 Typst {current}，原生 MathML 需要 Typst {required}+，建议升级。")


# ============================================================================
# 依赖分析与增量编译
# ============================================================================


def is_page_file(path: Path) -> bool:
    """content/ 下不含 _ 前缀路径段的 .typ 文件视为页面。"""
    try:
        parts = path.resolve().relative_to(CONTENT_DIR.resolve()).parts
    except ValueError:
        return False
    return not any(part.startswith("_") for part in parts)


def is_dep_file(path: Path) -> bool:
    """是否追踪为依赖：content/ 外的文件、config.typ、content/_* 下的文件。"""
    resolved = path.resolve()
    if resolved == CONFIG_FILE.resolve():
        return True
    try:
        resolved.relative_to(CONTENT_DIR.resolve())
    except ValueError:
        return True  # 不在 content/ 下（如 tufted-lib），视为依赖
    return not is_page_file(resolved)


def find_typ_dependencies(typ_file: Path) -> set[Path]:
    """解析 #import/#include 的本地 .typ 依赖（跳过 @package 与页面文件）。"""
    content = read_stripped(typ_file)
    if content is None:
        return set()

    deps: set[Path] = set()
    for match in IMPORT_RE.finditer(content):
        dep = match.group(2) or match.group(3)
        if dep.startswith("@"):
            continue
        path = Path(dep.lstrip("/")) if dep.startswith("/") else typ_file.parent / dep
        path = path.resolve()
        if path.exists() and path.suffix == ".typ" and is_dep_file(path):
            deps.add(path)
    return deps


def get_all_dependencies(typ_file: Path, visited: set[Path] | None = None) -> set[Path]:
    """递归获取 .typ 文件的全部传递依赖。"""
    if visited is None:
        visited = set()
    abs_path = typ_file.resolve()
    if abs_path in visited:
        return set()
    visited.add(abs_path)

    deps: set[Path] = set()
    for dep in find_typ_dependencies(typ_file):
        deps.add(dep)
        deps.update(get_all_dependencies(dep, visited))
    return deps


def needs_rebuild(source: Path, target: Path, extra_deps: list[Path] | None = None) -> bool:
    """目标不存在，或源文件/依赖/同目录资源比目标新时需要重建。"""
    if not target.exists():
        return True

    target_mtime = mtime(target)
    deps = [source, *(extra_deps or []), *get_all_dependencies(source)]
    if any(mtime(dep) > target_mtime for dep in deps if dep.exists()):
        return True

    # 源文件同目录下的非 .typ 资源（.md/.bib/图片等）
    return any(
        mtime(item) > target_mtime
        for item in source.parent.iterdir()
        if item.is_file() and item.suffix != ".typ"
    )


def find_common_dependencies() -> list[Path]:
    """公共依赖：config.typ 与 content/_* 目录下的 .typ 文件。"""
    deps = [CONFIG_FILE] if CONFIG_FILE.exists() else []
    if CONTENT_DIR.exists():
        for item in CONTENT_DIR.iterdir():
            if item.is_dir() and item.name.startswith("_"):
                deps.extend(item.rglob("*.typ"))
    return deps


def find_typ_files() -> list[Path]:
    """content/ 下所有页面 .typ 文件。"""
    return [f for f in CONTENT_DIR.rglob("*.typ") if is_page_file(f)]


def find_post_typ_files() -> list[Path]:
    """POSTS_DIRS 下所有文章 .typ 文件（去重排序）。"""
    files = {
        f
        for d in POSTS_DIRS
        if d.exists()
        for f in d.rglob("*.typ")
        if not f.name.startswith("_")
    }
    return sorted(files)


# ============================================================================
# 文章元数据
# ============================================================================


def extract_post_meta(text: str) -> dict | None:
    """从文章源码提取元数据，缺少 title 或 date 时返回 None。"""
    m = {name: pattern.search(text) for name, pattern in POST_META_PATTERNS.items()}
    if not m["title"] or not m["date"]:
        return None

    year, month, day = m["date"].groups()
    meta = {
        "title": m["title"].group(1),
        "description": m["description"].group(1) if m["description"] else "",
        "date_str": f"{year}-{month.zfill(2)}-{day.zfill(2)}",
        "datetime_str": f"datetime(year: {year}, month: {int(month)}, day: {int(day)})",
        "lang": m["lang"].group(1) if m["lang"] else "zh",
        "category": m["category"].group(1) if m["category"] else UNCATEGORIZED,
        "modified": None,
    }

    if m["modified"]:
        my, mmo, md = m["modified"].groups()
        meta["modified"] = f"datetime(year: {my}, month: {int(mmo)}, day: {int(md)})"

    return meta


def post_output_path(typ_file: Path) -> str:
    """文章相对站点根的 URL 路径：目录式文章用尾斜杠，文件式用 .html。"""
    rel = typ_file.relative_to(CONTENT_DIR).with_suffix("")
    if rel.name == "index":
        return rel.parent.as_posix() + "/"
    return rel.with_suffix(".html").as_posix()


def generate_posts_meta() -> bool:
    """扫描文章源码提取元数据，生成 content/_meta.typ。"""
    if not any(d.exists() for d in POSTS_DIRS):
        return True

    posts = []
    for typ_file in find_post_typ_files():
        text = read_stripped(typ_file)
        if text is None:
            continue

        meta = extract_post_meta(text)
        if meta is None:
            print(f"  ⚠ {typ_file.relative_to('.')}: 缺少 title 或 date 元数据，已跳过")
            continue

        url = post_output_path(typ_file)
        slug = url.removesuffix("/").removesuffix(".html")
        posts.append({"slug": slug, "url": url, **meta})

    posts.sort(key=lambda p: p["date_str"], reverse=True)

    lines = [
        "// 本文件由 build.py 自动生成，请勿手动编辑。",
        "// 元数据在每篇文章的 #show: template.with(...) 中声明。",
        "",
        "#let posts = (",
    ]
    for p in posts:
        lines += [
            "  (",
            f'    slug: "{p["slug"]}",',
            f'    url: "{p["url"]}",',
            f'    title: "{p["title"]}",',
            f'    description: "{p["description"]}",',
            f"    date: {p['datetime_str']},",
            f'    lang: "{p["lang"]}",',
            f'    category: "{p["category"]}",',
        ]
        if p["modified"]:
            lines.append(f"    modified: {p['modified']},")
        lines.append("  ),")
    lines.append(")")

    POSTS_META_FILE.parent.mkdir(parents=True, exist_ok=True)
    POSTS_META_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"📝 已生成 {POSTS_META_FILE} （{len(posts)} 篇文章）")
    return True


def generate_search_index(site_url: str) -> bool:
    """生成站内搜索索引 _site/search-index.json。"""
    if not any(d.exists() for d in POSTS_DIRS):
        return True

    entries = []
    for typ_file in find_post_typ_files():
        text = read_stripped(typ_file)
        if text is None:
            continue

        meta = extract_post_meta(text)
        if meta is None:
            continue

        entries.append(
            {
                "url": site_url.rstrip("/") + "/" + post_output_path(typ_file),
                "title": meta["title"],
                "description": meta["description"],
                "category": meta["category"],
                "date": meta["date_str"],
                "content": text,
            }
        )

    out = SITE_DIR / "search-index.json"
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"🔍 已生成搜索索引: {out} ({len(entries)} 篇文章)")
    return True


# ============================================================================
# 构建命令
# ============================================================================


def get_site_url_stamp() -> str | None:
    """上次构建使用的站点 URL，无记录返回 None。"""
    try:
        return SITE_URL_STAMP_FILE.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def set_site_url_stamp(site_url: str) -> None:
    """记录本次构建的站点 URL（URL 变化时据此强制重建）。"""
    try:
        SITE_DIR.mkdir(parents=True, exist_ok=True)
        SITE_URL_STAMP_FILE.write_text(site_url, encoding="utf-8")
    except OSError:
        pass


def get_file_output_path(typ_file: Path, suffix: str) -> Path:
    """映射 content/xxx.typ → _site/xxx.<suffix>。"""
    return SITE_DIR / typ_file.relative_to(CONTENT_DIR).with_suffix(f".{suffix}")


TYPST_COMMON_ARGS = ["compile", "--root", ".", "--font-path", str(ASSETS_DIR)]


def compile_files(
    files: list[Path],
    suffix: str,
    force: bool,
    extra_args,
) -> BuildStats:
    """按增量规则编译文件列表，extra_args(typ_file) 返回额外命令行参数。"""
    stats = BuildStats()
    common_deps = find_common_dependencies()

    for typ_file in files:
        output = get_file_output_path(typ_file, suffix)
        if not force and not needs_rebuild(typ_file, output, common_deps):
            stats.skipped += 1
            continue

        output.parent.mkdir(parents=True, exist_ok=True)
        args = [*TYPST_COMMON_ARGS, *extra_args(typ_file), str(typ_file), str(output)]
        if run_typst(args):
            stats.success += 1
        else:
            print(f"  ❌ {typ_file} 编译失败")
            stats.failed += 1

    return stats


def build_html(force: bool = False, site_url: str | None = None) -> bool:
    """编译所有页面为 HTML（文件名含 PDF 的除外），site-url 变化时强制重建。"""
    SITE_DIR.mkdir(parents=True, exist_ok=True)

    if site_url and get_site_url_stamp() != site_url:
        print(f"  🔄 站点 URL 变为 {site_url}，重新编译所有 HTML...")
        force = True

    html_files = [f for f in find_typ_files() if "pdf" not in f.stem.lower()]
    if not html_files:
        print("  ⚠️ 未找到任何 HTML 文件。")
        return True

    print("正在构建 HTML 文件...")

    def html_args(typ_file: Path) -> list[str]:
        rel = typ_file.relative_to(CONTENT_DIR)
        if rel.name == "index.typ":
            # content/index.typ → ""（首页），content/Blog/index.typ → "Blog"
            page_path = rel.parent.as_posix()
            page_path = "" if page_path == "." else page_path
        else:
            # content/about.typ → "about"
            page_path = rel.with_suffix("").as_posix()
        return [
            "--features",
            "html",
            "--format",
            "html",
            "--input",
            f"page-path={page_path}",
            *(["--input", f"site-url={site_url}"] if site_url else []),
        ]

    stats = compile_files(html_files, "html", force, html_args)

    if site_url:
        set_site_url_stamp(site_url)

    print(f"✅ HTML 构建完成。{stats.format_summary()}")
    return not stats.has_failures


def build_pdf(force: bool = False) -> bool:
    """编译文件名含 PDF 的页面为 PDF。"""
    SITE_DIR.mkdir(parents=True, exist_ok=True)

    pdf_files = [f for f in find_typ_files() if "pdf" in f.stem.lower()]
    if not pdf_files:
        return True

    print("正在构建 PDF 文件...")
    stats = compile_files(pdf_files, "pdf", force, lambda typ_file: [])
    print(f"✅ PDF 构建完成。{stats.format_summary()}")
    return not stats.has_failures


def copy_assets() -> bool:
    """将 css/、js/、assets/ 复制到 _site/ 下。"""
    SITE_DIR.mkdir(parents=True, exist_ok=True)

    for src_dir in (CSS_DIR, JS_DIR, ASSETS_DIR):
        if not src_dir.exists():
            continue
        target_dir = SITE_DIR / src_dir
        try:
            if target_dir.exists():
                shutil.rmtree(target_dir)
            shutil.copytree(src_dir, target_dir)
        except Exception as e:
            print(f"  ❌ 复制 {src_dir} 失败: {e}")
            return False
    return True


def copy_content_assets(force: bool = False) -> bool:
    """增量复制 content/ 下的非 .typ 资源（图片等）到 _site/。"""
    SITE_DIR.mkdir(parents=True, exist_ok=True)

    if not CONTENT_DIR.exists():
        print(f"  ⚠ 内容目录 {CONTENT_DIR} 不存在，跳过。")
        return True

    try:
        for item in CONTENT_DIR.rglob("*"):
            if item.is_dir() or item.suffix == ".typ":
                continue

            rel = item.relative_to(CONTENT_DIR)
            if any(part.startswith("_") for part in rel.parts):
                continue

            target = SITE_DIR / rel
            if not force and target.exists() and mtime(item) <= mtime(target):
                continue

            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
        return True
    except Exception as e:
        print(f"  ❌ 复制内容资源文件失败: {e}")
        return False


def clean() -> bool:
    """清理 _site 目录内容与自动生成的文章元数据。"""
    print("正在清理生成的文件...")

    cleaned = []
    try:
        if SITE_DIR.exists():
            for item in SITE_DIR.iterdir():
                shutil.rmtree(item) if item.is_dir() else item.unlink()
            cleaned.append(f"{SITE_DIR}/ 目录")
        if POSTS_META_FILE.exists():
            POSTS_META_FILE.unlink()
            cleaned.append(str(POSTS_META_FILE))
    except Exception as e:
        print(f"  ❌ 清理失败: {e}")
        return False

    if cleaned:
        print(f"  🧹 已清理 {' 和 '.join(cleaned)}。")
    else:
        print(f"  输出目录 {SITE_DIR} 不存在，无需清理。")
    return True


def build(force: bool = False, site_url: str | None = None) -> bool:
    """完整构建：元数据 → HTML/PDF → 搜索索引 → 资源 → SEO 文件。"""
    print("-" * 60)
    print("🛠️ 开始完整构建..." if force else "🚀 开始增量构建...")
    print("-" * 60)

    if force:
        clean()

    site_url = site_url or get_config_site_url()

    generate_posts_meta()
    results = [build_html(force, site_url), build_pdf(force)]

    generate_search_index(site_url)
    results += [
        copy_assets(),
        copy_content_assets(force),
        generate_sitemap(site_url),
        generate_robots_txt(site_url),
        generate_rss(site_url),
    ]

    print("-" * 60)
    if all(results):
        print("✅ 所有构建任务完成！")
        print(f"  📂 输出目录: {SITE_DIR.absolute()}")
    else:
        print("⚠ 构建完成，但有部分任务失败。")
    print("-" * 60)
    return all(results)


def preview(port: int = 8000, open_browser_flag: bool = True) -> bool:
    """用本地 URL 构建站点并启动预览服务器（优先 livereload，回退 http.server）。"""
    site_url = f"http://localhost:{port}"

    print(f"🛠️ 使用本地 URL {site_url}/ 构建（预览不受 website-url 影响）...")
    if not build(site_url=site_url):
        print("  ❌ 本地构建失败，无法启动预览服务器。")
        return False

    print("正在启动本地预览服务器（按 Ctrl+C 停止）...")

    if open_browser_flag:

        def open_browser():
            time.sleep(1.5)  # 等待服务器启动
            print(f"🚀 正在打开浏览器: http://localhost:{port}")
            webbrowser.open(f"http://localhost:{port}")

        threading.Thread(target=open_browser, daemon=True).start()

    try:
        return (
            subprocess.run(
                ["uvx", "livereload", str(SITE_DIR), "-p", str(port)], check=False
            ).returncode
            == 0
        )
    except FileNotFoundError:
        print("  未找到 uv，尝试 Python http.server...")
    except KeyboardInterrupt:
        print("\n服务器已停止。")
        return True

    print("使用 Python 内置 http.server...")
    try:
        return (
            subprocess.run(
                [sys.executable, "-m", "http.server", str(port), "--directory", str(SITE_DIR)],
                check=False,
            ).returncode
            == 0
        )
    except KeyboardInterrupt:
        print("\n服务器已停止。")
        return True
    except Exception as e:
        print(f"  ❌ 启动服务器失败: {e}")
        return False


# ============================================================================
# SEO 与订阅源
# ============================================================================


def parse_html_metadata(html_path: Path) -> dict[str, str]:
    """解析 HTML 文件，返回元数据字典。"""
    parser = HTMLMetadataParser()
    parser.feed(html_path.read_text(encoding="utf-8"))
    return parser.metadata


def get_config_site_url() -> str:
    """从 config.typ 读取默认站点 URL（带尾斜杠）。"""
    content = read_stripped(CONFIG_FILE)
    match = re.search(r'#let\s+website-url\s*=\s*"([^"]+)"', content or "")
    if not match:
        raise ValueError("config.typ 中缺少 website-url 配置")
    return match.group(1).rstrip("/") + "/"


def get_feed_dirs() -> set[str]:
    """从 config.typ 解析 RSS 订阅源目录列表。"""
    content = read_stripped(CONFIG_FILE)
    if content is None:
        return set()
    match = re.search(r"feed-dir\s*:\s*\((.*?)\)", content, re.DOTALL)
    if not match:
        return set()
    return {c.strip("/") for c in re.findall(r'"([^"]*)"', match.group(1)) if c.strip("/")}


def parse_date_str(date_str: str) -> datetime | None:
    """解析 YYYY-MM-DD（可带时间部分）为 UTC datetime，失败返回 None。"""
    try:
        return datetime.strptime(date_str.split("T")[0], "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return None


def extract_post_metadata(index_html: Path) -> tuple[str, str, str, datetime | None]:
    """从文章 index.html 提取 (title, description, canonical link, UTC date)。"""
    meta = parse_html_metadata(index_html)

    date_obj = parse_date_str(meta.get("date", ""))
    if date_obj is None:
        m = re.search(r"(\d{4}-\d{2}-\d{2})", index_html.parent.name)
        if m:
            date_obj = parse_date_str(m.group(1))

    return (
        meta["title"].strip(),
        meta.get("description", "").strip(),
        meta.get("link", ""),
        date_obj,
    )


def collect_posts(dirs: set[str]) -> list[dict]:
    """收集订阅目录下所有文章（标题/描述/链接/日期/分类）。"""
    posts = []
    for d in dirs:
        dir_path = SITE_DIR / d
        for index_html in dir_path.rglob("index.html"):
            article_dir = index_html.parent
            if article_dir == dir_path:  # 跳过订阅目录自身的 index.html
                continue

            title, description, link, date_obj = extract_post_metadata(index_html)
            if date_obj is None:
                print(f"⚠️ 无法确定文章 '{article_dir.name}' 的日期，已跳过。")
                continue

            try:
                category = article_dir.relative_to(dir_path).parts[0]
            except (ValueError, IndexError):
                category = d

            posts.append(
                {
                    "title": title,
                    "description": description,
                    "dir": category,
                    "link": link,
                    "date": date_obj,
                }
            )
    return posts


def build_rss_xml(posts: list[dict], config: dict) -> str:
    """构建 RSS 2.0 XML 字符串。"""
    import xml.etree.ElementTree as ET
    from email.utils import format_datetime

    ATOM_NS = "http://www.w3.org/2005/Atom"
    ET.register_namespace("atom", ATOM_NS)

    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = config["site_title"]
    ET.SubElement(channel, "link").text = config["site_url"]
    ET.SubElement(channel, "description").text = config["site_description"]
    ET.SubElement(channel, "language").text = config["lang"]
    ET.SubElement(channel, "lastBuildDate").text = format_datetime(datetime.now(timezone.utc))

    atom_link = ET.SubElement(channel, f"{{{ATOM_NS}}}link")
    atom_link.set("href", f"{config['site_url']}/feed.xml")
    atom_link.set("rel", "self")
    atom_link.set("type", "application/rss+xml")

    for post in posts:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = post["title"]
        ET.SubElement(item, "link").text = post["link"]
        ET.SubElement(item, "guid", isPermaLink="true").text = post["link"]
        ET.SubElement(item, "pubDate").text = format_datetime(post["date"])
        ET.SubElement(item, "category").text = post["dir"]
        if post["description"]:
            ET.SubElement(item, "description").text = post["description"]

    ET.indent(rss, space="  ")
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{ET.tostring(rss, encoding="unicode", xml_declaration=False)}'


def generate_rss(site_url: str) -> bool:
    """根据 config.typ 的 feed-dir 收集文章，生成 _site/feed.xml。"""
    dirs = get_feed_dirs()
    if not dirs:
        print("⚠️ 跳过 RSS 订阅源生成: 未配置任何目录。")
        return True

    existing = {d for d in dirs if (SITE_DIR / d).exists()}
    for d in dirs - existing:
        print(f"⚠️ 警告: 配置的目录 '{d}' 不存在。")
    if not existing:
        print("⚠️ 跳过 RSS 订阅源生成: 配置的目录都不存在。")
        return True

    posts = collect_posts(existing)
    if not posts:
        print("⚠️ 未找到任何文章，RSS 订阅源为空。")
        return True
    posts.sort(key=lambda p: p["date"], reverse=True)

    meta = parse_html_metadata(SITE_DIR / "index.html")
    config = {
        "site_url": site_url,
        "site_title": meta["title"].strip(),
        "site_description": meta.get("description", "").strip(),
        "lang": meta["lang"],
    }

    try:
        (SITE_DIR / "feed.xml").write_text(build_rss_xml(posts, config), encoding="utf-8")
        print(f"📡 RSS 订阅源生成成功: {SITE_DIR / 'feed.xml'} ({len(posts)} 篇文章)")
        return True
    except Exception as e:
        print(f"❌ 生成 RSS 订阅源失败: {e}")
        return False


def generate_sitemap(site_url: str) -> bool:
    """遍历 _site/*.html 生成 sitemap.xml。"""
    import xml.etree.ElementTree as ET

    NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("", NS)
    urlset = ET.Element("urlset", xmlns=NS)

    for file_path in sorted(SITE_DIR.rglob("*.html")):
        rel = file_path.relative_to(SITE_DIR).as_posix()
        if rel == "index.html":
            url_path = ""
        elif rel.endswith("/index.html"):
            url_path = rel.removesuffix("index.html")
        elif rel.endswith(".html"):
            url_path = rel.removesuffix(".html") + "/"
        else:
            url_path = rel

        loc = ET.SubElement(urlset, "url")
        ET.SubElement(loc, "loc").text = f"{site_url}/{url_path}"
        ET.SubElement(loc, "lastmod").text = datetime.fromtimestamp(
            file_path.stat().st_mtime
        ).strftime("%Y-%m-%d")

    ET.indent(urlset, space="  ")
    xml = (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'{ET.tostring(urlset, encoding="unicode", xml_declaration=False)}'
    )

    try:
        (SITE_DIR / "sitemap.xml").write_text(xml, encoding="utf-8")
        print(f"🗺️ Sitemap 构建完成: 包含 {len(urlset)} 个页面")
        return True
    except Exception as e:
        print(f"❌ Sitemap 构建失败: {e}")
        return False


def generate_robots_txt(site_url: str) -> bool:
    """生成指向 sitemap 的 robots.txt。"""
    content = f"User-agent: *\nAllow: /\n\nSitemap: {site_url}/sitemap.xml\n"
    try:
        (SITE_DIR / "robots.txt").write_text(content, encoding="utf-8")
        return True
    except Exception as e:
        print(f"❌ 生成 robots.txt 失败: {e}")
        return False


# ============================================================================
# 命令行接口
# ============================================================================


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="build.py",
        description="Tufted Blog Template 构建脚本 - 将 content 中的 Typst 文件编译为 HTML 和 PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
构建脚本默认只重新编译修改过的文件，可使用 -f/--force 选项强制完整重建：
    uv run build.py build --force
    或 python build.py build -f

使用 preview 命令启动本地预览服务器（自动使用本地 URL 构建，预览不受 website-url 影响）：
    uv run build.py preview
    或 python build.py preview -p 3000  # 使用自定义端口

更多信息请参阅 README.md
""",
    )
    sub = parser.add_subparsers(dest="command", title="可用命令", metavar="<command>")

    for name, help_text in (
        ("build", "完整构建 (HTML + PDF + 资源)"),
        ("html", "仅构建 HTML 文件"),
        ("pdf", "仅构建 PDF 文件"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("-f", "--force", action="store_true", help="强制完整重建")
        if name != "pdf":
            p.add_argument("--site-url", help="覆盖站点完整 URL")

    sub.add_parser("assets", help="仅复制静态资源")
    sub.add_parser("clean", help="清理生成的文件")

    p = sub.add_parser("preview", help="用本地 URL 构建并启动预览服务器")
    p.add_argument("-p", "--port", type=int, default=8000, help="服务器端口号（默认: 8000）")
    p.add_argument(
        "--no-open", action="store_false", dest="open_browser", help="不自动打开浏览器"
    )
    p.set_defaults(open_browser=True)

    return parser


if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    # 确保在项目根目录运行
    os.chdir(Path(__file__).parent.absolute())

    if args.command in {"build", "html", "pdf"}:
        warn_if_typst_version_is_outdated()

    force = getattr(args, "force", False)
    site_url = getattr(args, "site_url", None)

    match args.command:
        case "build":
            ok = build(force, site_url)
        case "html":
            ok = build_html(force, site_url or get_config_site_url())
        case "pdf":
            ok = build_pdf(force)
        case "assets":
            ok = copy_assets()
        case "clean":
            ok = clean()
        case "preview":
            ok = preview(getattr(args, "port", 8000), getattr(args, "open_browser", True))
        case _:
            print(f"❌ 未知命令: {args.command}")
            ok = False

    sys.exit(0 if ok else 1)
