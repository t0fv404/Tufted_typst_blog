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
  // Apply styling
  show: template-math
  show: template-refs
  show: template-notes
  show: template-figures
  show: template-links
  show: template-byline.with(author: author, date: date, extra-info: extra-info)

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
          website-url: website-url,
          image-path: image-path,
          feed-dir: feed-dir,
        )

        // load CSS
        let base-css = (
          "https://cdnjs.cloudflare.com/ajax/libs/tufte-css/1.8.0/tufte.min.css",
          "/css/tufted.css",
          "/css/theme.css",
          "/css/rss.css",
        )
        for (css-link) in (base-css + css).dedup() {
          html.link(rel: "stylesheet", href: css-link)
        }

        // load JS scripts
        let base-js = (
          "/js/code-blocks.js",
          "/js/format-headings.js",
          "/js/theme-toggle.js",
          "/js/rss-copy.js",
          "/js/marginnote-toggle.js",
          "/js/toc.js",
          "/js/back-to-top.js",
          "/js/math-copy.js",
        )
        for (js-src) in (base-js + js-scripts).dedup() {
          html.script(src: js-src)
        }
      })

      // Body
      html.body({
        // Custom header elements (site header, not navigation)
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

        // Add website navigation
        html.header(
          class: "site-header",
          if header-links != none {
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
                  html.a(href: href, title)
                }
                html.elem(
                  "button",
                  attrs: (
                    id: "rss-copy",
                    class: "rss-btn",
                    type: "button",
                    "aria-label": "Copy RSS link",
                  ),
                  "",
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
          }
        )

        // Table of contents drawer
        html.elem(
          "aside",
          attrs: (id: "toc-drawer", class: "toc-drawer"),
          {
            html.div(class: "toc-drawer-inner")
            html.div(id: "toc-resize-handle", class: "toc-resize-handle")
          },
        )

        // Main content
        html.article(
          html.section(content),
        )

        // Custom footer elements
        html.footer({
          for (i, element) in footer-elements.enumerate() {
            element
            if i < footer-elements.len() - 1 {
              html.br()
            }
          }
        })
      })
    },
  )
}
