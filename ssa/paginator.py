from django.core.paginator import Paginator


class TotalCountPaginator(Paginator):
    def __init__(
        self,
        object_list,
        per_page,
        total_count=None,
        orphans=0,
        allow_empty_first_page=True,
        error_messages=None,
    ):
        super().__init__(object_list, per_page, orphans=orphans, allow_empty_first_page=allow_empty_first_page)
        self._total_count = total_count

    @property
    def count(self):
        if self._total_count is not None:
            return self._total_count
        return super().count()

    @property
    def num_pages(self):
        if self.count == 0 and not self.allow_empty_first_page:
            return 0
        hits = max(1, self.count - self.orphans)
        return -(-hits // self.per_page)  # ceil division
