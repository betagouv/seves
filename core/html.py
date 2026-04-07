ALLOWED_TAGS = ["h2", "p", "ol", "li", "span", "strong", "br", "s", "em", "u"]
ALLOWED_BG_COLORS = [
    "yellow-tournesol-925-125",
    "green-emeraude-950-100",
    "green-archipel-950-100",
    "pink-macaron-925-125",
    "purple-glycine-925-125",
    "blue-ecume-925-125",
]
ALLOWED_COLORS = [
    "grey-925-125",
    "blue-france-sun-113-625",
    "blue-france-main-525",
    "success-425-625",
    "purple-glycine-main-494",
    "error-425-625",
]


def _get_style_value(style, selector):
    return style.split(selector)[-1].replace(";", "").strip()


def inline_styles_to_classes(soup):
    for element in soup.find_all(style=True):
        classes = element.get("class", [])
        styles = element["style"].split(";")
        for style in styles:
            style = style.strip()
            if style.startswith("background-color:"):
                for color in ALLOWED_BG_COLORS:
                    if color in _get_style_value(style, "background-color:"):
                        classes.append(f"background-color-{color}")
            if style.startswith("color:"):
                for color in ALLOWED_COLORS:
                    if color in _get_style_value(style, "color:"):
                        classes.append(f"text-color-{color}")
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
