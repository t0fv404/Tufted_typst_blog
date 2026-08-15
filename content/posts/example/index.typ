#import "/config.typ": template

#show: template.with(
  title: "示例文章",
  description: "这是一篇示例文章，展示如何声明元数据。",
  date: datetime(year: 2026, month: 8, day: 13),
  modified: datetime(year: 2026, month: 8, day: 13),
  category: "示例分类",
  lang: "zh",
)

= 示例文章

这是一篇示例文章，展示如何编写一篇文章。

- 元数据在 `#show: template.with(...)` 中声明
- `category` 未声明时自动归入"未分类"
- `modified` 会在 byline 中显示为"更新于 ..."

== 一级标题

这是正文内容。

```c
int main(){
  return 0;
}
```

=== 二级标题

这里可以写更多内容。

=== 另一个二级标题

足够多的标题会让抽屉式目录自动生成树形结构。
