#import "math.typ": template-math
#import "refs.typ": template-refs
#import "notes.typ": template-notes
#import "figures.typ": template-figures
#import "blog-entry.typ": blog-entry
#import "layout.typ": full-width, margin-note
#import "links.typ": template-links
#import "metadata.typ": metadata
#import "byline.typ": template-byline

/// The main wrapper function of Tufted Blog Template.
///
/// Used to generate a complete HTML page structure,
/// including SEO metadata, CSS/JS resource loading, and header and footer layout.
#let tufted-web(
  header-links: (:),

  // Meta data
  title: "",
  author: none,
  description: "",
  lang: "zh",
  date: none,
  modified: none,
  category: none,
  extra-info: none,
  website-title: "",
  website-url: none,

  // For SEO
  image-path: none,

  // For RSS
  feed-dir: (),

  // Custom header and footer
  header-elements: (),
  footer-elements: (),

  // Custom CSS and JS Scripts
  css: ("/css/custom.css",),
  js-scripts: (),

  content,
) = {
  let effective-site-url = sys.inputs.at("site-url", default: website-url)
  let site-root = if effective-site-url == none { "" } else { effective-site-url.trim("/", at: end) }
  let site-link = path => site-root + "/" + path.trim("/", at: start)

  // Apply styling
  show: template-math
  show: template-refs
  show: template-notes
  show: template-figures
  show: template-links.with(site-url: effective-site-url)
  show: template-byline.with(author: author, date: date, extra-info: extra-info, category: category, modified: modified)

  set text(lang: lang)

  html.html(
    lang: lang,
    {
      // Head
      html.head({
        // All metadata
        metadata(
          title: title,
          author: author,
          description: description,
          lang: lang,
          date: date,
          website-title: website-title,
          website-url: effective-site-url,
          image-path: image-path,
          feed-dir: feed-dir,
        )
        html.meta(name: "site-url", content: site-link("/"))

        // load CSS
        let base-css = (
          "https://cdnjs.cloudflare.com/ajax/libs/tufte-css/1.8.0/tufte.min.css",
          "css/tufted.css",
          "css/theme.css",
          "css/rss.css",
          "css/search.css",
        )
        for (css-link) in (base-css + css).dedup() {
          html.link(rel: "stylesheet", href: if css-link.starts-with("http") { css-link } else { site-link(css-link) })
        }

        // load JS scripts
        let base-js = (
          site-link("js/code-blocks.js"),
          site-link("js/format-headings.js"),
          site-link("js/theme-toggle.js"),
          site-link("js/search.js"),
          site-link("js/marginnote-toggle.js"),
          site-link("js/toc.js"),
          site-link("js/back-to-top.js"),
          site-link("js/math-copy.js"),
          site-link("js/copy-button.js"),
          site-link("js/custom.js"),
        )
        for (js-src) in (base-js + js-scripts).dedup() {
          html.script(src: if js-src.starts-with("http") { js-src } else { site-link(js-src) })
        }
      })

      // Body
      html.body({
        // Custom header elements (site header, not navigation)
        if header-elements.len() > 0 {
          html.header(
            class: "site-header",
            {
              for (i, element) in header-elements.enumerate() {
                element
                if i < header-elements.len() - 1 {
                  html.br()
                }
              }
            },
          )
        }

        // Add website navigation
        if header-links != none {
          html.header(
            class: "site-nav-header",
            html.nav(
              class: "site-nav",
              {
                html.elem(
                  "button",
                  attrs: (
                    id: "toc-toggle",
                    class: "toc-toggle-btn",
                    type: "button",
                    "aria-label": "切换目录",
                  ),
                  html.elem(
                    "svg",
                    attrs: (
                      "xmlns": "http://www.w3.org/2000/svg",
                      width: "1em",
                      height: "1em",
                      fill: "none",
                      stroke: "currentColor",
                      "stroke-width": "2",
                      "stroke-linecap": "round",
                      viewBox: "0 0 24 24",
                    ),
                    html.elem(
                      "path",
                      attrs: (d: "M4 6h16M4 12h16M4 18h16"),
                    ),
                  ),
                )
                for (href, title) in header-links {
                  html.a(href: site-link(href), title)
                }
                html.div(
                  class: "search-box",
                  {
                    html.elem(
                      "button",
                      attrs: (
                        id: "search-toggle",
                        class: "search-toggle-btn",
                        type: "button",
                        "aria-label": "搜索文章",
                      ),
                      "",
                    )
                    html.elem(
                      "input",
                      attrs: (
                        id: "search-input",
                        class: "search-input",
                        type: "search",
                        placeholder: "可使用日期，内容，标题以及分类来搜索相关文章，使用空格以区分多个关键字",
                        autocomplete: "off",
                        "aria-label": "搜索文章",
                      ),
                    )
                    html.div(id: "search-results", class: "search-results")
                  },
                )
                html.elem(
                  "button",
                  attrs: (
                    id: "rss-copy",
                    class: "rss-btn",
                    type: "button",
                    "aria-label": "Copy RSS link",
                    "data-copy-value": site-link("feed.xml"),
                    "data-copy-label": "RSS 链接已复制",
                  ),
                  html.elem(
                    "svg",
                    attrs: (
                      "xmlns": "http://www.w3.org/2000/svg",
                      width: "1em",
                      height: "1em",
                      fill: "currentColor",
                      viewBox: "0 0 256 256",
                    ),
                    html.elem(
                      "path",
                      attrs: (
                        d: "M208,32H48A16,16,0,0,0,32,48V208a16,16,0,0,0,16,16H208a16,16,0,0,0,16-16V48A16,16,0,0,0,208,32ZM76,200a12,12,0,1,1,12-12A12,12,0,0,1,76,200Zm52,0a8,8,0,0,1-8-8,56.06,56.06,0,0,0-56-56,8,8,0,0,1,0-16,72.08,72.08,0,0,1,72,72A8,8,0,0,1,128,200Zm48,0a8,8,0,0,1-8-8A104.11,104.11,0,0,0,64,88a8,8,0,0,1,0-16A120.13,120.13,0,0,1,184,192,8,8,0,0,1,176,200Z",
                      ),
                    ),
                  ),
                )
                html.elem(
                  "button",
                  attrs: (
                    id: "theme-toggle",
                    class: "theme-toggle-btn",
                    type: "button",
                    aria-label: "Toggle theme",
                  ),
                  "",
                )
              },
            )
          )
        }

        // Table of contents drawer
        if header-links != none {
          html.elem(
            "aside",
            attrs: (id: "toc-drawer", class: "toc-drawer"),
            {
              html.div(class: "toc-drawer-inner")
              html.div(id: "toc-resize-handle", class: "toc-resize-handle")
            },
          )
        }

        // Main content
        html.article(
          html.section(content),
        )

        // Custom footer elements
        if footer-elements.len() > 0 {
          html.footer({
            for (i, element) in footer-elements.enumerate() {
              element
              if i < footer-elements.len() - 1 {
                html.br()
              }
            }
          })
        }
      })
    },
  )
}
