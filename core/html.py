ALLOWED_TAGS = ["h2", "p", "ol", "li", "span", "strong", "br", "s", "em", "u"]
BG_COLOR_TO_CLASS = {
    "rgb(184, 254, 201)": "background-color-green",
    "rgb(255, 233, 230)": "background-color-red",
    "rgb(0, 99, 203)": "background-color-light-blue",
}
TEXT_COLOR_TO_CLASS = {
    "rgb(0, 0, 145)": "text-color-blue",
    "rgb(206, 5, 0)": "text-color-red",
    "rgb(24, 117, 60)": "text-color-green",
}


def _get_style_value(style, selector):
    return style.split(selector)[-1].replace(";", "").strip()


def inline_styles_to_classes(soup):
    for element in soup.find_all(style=True):
        classes = element.get("class", [])
        styles = element["style"].split(";")
        for style in styles:
            style = style.strip()
            if style.startswith("background-color:"):
                bg_class = BG_COLOR_TO_CLASS.get(_get_style_value(style, "background-color:"))
                if bg_class:
                    classes.append(bg_class)
            if style.startswith("color:"):
                color_class = TEXT_COLOR_TO_CLASS.get(_get_style_value(style, "color:"))
                if color_class:
                    classes.append(color_class)
        element["class"] = list(classes)


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
