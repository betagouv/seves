import {addLevel2CategoryIfAllChildrenAreSelected, patchItems, tsDefaultOptions} from "CustomTreeSelect"

document.addEventListener("DOMContentLoaded", () => {
    function clearSidebarFilters(event) {
        event.preventDefault()
        resetForm(document.getElementById("sidebar"))
    }

    function addSidebarFilters(event) {
        event.preventDefault()
        event.target.closest(".sidebar").classList.toggle("open")
        document.querySelector(".main-container").classList.toggle("open")
    }

    function disableCheckboxIfNeeded() {
        document.querySelector("#id_with_free_links").disabled = !document.querySelector("#id_numero").value
    }

    function updateFilterCounter() {
        let filledFields = [...document.getElementById("sidebar").querySelectorAll("input, select")]
        filledFields = filledFields.filter(el => el.value.trim() !== "")

        if (filledFields.length === 0) {
            document.getElementById("more-filters-btn-counter").classList.add("fr-hidden")
        } else {
            document.getElementById("more-filters-btn-counter").innerText = filledFields.length
            document.getElementById("more-filters-btn-counter").classList.remove("fr-hidden")
        }
    }

    document.querySelector(".clear-btn").addEventListener("click", clearSidebarFilters)
    document.querySelector(".add-btn").addEventListener("click", addSidebarFilters)
    document.querySelector("#id_numero").addEventListener("input", disableCheckboxIfNeeded)
    disableCheckboxIfNeeded()
    updateFilterCounter()

    const sidebarClosingObserver = new MutationObserver(mutations => {
        mutations.forEach(mutation => {
            if (mutation.type !== "attributes" && mutation.attributeName !== "class") return
            if (!mutation.target.classList.contains("open")) {
                updateFilterCounter()
            }
        })
    })
    sidebarClosingObserver.observe(document.getElementById("sidebar"), {attributes: true})

    const searchForm = document.getElementById("search-form")
    searchForm.addEventListener("reset", event => {
        event.preventDefault()
        resetForm(searchForm)
        searchForm.submit()
    })
})
