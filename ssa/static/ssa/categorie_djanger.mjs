import { findPath, isLevel2WithChildren, patchItems, tsDefaultOptions } from "CustomTreeSelect"

function handleValueChangeCategorieDanger(value, options) {
    const fullPath = findPath(value, options)
        .map((n) => n.name)
        .join(" > ")

    document.getElementById("id_categorie_danger").value = value
    document.querySelector("#categorie-danger .treeselect-input__tags-count").innerText = fullPath
    if (document.getElementById("pam-container")) {
        if (fullPath.includes("Bactérie >") && document.getElementById("pam-container")) {
            document.getElementById("pam-container").classList.remove("fr-hidden")
        } else {
            document.getElementById("pam-container").classList.add("fr-hidden")
        }
    }
}

function handleNoticeDangerDisplay(options, value) {
    if (isLevel2WithChildren(options, value)) {
        document.querySelector("#notice-container-risque").classList.remove("fr-hidden")
    } else {
        document.querySelector("#notice-container-risque").classList.add("fr-hidden")
    }
}

function setupCategorieDanger() {
    const options = JSON.parse(document.getElementById("categorie-danger-data").textContent)
    const selectedValue = document.getElementById("id_categorie_danger").value
    const treeselect = new Treeselect({
        parentHtmlContainer: document.getElementById("categorie-danger"),
        value: selectedValue,
        options: options,
        isSingleSelect: true,
        openCallback() {
            patchItems(treeselect.srcElement)
            if (this._customHeaderAdded) {
                treeselect.srcElement.querySelectorAll(".categorie-danger-header").forEach((el) => {
                    el.removeAttribute("hidden")
                    el.removeAttribute("aria-hidden")
                })
                return
            }
            const list = document.querySelector("#categorie-danger .treeselect-list")
            if (list) {
                const clone = document.getElementById("categorie-danger-header").cloneNode(true)
                clone.id = ""
                clone.classList.remove("fr-hidden")
                clone.classList.add("categorie-danger-header")
                list.prepend(clone)
                this._customHeaderAdded = true

                document.querySelector("#categorie-danger .treeselect-list").addEventListener("click", (event) => {
                    if (
                        event.target.firstElementChild &&
                        event.target.firstElementChild.classList.contains("shortcut")
                    ) {
                        const value = event.target.firstElementChild.textContent.trim()
                        treeselect.updateValue(value)
                        treeselect.toggleOpenClose()
                        handleValueChangeCategorieDanger(value, options)
                    }
                })
            }
        },
        searchCallback(item) {
            if (item.length === 0) {
                treeselect.srcElement.querySelectorAll(".categorie-danger-header").forEach((el) => {
                    el.removeAttribute("hidden")
                    el.removeAttribute("aria-hidden")
                })
            } else {
                treeselect.srcElement.querySelectorAll(".categorie-danger-header").forEach((el) => {
                    el.setAttribute("hidden", "hidden")
                    el.setAttribute("aria-hidden", "true")
                })
            }
        },
        ...tsDefaultOptions,
    })
    document.querySelector("#categorie-danger .treeselect-input").classList.add("fr-input")
    treeselect.srcElement.addEventListener("update-dom", () => {
        patchItems(treeselect.srcElement)
    })
    treeselect.srcElement.addEventListener("input", (e) => {
        if (!!e.detail) {
            handleValueChangeCategorieDanger(e.detail, options)
        } else {
            if (document.getElementById("pam-container")) {
                document.getElementById("pam-container").classList.add("fr-hidden")
            }
        }
    })

    treeselect.srcElement.addEventListener("input", (e) => {
        handleNoticeDangerDisplay(options, e.detail)
    })
    handleNoticeDangerDisplay(options, selectedValue)
}

setupCategorieDanger()
