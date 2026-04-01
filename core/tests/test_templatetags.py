from unittest import mock

from django.template import Context, Template
from pytest_django.asserts import assertHTMLEqual

from core.templatetags import and_more_ellipsis_tooltip


def test_and_more_ellipsis_empty():
    context = Context({"items": []})
    actual = Template(
        """
        {% load and_more_ellipsis_tooltip %}
        {% and_more_ellipsis_tooltip items tooltip_prefix="Autre{plural} élément{plural} :" %}
        """
    ).render(context)

    assertHTMLEqual('<span class="empty-value">Vide</span>', actual)


def test_and_more_ellipsis_1_element():
    context = Context({"items": ["élement 1"]})
    actual = Template(
        "{% load and_more_ellipsis_tooltip %}"
        "{% and_more_ellipsis_tooltip items "
        'tooltip_prefix="Autre{plural} élément{plural} :" '
        'tooltip_id="test" %}'
    ).render(context)

    assertHTMLEqual(
        """élement 1""",
        actual,
    )


def test_and_more_ellipsis_2_elements():
    context = Context({"items": ["élement 1", "élément 2"]})
    actual = Template(
        "{% load and_more_ellipsis_tooltip %}"
        "{% and_more_ellipsis_tooltip items "
        'tooltip_prefix="Autre{plural} élément{plural} :" '
        'tooltip_id="test" %}'
    ).render(context)

    assertHTMLEqual(
        """
            élement 1 <p aria-describedby="test" class="fr-tag">et 1 autre</p>
            <span aria-hidden="true" class="fr-placement fr-tooltip" id="test" role="tooltip">
                Autre élément : élément 2
            </span>
            """,
        actual,
    )


@mock.patch(f"{and_more_ellipsis_tooltip.__name__}.get_random_string")
def test_and_more_ellipsis_auto_tooltip_id(get_random_string_mock: mock.MagicMock):
    get_random_string_mock.return_value = "abcd"

    context = Context({"items": ["élement 1", "élément 2"]})
    actual = Template(
        "{% load and_more_ellipsis_tooltip %}"
        "{% and_more_ellipsis_tooltip items "
        'tooltip_prefix="Autre{plural} élément{plural} :" %}'
    ).render(context)

    assertHTMLEqual(
        """
            élement 1 <p aria-describedby="tooltip-abcd" class="fr-tag">et 1 autre</p>
            <span aria-hidden="true" class="fr-placement fr-tooltip" id="tooltip-abcd" role="tooltip">
                Autre élément : élément 2
            </span>
            """,
        actual,
    )


def test_and_more_ellipsis_3_elements():
    context = Context({"items": ["élement 1", "élément 2", "élément 3"]})
    actual = Template(
        "{% load and_more_ellipsis_tooltip %}"
        "{% and_more_ellipsis_tooltip items "
        'tooltip_prefix="Autre{plural} élément{plural} :" '
        'tooltip_id="test" %}'
    ).render(context)

    assertHTMLEqual(
        """
            élement 1 <p aria-describedby="test" class="fr-tag">et 2 autres</p>
            <span aria-hidden="true" class="fr-placement fr-tooltip" id="test" role="tooltip">
                Autres éléments : élément 2, élément 3
            </span>
            """,
        actual,
    )


def test_and_more_ellipsis_tooltip_prefix_plural():
    context = Context({"items": ["élement 1", "élément 2", "élément 3"]})
    actual = Template(
        "{% load and_more_ellipsis_tooltip %}"
        "{% and_more_ellipsis_tooltip items "
        'tooltip_prefix="Autre{plural} élément{plural} :" '
        'tooltip_prefix_plural="Éléments supplémentaires :" '
        'tooltip_id="test" %}'
    ).render(context)

    assertHTMLEqual(
        """
            élement 1 <p aria-describedby="test" class="fr-tag">et 2 autres</p>
            <span aria-hidden="true" class="fr-placement fr-tooltip" id="test" role="tooltip">
                Éléments supplémentaires : élément 2, élément 3
            </span>
            """,
        actual,
    )


def test_and_more_ellipsis_field_resolution():
    class InnerTest:
        def __init__(self, value):
            self.value = value

        def some_value(self):
            return f"some_value {self.value}"

    class Test:
        def __init__(self, value):
            self.inner = InnerTest(value)

    context = Context({"items": [Test(1), Test(2), Test(3)]})
    actual = Template(
        "{% load and_more_ellipsis_tooltip %}"
        "{% and_more_ellipsis_tooltip items "
        'tooltip_prefix="Autre{plural} élément{plural} :" '
        'field="inner.some_value" '
        'tooltip_id="test" %}'
    ).render(context)

    assertHTMLEqual(
        """
            some_value 1 <p aria-describedby="test" class="fr-tag">et 2 autres</p>
            <span aria-hidden="true" class="fr-placement fr-tooltip" id="test" role="tooltip">
                Autres éléments : some_value 2, some_value 3
            </span>
            """,
        actual,
    )
