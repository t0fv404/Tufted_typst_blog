#let template-links(site-url: none, content) = {
  // Open external links and non-web resources in a new tab
  show link: it => {
    if type(it.dest) == str {
      // Absolute URLs belonging to this site are internal navigation links.
      let site-root = if site-url == none { none } else { site-url.trim("/", at: end) }
      let is-http = it.dest.starts-with("http")
      let is-internal-site = site-root != none and it.dest.starts-with(site-root)
      let is-external = is-http and not is-internal-site

      // 2. Determine whether it is a "non-web page resource"
      let is-resource = not is-http and it.dest.contains(".") and not it.dest.ends-with(".html")

      if is-external or is-resource {
        html.a(
          href: it.dest,
          target: "_blank",
          rel: ("noopener", "noreferrer"),
          it.body,
        )
      } else {
        it // Internal page link or anchor link (#top), keep as is
      }
    } else {
      it // Internal reference object, keep as is
    }
  }

  content
}
