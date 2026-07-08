from contextlib import contextmanager
import functools
from functools import cached_property

from playwright.sync_api import Error as PlaywrightError, Locator, Page, expect

from core.mixins import GroupedChoicesMixin


def playwright_repeatable(maybe_func=None, timeout=None, retries=10):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            error = None
            old_timeout = expect._timeout
            new_timeout = timeout or (old_timeout or 5_000 / retries)
            for i in range(retries):
                try:
                    expect.set_options(timeout=new_timeout)
                    return func(*args, **kwargs)
                except (PlaywrightError, AssertionError) as e:
                    if error is not None:
                        e.__cause__ = error
                    error = e
                    continue
                finally:
                    expect.set_options(timeout=old_timeout)
            raise error

        return wrapper

    return decorator(maybe_func) if callable(maybe_func) else decorator


class ChoiceJSPage:
    @cached_property
    def _choice_widget_locator(self):
        locator = self.locator.locator(
            "xpath=descendant-or-self::*[contains(concat(' ',normalize-space(@class),' '),' choices ')]"
        )
        if len(locator.all()) == 0:
            return self.locator.locator(
                "xpath=ancestor-or-self::*[contains(concat(' ',normalize-space(@class),' '),' choices ')]"
            )
        return locator

    @property
    def choice_widget(self):
        return self._choice_widget_locator.first

    @property
    def dropdown(self):
        return self.choice_widget.locator(".choices__list.choices__list--dropdown")

    @property
    def click_zone(self):
        result = self.choice_widget.locator(".choices__list.choices__list--multiple + .choices__input")
        return result.first if result.count() > 0 else self.choice_widget

    def __init__(self, page: Page, sel_or_locator: str | Locator):
        self.locator = sel_or_locator if isinstance(sel_or_locator, Locator) else page.locator(sel_or_locator)

    def _try_open(self):
        if self.dropdown.is_visible():
            return

        self.click_zone.click()
        expect(self.dropdown).to_be_visible()

    def _get_selected_option(self, exact_name):
        return self.choice_widget.locator(
            ".choices__list.choices__list--single,.choices__list.choices__list--multiple"
        ).get_by_role("option", name=exact_name)

    def _check_selection(self, exact_name, check_selection):
        if callable(check_selection):
            return check_selection()
        return expect(self._get_selected_option(exact_name)).to_have_count(1)

    @playwright_repeatable
    def try_select_option(self, exact_name, *, search=None, check_selection=None):
        search = search or exact_name

        if self._get_selected_option(exact_name).count() > 0:
            # Option already selected
            return

        self._try_open()
        self.choice_widget.locator("input.choices__input").fill(search)
        self.dropdown.get_by_role("option", name=exact_name, exact=True).locator("visible=true").click()
        self._check_selection(exact_name, check_selection)


class TreeselectPage:
    @property
    def treeselect(self):
        return self.container.locator(".fr-treeselect").first

    @property
    def main_button(self):
        return self.treeselect.locator(".fr-treeselect__button").first

    @property
    def main_dropdown(self):
        return self.treeselect.locator(".fr-treeselect__collapse").first

    @property
    def options_container(self):
        return self.treeselect.locator(".fr-treeselect__body").first

    @property
    def search_bar(self):
        return self.treeselect.locator(".fr-treeselect__head .fr-search-bar input").first

    @property
    def selected_tags(self):
        return self.container.get_by_test_id("selected-tag")

    def __init__(self, page: Page, container: Locator):
        self.page = page
        self.container = container

    @playwright_repeatable
    def open_treeselect(self):
        if self.options_container.is_visible():
            return
        self.main_button.click()
        expect(self.options_container).to_be_visible()

    @playwright_repeatable
    def close_treeselect(self):
        if not self.options_container.is_visible():
            return
        self.main_button.click()
        expect(self.options_container).not_to_be_visible()

    @contextmanager
    def opened_treeselect(self, *, close_after=True):
        self.open_treeselect()
        yield
        if close_after:
            self.close_treeselect()

    def _locate_group(self, name: str, container: Locator | None = None):
        container = container or self.container
        group_header = container.locator(
            f'.fr-treeselect__group .fr-treeselect__group-header:has(.fr-treeselect__group-button:text-is("{name}"))'
        ).first
        group = group_header.locator("..")
        collapse = group.locator("> .fr-collapse")
        button = group_header.locator(".fr-treeselect__group-button")
        return group, button, collapse

    def open_group(self, name: str, container: Locator | None = None):
        self.open_treeselect()

        group, button, collapse = self._locate_group(name, container)

        @playwright_repeatable
        def do_open():
            if not collapse.is_visible():
                button.click()
                expect(collapse).to_be_visible()

        do_open()

        return group

    def open_groups(self, *names: str) -> Locator:
        group = None
        for name in names:
            group = self.open_group(name, group)
        # If `names` is an empty liste because check box is top-level, just return the main dropdown
        return group or self.main_dropdown

    def close_group(self, name: str, container: Locator | None = None):
        self.open_treeselect()

        group, button, collapse = self._locate_group(name, container)

        @playwright_repeatable
        def do_close():
            if collapse.is_visible():
                button.click()
                expect(collapse).not_to_be_visible()

        do_close()

        return group or self.container

    def check_option(self, *names: str, close_after=True):
        with self.opened_treeselect(close_after=close_after):
            *groups, checkbox_label = names
            group = self.open_groups(*groups)

            @playwright_repeatable
            def tick_checkbox():
                input = group.get_by_label(checkbox_label, exact=True).first
                if not input.is_checked():
                    input.evaluate("it => it.click()")
                expect(input).to_be_checked()

            tick_checkbox()

    def uncheck_option(self, *names: str, close_after=True):
        with self.opened_treeselect(close_after=close_after):
            *groups, checkbox_label = names
            group = self.open_groups(*groups)

            @playwright_repeatable
            def untick_checkbox():
                input = group.get_by_label(checkbox_label, exact=True).first
                if input.is_checked():
                    input.evaluate("it => it.click()")
                expect(input).not_to_be_checked()

            untick_checkbox()

    def uncheck_by_tag(self, text):
        with self.opened_treeselect():
            locator = self.container.get_by_test_id("selected-tag").get_by_text(text, exact=True)
            expect(locator).to_be_visible()
            locator.get_by_role("button").click()
            expect(locator).not_to_be_visible()

    def uncheck_all(self):
        with self.opened_treeselect():
            selected_tags_locator = self.container.get_by_test_id("selected-tag")
            while selected_tags_locator.count():
                before = selected_tags_locator.count()
                selected_tags_locator.first.get_by_role("button").click()
                assert selected_tags_locator.count() == before - 1

    def get_option(self, option: GroupedChoicesMixin, exact=True):
        return self.container.get_by_label(option.uncategorized_label, exact=exact)

    def search(self, term):
        self.search_bar.fill(term)
