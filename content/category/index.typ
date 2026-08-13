// 类别页面 — 按目录层级分组显示所有文章
#import "/content/index.typ": template, tufted, site-link

#show: template.with(
  title: "文章分类",
  description: "按类别浏览所有文章",
)

= 文章分类

#import "/content/_meta.typ": posts

// 按 category 分组
#let grouped = (:)
#for post in posts {
  let cat = post.category
  if cat not in grouped {
    grouped.insert(cat, ())
  }
  grouped.at(cat).push(post)
}

// 按层级路径展开：一级分类 → h2，二级分类 → h3，依次类推
#let keys = grouped.keys().sorted()
#for (i, cat) in keys.enumerate() {
  let parts = if cat == "" {
    ("未分类",)
  } else {
    cat.split("/")
  }

  // 与上一个分类的公共前缀（Typst 无可变变量，直接取上一个 key 计算）
  let prev-parts = if i > 0 {
    let prev-cat = keys.at(i - 1)
    if prev-cat == "" {
      ("未分类",)
    } else {
      prev-cat.split("/")
    }
  } else {
    ()
  }
  let n = 0
  while n < parts.len() and n < prev-parts.len() and parts.at(n) == prev-parts.at(n) {
    n += 1
  }

  // 只输出新出现的层级标题
  for j in range(n, parts.len()) {
    if j == 0 {
      html.h2(class: "heading-year", parts.at(j))
    } else {
      html.h3(class: "heading-month", parts.at(j))
    }
  }

  // 该分类下的文章按日期倒序
  let cat-posts = grouped.at(cat).sorted(key: p => p.date)
  for post in cat-posts.rev() {
    html.div(class: "blog-entry", {
      html.div(
        class: "blog-entry-date",
        post.date.display(),
      )
      html.div(class: "blog-entry-content", {
        html.a(href: site-link(post.url), post.title)
      })
    })
  }
}
