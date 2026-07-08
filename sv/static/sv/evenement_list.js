import {resetForm} from "Forms"

document.addEventListener("DOMContentLoaded", () => {
    const searchForm = document.getElementById("search-form")
    searchForm.addEventListener("reset", e => {
        e.preventDefault()
        resetForm(searchForm)
        searchForm.submit()
    })
})
