ALLOWED_TAGS = ["h2", "p", "ol", "li", "span", "strong", "br", "s", "em", "u", "ul"]


def _get_style_value(style, selector):
    return style.split(selector)[-1].replace(";", "").strip()


def filter_tags_and_attributes(soup):
    for tag in soup.find_all(True):
        if tag.name not in ALLOWED_TAGS:
            tag.decompose()
        else:
            tag.attrs = {"class": tag.get("class")} if tag.get("class") else {}


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
