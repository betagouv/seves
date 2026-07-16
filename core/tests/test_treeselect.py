from enum import auto

from django import forms
from django.db.models import TextChoices
from django.template import Context, Template
from django.utils.functional import classproperty
from dsfr.forms import DsfrBaseForm
from playwright.sync_api import Page, expect
import pytest

from core.mixins import GroupedChoicesMixin
from core.tests.pages import TreeselectPage
from core.widgets import TreeselectCheckbox, TreeselectGroup, TreeselectRadio


class TestChoices(GroupedChoicesMixin, TextChoices):
    TOULOUSE = auto(), "Europe > France > Toulouse"
    PARIS = auto(), "Europe > France > Paris"
    FRANCE = auto(), "Europe > France"
    MUNICH = auto(), "Europe > Allemagne > Munich"
    BERLIN = auto(), "Europe > Allemagne > Berlin"
    PORTE_DE_BRANDEBOURG = auto(), "Europe > Allemagne > Berlin > Porte de Brandebourg"
    HAMBOURG = auto(), "Europe > Allemagne > Hambourg"
    CHILI = auto(), "Amérique > Amérique du sud > Chili"
    ARGENTINE = auto(), "Amérique > Amérique du sud > Argentine"
    NICARAGUA = auto(), "Amérique > Amérique centrale > Nicaragua"
    MEXIQUE = auto(), "Amérique > Amérique centrale > Mexique"
    BRESIL = auto(), "Amérique > Amérique du sud > Brésil"
    SAO_POLO = auto(), "Amérique > Amérique du sud > Brésil > São Paulo"

    @classproperty
    def les_plus_courants(cls):
        return cls.MUNICH, cls.PORTE_DE_BRANDEBOURG, cls.CHILI, cls.BRESIL, cls.SAO_POLO

    @classproperty
    def treeselect_choices(cls):
        return (
            TreeselectGroup(
                label="Les plus choisis",
                choices=tuple(it.get_treeselect_item(html_name_prefix="shortcut") for it in cls.les_plus_courants),
                can_expand=False,
                categorised_label=None,
            ),
            TreeselectGroup(
                label="Liste complète",
                choices=cls.treeselect_groups,
                can_expand=False,
                categorised_label=None,
            ),
        )


class TestForm(DsfrBaseForm):
    animal_radio = forms.ChoiceField(
        required=False, choices=TestChoices, widget=TreeselectRadio(choices=TestChoices.treeselect_choices)
    )

    animal_checkbox = forms.ChoiceField(
        required=False, choices=TestChoices, widget=TreeselectCheckbox(choices=TestChoices.treeselect_choices)
    )


@pytest.fixture
def navigate_to_form(live_server, page: Page):
    def _navigate_to_form(form):
        # language=html
        template = """
            {% extends "core/base.html" %}
            {% load dsfr_tags %}

            {% block content %}
                <div class='fr-container fr-py-4v'>
                    <div class='fr-grid-row fr-grid-row--center'>
                        <div class='fr-col-12 fr-col-sm-6'>
                            {% for field in form %}
                                <div data-testid="{{ field.name }}">
                                    {% dsfr_form_field field %}
                                </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            {% endblock %}
        """

        def resolve(route):
            body = Template(template).render(Context({"form": form, "media": form.media}))
            route.fulfill(status=200, body=body, content_type="text/html")

        page.route("**/test-treeselect/", resolve)
        page.goto(f"{live_server.url}/test-treeselect/")

    yield _navigate_to_form
    page.unroute("**/test-treeselect/")


def test_treeselect_all_radio_with_same_value_are_selected(navigate_to_form, page: Page):
    navigate_to_form(TestForm())
    treeselect_animal_radio = TreeselectPage(page, page.get_by_test_id("animal_radio"))

    # First case: select result inside accordion
    treeselect_animal_radio.check_option(*TestChoices.MUNICH.splitted_label)
    options = treeselect_animal_radio.options_container.get_by_label(TestChoices.MUNICH.uncategorized_label, exact=True)
    assert options.count() == 2
    for option in options.all():
        expect(option).to_be_checked()

    # Unselect result
    treeselect_animal_radio.uncheck_by_tag(TestChoices.MUNICH.uncategorized_label)
    options = treeselect_animal_radio.options_container.get_by_label(TestChoices.MUNICH.uncategorized_label, exact=True)
    assert options.count() == 2
    for option in options.all():
        expect(option).not_to_be_checked()

    # Select by shortcut
    with treeselect_animal_radio.opened_treeselect():
        treeselect_animal_radio.container.locator(
            f"[name^='shortcut'][value='{TestChoices.MUNICH.value}']"
        ).set_checked(True, force=True)
    options = treeselect_animal_radio.options_container.get_by_label(TestChoices.MUNICH.uncategorized_label, exact=True)
    assert options.count() == 2
    for option in options.all():
        expect(option).to_be_checked()


def test_search(navigate_to_form, page: Page):
    navigate_to_form(TestForm())
    treeselect_animal_radio = TreeselectPage(page, page.get_by_test_id("animal_radio"))

    with treeselect_animal_radio.opened_treeselect():
        expect(treeselect_animal_radio.container.get_by_text("Amérique", exact=True)).to_be_visible()
        expect(treeselect_animal_radio.container.get_by_text("Europe", exact=True)).to_be_visible()
        expect(
            treeselect_animal_radio.container.get_by_text(TestChoices.FRANCE.uncategorized_label, exact=True)
        ).not_to_be_visible()

        treeselect_animal_radio.search(TestChoices.FRANCE.uncategorized_label)

        search_results = treeselect_animal_radio.container.get_by_text(TestChoices.FRANCE.uncategorized_label).all()
        expect(treeselect_animal_radio.container.get_by_text("Amérique", exact=True)).not_to_be_visible()
        expect(treeselect_animal_radio.container.get_by_text("Europe", exact=True)).to_be_visible()

        for it in treeselect_animal_radio.container.get_by_text(TestChoices.MUNICH.uncategorized_label).all():
            expect(it).not_to_be_visible()

        assert set(it.inner_text() for it in search_results) == {
            "France",  # Group input text
            "Ouvrir la catégorie\nFrance",  # Group button text
        }


def test_treeselect_button_label(navigate_to_form, page: Page):
    navigate_to_form(TestForm())
    treeselect_animal_radio = TreeselectPage(page, page.get_by_test_id("animal_checkbox"))

    treeselect_animal_radio.check_option(*TestChoices.HAMBOURG.splitted_label)
    assert treeselect_animal_radio.main_button.inner_text() == TestChoices.HAMBOURG.label
    treeselect_animal_radio.check_option(*TestChoices.MUNICH.splitted_label)
    assert treeselect_animal_radio.main_button.inner_text() == "2 éléments"
    treeselect_animal_radio.uncheck_all()
    assert treeselect_animal_radio.main_button.inner_text() == "Choisir dans la liste"


def test_checkbox_options_and_parent_behavior(navigate_to_form, page: Page):
    navigate_to_form(TestForm())
    treeselect_animal_radio = TreeselectPage(page, page.get_by_test_id("animal_checkbox"))

    # Test that checking group's input auto-checks children
    treeselect_animal_radio.check_option(*TestChoices.FRANCE.splitted_label)

    for it in (TestChoices.TOULOUSE, TestChoices.PARIS):
        expect(treeselect_animal_radio.get_option(it)).to_be_checked()

    assert set(it.text_content().strip() for it in treeselect_animal_radio.selected_tags.all()) == {
        TestChoices.FRANCE.uncategorized_label,
        TestChoices.TOULOUSE.uncategorized_label,
        TestChoices.PARIS.uncategorized_label,
    }

    # Test that unchecking on children unchecks parent without unchecking other children
    treeselect_animal_radio.uncheck_option(*TestChoices.PARIS.splitted_label)
    expect(treeselect_animal_radio.get_option(TestChoices.FRANCE)).not_to_be_checked()
    expect(treeselect_animal_radio.get_option(TestChoices.TOULOUSE)).to_be_checked()

    assert set(it.text_content().strip() for it in treeselect_animal_radio.selected_tags.all()) == {
        TestChoices.TOULOUSE.uncategorized_label
    }

    # Test that checking all children auto-checks parent
    for it in (TestChoices.TOULOUSE, TestChoices.PARIS):
        treeselect_animal_radio.check_option(*it.splitted_label)

    expect(treeselect_animal_radio.get_option(TestChoices.FRANCE)).to_be_checked()

    assert set(it.text_content().strip() for it in treeselect_animal_radio.selected_tags.all()) == {
        TestChoices.FRANCE.uncategorized_label,
        TestChoices.TOULOUSE.uncategorized_label,
        TestChoices.PARIS.uncategorized_label,
    }

    # Test that unchecking group's input auto-unchecks children
    treeselect_animal_radio.uncheck_option(*TestChoices.FRANCE.splitted_label)

    for it in (TestChoices.TOULOUSE, TestChoices.PARIS):
        expect(treeselect_animal_radio.get_option(it)).not_to_be_checked()

    assert treeselect_animal_radio.selected_tags.count() == 0

    # Test that unchecking one child from selected tag auto-unchecks parent
    for it in (TestChoices.TOULOUSE, TestChoices.PARIS):
        treeselect_animal_radio.check_option(*it.splitted_label)

    expect(treeselect_animal_radio.get_option(TestChoices.FRANCE)).to_be_checked()

    assert set(it.text_content().strip() for it in treeselect_animal_radio.selected_tags.all()) == {
        TestChoices.FRANCE.uncategorized_label,
        TestChoices.TOULOUSE.uncategorized_label,
        TestChoices.PARIS.uncategorized_label,
    }

    treeselect_animal_radio.uncheck_by_tag(TestChoices.PARIS.uncategorized_label)
    expect(treeselect_animal_radio.get_option(TestChoices.FRANCE)).not_to_be_checked()
    expect(treeselect_animal_radio.get_option(TestChoices.TOULOUSE)).to_be_checked()

    assert set(it.text_content().strip() for it in treeselect_animal_radio.selected_tags.all()) == {
        TestChoices.TOULOUSE.uncategorized_label
    }

    # Test that unchecking parent from selected tag auto-unchecks all children
    for it in (TestChoices.TOULOUSE, TestChoices.PARIS):
        treeselect_animal_radio.check_option(*it.splitted_label)

    expect(treeselect_animal_radio.get_option(TestChoices.FRANCE)).to_be_checked()

    assert set(it.text_content().strip() for it in treeselect_animal_radio.selected_tags.all()) == {
        TestChoices.FRANCE.uncategorized_label,
        TestChoices.TOULOUSE.uncategorized_label,
        TestChoices.PARIS.uncategorized_label,
    }

    treeselect_animal_radio.uncheck_by_tag(TestChoices.FRANCE.uncategorized_label)
    for it in (TestChoices.FRANCE, TestChoices.TOULOUSE, TestChoices.PARIS):
        expect(treeselect_animal_radio.get_option(it)).not_to_be_checked()

    assert treeselect_animal_radio.selected_tags.count() == 0


def test_shortcut_behavior(navigate_to_form, page: Page):
    navigate_to_form(TestForm())
    treeselect = TreeselectPage(page, page.get_by_test_id("animal_checkbox"))

    # Test that checking option also checks its shortcut
    treeselect.check_option(*TestChoices.PORTE_DE_BRANDEBOURG.splitted_label)
    options = treeselect.container.locator(f'input[value="{TestChoices.PORTE_DE_BRANDEBOURG.value}"]').all()
    assert len(options) == 2
    for option in options:
        expect(option).to_be_checked()

    # Test that unchecking option also unchecks its shortcut
    treeselect.uncheck_option(*TestChoices.PORTE_DE_BRANDEBOURG.splitted_label)
    for option in options:
        expect(option).not_to_be_checked()


def test_check_group_input_opens_group_accordion(navigate_to_form, page: Page):
    navigate_to_form(TestForm())

    for treeselect in (
        TreeselectPage(page, page.get_by_test_id("animal_radio")),
        TreeselectPage(page, page.get_by_test_id("animal_checkbox")),
    ):
        with treeselect.opened_treeselect():
            treeselect.check_option(*TestChoices.BERLIN.splitted_label, close_after=False)
            for option in treeselect.container.get_by_label(TestChoices.PORTE_DE_BRANDEBOURG.uncategorized_label).all():
                expect(option).to_be_visible()


def test_checking_group_input_opens_group_dropdown(navigate_to_form, page: Page):
    navigate_to_form(TestForm())
    treeselect_animal_radio = TreeselectPage(page, page.get_by_test_id("animal_checkbox"))

    treeselect_animal_radio.open_treeselect()
    expect(treeselect_animal_radio.get_option(TestChoices.TOULOUSE)).not_to_be_visible()
    expect(treeselect_animal_radio.get_option(TestChoices.PARIS)).not_to_be_visible()
    treeselect_animal_radio.check_option(*TestChoices.FRANCE.splitted_label, close_after=False)
    expect(treeselect_animal_radio.get_option(TestChoices.TOULOUSE)).to_be_visible()
    expect(treeselect_animal_radio.get_option(TestChoices.PARIS)).to_be_visible()


def test_unselect_all_button(navigate_to_form, page: Page):
    navigate_to_form(TestForm())
    treeselect_animal_radio = TreeselectPage(page, page.get_by_test_id("animal_checkbox"))

    expect(treeselect_animal_radio.selected_tags).to_have_count(0)
    treeselect_animal_radio.open_treeselect()
    treeselect_animal_radio.check_option(*TestChoices.FRANCE.splitted_label, close_after=False)
    expect(treeselect_animal_radio.selected_tags).to_have_count(3)
    treeselect_animal_radio.uncheck_all_by_unselect_button()
    expect(treeselect_animal_radio.selected_tags).to_have_count(0)
