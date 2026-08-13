#import "/config.typ": template, site-link

#show: template.with(
  title: "404 - 页面未找到",
  description: "你访问的页面不存在。",
)

= 404

其实有一种可能，就是一种可能，也就是说，这个页面的确*不存在！*#footnote[作为注释，我赞同正文的观点]

#link(site-link("/"))[← 返回首页]
