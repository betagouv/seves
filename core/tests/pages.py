import functools
from functools import cached_property

from playwright.sync_api import Error as PlaywrightError, Locator, Page, expect


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
