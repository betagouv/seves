import {patchItems, addLevel2CategoryIfAllChildrenAreSelected} from "/static/ssa/_custom_tree_select.js"

document.addEventListener('DOMContentLoaded', function() {
    function resetAndSubmit(event){
        const searchForm = document.getElementById('search-form')
        event.preventDefault()
        resetForm(searchForm)
        searchForm.submit()
    }

    function clearSidebarFilters(event) {
        event.preventDefault()
        resetForm(document.getElementById("sidebar"))
    }

    function addSidebarFilters(event) {
        event.preventDefault()
        event.target.closest(".sidebar").classList.toggle('open');
        document.querySelector('.main-container').classList.toggle('open')
    }
    function setupCategorieProduit(){
        const options = JSON.parse(document.getElementById("categorie-produit-data").textContent)
        const parentContainer = document.getElementById("categorie-produit")
        const selectedValues = parentContainer.dataset.selected.split("||").map(v => v.trim())
        const treeselect = new Treeselect({
            parentHtmlContainer: parentContainer,
            value: selectedValues,
            options: options,
            showTags: false,
            placeholder: "Choisir",
            emptyText: "Pas de résultat",
            clearable: false,
            openCallback() {
                patchItems(treeselect.srcElement)
            },
        })
        document.querySelector("#categorie-produit .treeselect-input").classList.add("fr-input")
        patchItems(treeselect.srcElement)
        treeselect.srcElement.addEventListener("update-dom", ()=>{patchItems(treeselect.srcElement)})

        treeselect.srcElement.addEventListener('input', (e) => {
            const values = addLevel2CategoryIfAllChildrenAreSelected(options, e.detail)
            document.getElementById("id_categorie_produit").value = values.join("||")
        })
    }

    function setupCategorieDanger(){
        const options = JSON.parse(document.getElementById("categorie-danger-data").textContent)
        const parentContainer = document.getElementById("categorie-danger")
        const selectedValues = parentContainer.dataset.selected.split("||").map(v => v.trim())
        const treeselect = new Treeselect({
            parentHtmlContainer: parentContainer,
            value: selectedValues,
            options: options,
            showTags: false,
            placeholder: "Choisir",
            emptyText: "Pas de résultat",
            clearable: false,
            openCallback() {
                patchItems(treeselect.srcElement)
            },
        })
        document.querySelector("#categorie-danger .treeselect-input").classList.add("fr-input")
        patchItems(treeselect.srcElement)
        treeselect.srcElement.addEventListener("update-dom", ()=>{patchItems(treeselect.srcElement)})

        treeselect.srcElement.addEventListener('input', (e) => {
            const values = addLevel2CategoryIfAllChildrenAreSelected(options, e.detail)
            document.getElementById("id_categorie_danger").value = values.join("||")
        })
    }

    function disableCheckboxIfNeeded(){
        document.querySelector("#id_with_free_links").disabled = !document.querySelector("#id_numero").value
    }

    document.getElementById('search-form').addEventListener('reset', resetAndSubmit)
    document.querySelector(".clear-btn").addEventListener("click", clearSidebarFilters)
    document.querySelector(".add-btn").addEventListener("click", addSidebarFilters)
    document.querySelector("#id_numero").addEventListener("input", disableCheckboxIfNeeded)
    disableCheckboxIfNeeded()
    setupCategorieProduit()
    setupCategorieDanger()

    const sidebarClosingObserver = new MutationObserver((mutations) => {
        mutations.forEach(mutation => {
            if (mutation.type !== "attributes" && mutation.attributeName !== "class") return;
            if (!mutation.target.classList.contains("open")){
                let filledFields = [...document.getElementById("sidebar").querySelectorAll('input, select')]
                filledFields = filledFields.filter(el => el.value.trim() !== '');

                if (filledFields.length === 0){
                    document.getElementById("more-filters-btn-counter").classList.add("fr-hidden")
                } else {
                    document.getElementById("more-filters-btn-counter").innerText = filledFields.length
                    document.getElementById("more-filters-btn-counter").classList.remove("fr-hidden")
                }
            }
        });
    });
    sidebarClosingObserver.observe(document.getElementById("sidebar"), {attributes: true})
});
