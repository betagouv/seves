from bs4 import BeautifulSoup
import pytest

from core.html import filter_tags_and_attributes


@pytest.mark.parametrize(
    "html,expected",
    [
        (
            '<p class="ql-indent-1" style="color: red"><span class="text-color-blue" onclick="foo()">Texte</span></p>',
            '<p class="ql-indent-1"><span class="text-color-blue">Texte</span></p>',
        ),
        (
            '<p>Contactez <a href="mailto:test@example.com">test@example.com</a></p>',
            "<p>Contactez test@example.com</p>",
        ),
        (
            "<table><tbody><tr><td>Cellule 1</td><td>Cellule 2</td></tr></tbody></table>",
            "<p>Cellule 1</p><p>Cellule 2</p>",
        ),
        (
            "<table><tr><td><p>Bonjour,</p><p>Cordialement</p></td></tr></table>",
            "<p>Bonjour,</p><p>Cordialement</p>",
        ),
        ("<blockquote>Message d'origine</blockquote>", "<p>Message d'origine</p>"),
        ("<h1>Titre</h1>", "<p>Titre</p>"),
        ("<p>Texte<script>alert(1)</script><style>p {color: red}</style></p>", "<p>Texte</p>"),
    ],
)
def test_filter_tags_and_attributes_keeps_text_of_unsupported_tags(html, expected):
    soup = BeautifulSoup(html, "html.parser")
    filter_tags_and_attributes(soup)
    assert str(soup) == expected
