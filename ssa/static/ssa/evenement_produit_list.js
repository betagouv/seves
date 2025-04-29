document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('search-form')
    searchForm.addEventListener('reset', function (e) {
        e.preventDefault()
        resetForm(searchForm)
        searchForm.submit()
    });
});
