ALLOWED_TAGS = ["h2", "p", "ol", "li", "span", "strong", "br", "s", "em", "u", "ul"]
REMOVED_WITH_CONTENT_TAGS = ["script", "style"]
BLOCK_TAGS = [
    "address",
    "article",
    "aside",
    "blockquote",
    "dd",
    "div",
    "dl",
    "dt",
    "figcaption",
    "figure",
    "footer",
    "h1",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "main",
    "nav",
    "pre",
    "section",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
]


def filter_tags_and_attributes(soup):
    """
    Only keep the tags supported by the editor without losing the text (e.g. when pasting a formatted email):
    - unsupported block elements are converted into paragraphs, or unwrapped if they contain other blocks
    - unsupported inline elements are unwrapped
    """
    for tag in soup.find_all(True):
        if tag.decomposed:
            continue
        if tag.name in REMOVED_WITH_CONTENT_TAGS:
            tag.decompose()
        elif tag.name in ALLOWED_TAGS:
            tag.attrs = {"class": tag.get("class")} if tag.get("class") else {}
        elif tag.name in BLOCK_TAGS and not tag.find(BLOCK_TAGS + ["p", "h2", "ol", "ul", "li"]):
            tag.name = "p"
            tag.attrs = {}
        else:
            tag.unwrap()


def replace_ol_elements_with_ul(soup):
    """
    This is needed because the editor will use the ol tag even if we ask for simple bullet point list (which should be
    using an ul tag).
    This can be done in this way because we have no use for the ol tag for now in the editor. This simplifies the display
    of the message when using the DSFR (the correct style is rendered)
    """
    for ol in soup.find_all("ol"):
        ol.name = "ul"


def html_to_simple_text(soup):
    return str(soup.get_text(separator="\n\n").strip())
