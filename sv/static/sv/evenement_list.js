import choicesDefaults from "choicesDefaults"
import {resetForm} from "Forms"

document.addEventListener("DOMContentLoaded", () => {
    const choicesOrganismeNuisible = new Choices(document.getElementById("id_organisme_nuisible"), choicesDefaults)
    const searchForm = document.getElementById("search-form")
    searchForm.addEventListener("reset", e => {
        e.preventDefault()
        resetForm(searchForm)
        choicesOrganismeNuisible.setChoiceByValue("")
        searchForm.submit()
    })
})
