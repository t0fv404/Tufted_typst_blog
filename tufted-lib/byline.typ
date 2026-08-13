/// Render article metadata below the first level-one heading.
#let article-byline(author: none, date: none, extra-info: none, category: none, modified: none) = {
  let formatted-date = if date != none {
    if type(date) == datetime {
      (display: date.display(), datetime: date.display())
    } else {
      (display: date, datetime: none)
    }
  } else {
    (display: none, datetime: none)
  }

  let formatted-modified = if modified != none {
    if type(modified) == datetime {
      (display: modified.display(), datetime: modified.display())
    } else {
      (display: modified, datetime: none)
    }
  } else {
    (display: none, datetime: none)
  }

  html.div(
    class: "article-byline",
    {
      if author != none or date != none or category != none or modified != none {
        html.p(
          class: "article-byline-main",
          {
            if author != none {
              html.span(class: "article-author", author)
            }
            if author != none and date != none {
              html.span(class: "article-byline-separator", " · ")
            }
            if date != none {
              let attrs = if formatted-date.datetime != none {
                (class: "article-date", datetime: formatted-date.datetime)
              } else {
                (class: "article-date")
              }

              html.elem("time", attrs: attrs, formatted-date.display)
            }
            if (author != none or date != none) and category != none {
              html.span(class: "article-byline-separator", " · ")
            }
            if category != none {
              html.span(class: "article-category", category)
            }
            if (author != none or date != none or category != none) and modified != none {
              html.span(class: "article-byline-separator", " · ")
            }
            if modified != none {
              let attrs = if formatted-modified.datetime != none {
                (class: "article-modified", datetime: formatted-modified.datetime)
              } else {
                (class: "article-modified")
              }

              html.span(class: "article-modified-prefix", "更新于 ")
              html.elem("time", attrs: attrs, formatted-modified.display)
            }
          },
        )
      }

      if extra-info != none {
        html.p(class: "article-extra-info", extra-info)
      }
    },
  )
}

/// Inject article metadata once, directly below the first level-one heading.
#let template-byline(content, author: none, date: none, extra-info: none, category: none, modified: none) = {
  if date != none or extra-info != none or category != none or modified != none {
    let injected = state("article-byline-injected", false)

    show heading.where(level: 1): it => {
      it
      context {
        if not injected.get() {
          injected.update(true)
          article-byline(author: author, date: date, extra-info: extra-info, category: category, modified: modified)
        }
      }
    }

    content
  } else {
    content
  }
}
