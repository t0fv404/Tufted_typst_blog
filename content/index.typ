#import "../config.typ": template, site-link
#import "../tufted-lib/tufted.typ" as tufted

#show: template

= 文章列表

#import "_meta.typ": posts

#let sorted = posts.sorted(key: p => p.date)
#let n = sorted.len()

#let prev-year = ""
#let prev-month = ""
#for i in range(n) {
  let post = sorted.at(n - 1 - i)
  let yd = post.date.display("[year]")
  let md = post.date.display("[month]")

  if yd != prev-year {
    html.h3(class: "heading-year", yd)
    prev-year = yd
    prev-month = ""
  }
  if md != prev-month {
    let month-names = ("1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月")
    let mi = int(md)
    let mname = if mi >= 1 and mi <= 12 { month-names.at(mi - 1) } else { md + "月" }
    html.h4(class: "heading-month", mname)
    prev-month = md
  }

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
