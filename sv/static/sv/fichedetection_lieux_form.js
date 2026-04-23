import {escapeHTML} from "Application"
import {setUpAddressChoices} from "BanAutocomplete"
import {setUpSiretChoices} from "siret"
import {setUpCommuneChoices} from "/static/core/commune.js"

document.lieuxCards = []
const modalHTMLContent = {}
document.choicesInstances = {}

function deleteLieu(event) {
    const id = event.target.dataset.id
    document.lieuxCards = document.lieuxCards.filter(item => item.id !== id)
    const modal = document.getElementById(`modal-add-lieu-${id}`)
    resetForm(modal)
    if (modal.querySelector("[id$=DELETE]")) {
        modal.querySelector("[id$=DELETE]").checked = true
    }
    displayLieuxCards()
    dsfr(document.getElementById("modal-delete-lieu-confirmation")).modal.conceal()
}

function displayLieuxCards() {
    const lieuListElement = document.getElementById("lieux-list")
    const lieuTpl = document.getElementById("lieu-carte-tpl").innerHTML
    lieuListElement.innerHTML = ""
    if (document.lieuxCards.length === 0) {
        lieuListElement.innerText = "Aucun lieu."
    }

    document.lieuxCards.forEach(card => {
        let departement = (card.departement || null) ?? ""
        let lieuCommune = card.commune
        if (card.codePostal || null) {
            lieuCommune += ` (${card.codePostal})`
            departement = departement.replaceAll(/^\s*\w+\s*-\s*/g, "")
        }
        if (departement.length > 0) {
            lieuCommune += ` | ${departement}`
        }

        const lieuMarkup =
            lieuCommune.trim() !== ""
                ? `<p class="fr-card__detail fr-icon-map-pin-2-line">${escapeHTML(lieuCommune)}</p>`
                : ""

        const labels = [card.siteInspection.trim(), card.supplyChainPosition.trim()]
            .map(it =>
                it !== "" ? `<p class="fr-badge fr-badge--info fr-badge--no-icon fr-mt-4v fr-mr-4v">${it}</p>` : "",
            )
            .join("")

        const newCard = lieuTpl
            .replaceAll("__nom__", escapeHTML(card.nom))
            .replaceAll("__lieu__", lieuMarkup)
            .replaceAll("__labels__", labels)
            .replaceAll("__card_id__", card.id)

        lieuListElement.insertAdjacentHTML("beforeend", newCard)

        for (const it of lieuListElement.querySelectorAll(".lieu-delete-btn")) {
            it.addEventListener("click", event => {
                const lieuLinkedToPrelevement = document.prelevementCards.some(
                    prelevement => prelevement.lieu === card.nom,
                )
                if (lieuLinkedToPrelevement === true) {
                    dsfr(document.getElementById("fr-modal-suppression-lieu")).modal.disclose()
                } else {
                    document.getElementById("delete-lieu-confirm-btn").setAttribute("data-id", event.target.dataset.id)
                    dsfr(document.getElementById("modal-delete-lieu-confirmation")).modal.disclose()
                }
            })
        }
    })
    showOrHidePrelevementUI()
}

function showLieuModal(event) {
    event.preventDefault()
    const currentModal = getNextAvailableModal()
    currentModal.querySelector(".map-container").setAttribute("data-controller", "map")
    handleHasNotImplemented(currentModal)
    modalHTMLContent[currentModal.dataset.id] = currentModal.querySelector(".fr-modal__content").innerHTML
    dsfr(currentModal).modal.disclose()
    dataRequiredToRequired(currentModal)
}

function handleEvent(evt) {
    const target = evt instanceof Event ? evt.target : evt
    if (target.checked) {
        target.closest(".fr-modal__content").classList.add("is-etablissement")
    } else {
        target.closest(".fr-modal__content").classList.remove("is-etablissement")
    }
}

function handleHasNotImplemented(modal) {
    try {
        document.querySelector(":has(body)")
    } catch {
        const checkBox = modal.querySelector("[name*='is_etablissement']")
        checkBox.removeEventListener("change", handleEvent)
        checkBox.addEventListener("change", handleEvent)
        handleEvent(checkBox)
    }
}

function buildLieuCardFromModal(element) {
    /** @type {HTMLSelectElement} */
    const dptSelect = element.querySelector("[id$=departement]")
    const supplyChainPositionEl = element.querySelector('[id$="position_chaine_distribution_etablissement"]')
    const supplyChainPosition =
        (supplyChainPositionEl?.selectedIndex ?? -1 > 0) ? supplyChainPositionEl.selectedOptions[0].label : ""
    const siteInspectionEl = element.querySelector('[id$="site_inspection"]')
    const siteInspection = siteInspectionEl.selectedOptions[0].getAttribute("data-grouped-label")

    return {
        id: element.dataset.id,
        nom: element.querySelector(`[id^="id_lieux-"][id$="-nom"]`).value,
        commune: element.querySelector(`[id^="id_lieux-"][id$="-commune"]`).value,
        departement:
            dptSelect.selectedOptions.length > 0 && dptSelect.selectedOptions[0].value !== ""
                ? dptSelect.selectedOptions[0].textContent
                : "",
        codePostal: element.querySelector(`[id^="id_lieux-"][id$="-code_postal"]`)?.value ?? "",
        supplyChainPosition,
        siteInspection,
    }
}

function saveLieu(event) {
    const id = event.target.dataset.id
    const modal = document.getElementById(`modal-add-lieu-${id}`)
    if (formIsValid(modal) === false) {
        return
    }

    const index = document.lieuxCards.findIndex(element => element.id === id)
    if (index === -1) {
        document.lieuxCards.push(buildLieuCardFromModal(modal))
    } else {
        document.lieuxCards[index] = buildLieuCardFromModal(modal)
    }

    displayLieuxCards()
    removeRequired(modal)
    dsfr(modal).modal.conceal()
    modal.querySelector(".fr-modal__title").textContent = "Modifier le lieu"
}

function setupPreselection(choicesCommunes, communeInput, departementInput, inseeInput, codePostalInput) {
    if (communeInput.value) {
        choicesCommunes.setChoiceByValue(communeInput.value)
        choicesCommunes.setChoices(
            [
                {
                    value: communeInput.value,
                    label: `${communeInput.value} (${departementInput.value})`,
                    selected: true,
                    customProperties: {
                        departementCode: departementInput.value,
                        inseeCode: inseeInput.value,
                        postCode: codePostalInput.value,
                    },
                },
            ],
            "value",
            "label",
            true,
        )
    }
}

function setUpCommune(element) {
    const choicesCommunes = setUpCommuneChoices(element)

    const currentModal = element.closest("dialog")
    const communeInput = currentModal.querySelector("[id$=commune]")
    const inseeInput = currentModal.querySelector("[id$=code_insee]")
    const codePostalInput = currentModal.querySelector("[id$=code_postal]")

    /** @type {HTMLSelectElement} */
    const departementInput = currentModal.querySelector("[id$=departement]")

    setupPreselection(choicesCommunes, communeInput, departementInput, inseeInput, codePostalInput)

    choicesCommunes.passedElement.element.addEventListener("choice", event => {
        communeInput.value = event.detail.value
        inseeInput.value = event.detail.customProperties.inseeCode
        codePostalInput.value = event.detail.customProperties.postCode
        for (const it of departementInput.options) {
            if (it.value === event.detail.customProperties.departementCode) {
                it.selected = true
                break
            }
        }
    })

    choicesCommunes.passedElement.element.addEventListener("removeItem", () => {
        communeInput.value = ""
        inseeInput.value = ""
        codePostalInput.value = ""
        departementInput.value = ""
    })
    choicesCommunes.passedElement.element.addEventListener("forcedChoice", event => {
        choicesCommunes.setValue([event.detail.value])
    })

    return choicesCommunes
}

function onAdresseLieuChoice(event, modal, communeChoice) {
    communeChoice.setValue([event.detail.customProperties.city])
    modal.querySelector("[id$=commune]").value = event.detail.customProperties.city
    modal.querySelector("[id$=code_insee]").value = event.detail.customProperties.inseeCode
    modal.querySelector("[id$=code_postal]").value = event.detail.customProperties.postCode
    modal.querySelector("[id$=wgs84_latitude]").value = event.detail.customProperties.lat
    modal.querySelector("[id$=wgs84_longitude]").value = event.detail.customProperties.long
    modal.querySelector("[id$=wgs84_latitude]").dispatchEvent(new Event("input"))
    modal.querySelector("[id$=wgs84_longitude]").dispatchEvent(new Event("input"))
    if (event.detail.customProperties.context) {
        modal.querySelector("[id$=departement]").value = event.detail.customProperties.context.split(",")[0].trim()
    }
}

function setUpAdresseLieu(modal, communeChoice) {
    const adresseLieuElement = modal.querySelector("[id$=adresse_lieu_dit]")
    const choicesAdresseLieu = setUpAddressChoices(adresseLieuElement)
    choicesAdresseLieu.passedElement.element.addEventListener("choice", event =>
        onAdresseLieuChoice(event, modal, communeChoice),
    )
}

function onAdresseEtablissementChoice(event, modal) {
    modal.querySelector("[id$=commune_etablissement]").value = event.detail.customProperties.city
    modal.querySelector("[id$=code_insee_etablissement]").value = event.detail.customProperties.inseeCode
    if (event.detail.customProperties.context) {
        modal.querySelector("[id$=pays_etablissement]").value = "FR"
        modal.querySelector("[id$=departement_etablissement]").value = event.detail.customProperties.context
            .split(",")[0]
            .trim()
    }
}

function setUpAdresseEtablissement(modal) {
    const adresseEtablissementElement = modal.querySelector("[id$=adresse_etablissement]")
    const choicesAdresseEtablissement = setUpAddressChoices(adresseEtablissementElement)
    choicesAdresseEtablissement.passedElement.element.addEventListener("choice", event =>
        onAdresseEtablissementChoice(event, modal),
    )
    const modalId = modal.getAttribute("id").split("-").pop()
    document.choicesInstances[modalId] = {
        ...(document.choicesInstances[modalId] || {}),
        adresseEtablissement: choicesAdresseEtablissement,
    }
}

function saveModalWhenOpening(event) {
    const modalId = event.target.getAttribute("id").split("-").pop()
    modalHTMLContent[modalId] = event.target.querySelector(".fr-modal__content").innerHTML
}

function resetModalWhenClosing(event) {
    const originalTarget = event.explicitOriginalTarget
    if (!originalTarget.classList.contains("lieu-save-btn")) {
        const modalId = event.originalTarget.getAttribute("id").split("-").pop()
        event.originalTarget.querySelector(".fr-modal__content").innerHTML = modalHTMLContent[modalId]
    }
}
function getNextAvailableModal() {
    const elements = document.querySelectorAll("[id^=modal-add-lieu-]")
    for (const element of elements) {
        const input = element.querySelector(`[id^="id_lieux-"][id$="-nom"]`)
        if (input && input.value === "") {
            return element
        }
    }
}

function setupCharacterCounter(element) {
    const input = element.querySelector(`[id^="id_lieux-"][id$="-activite_etablissement"]`)
    const counterDiv = element.querySelector(".character-counter")
    const maxLength = input.getAttribute("maxlength")

    counterDiv.textContent = `${maxLength - input.value.length} caractères restants`

    input.addEventListener("input", e => {
        const remaining = maxLength - e.target.value.length
        counterDiv.textContent = `${remaining} caractères restants`
    })
}

function configureSiretField(field) {
    const modal = field.closest("dialog")
    const modalId = modal.getAttribute("id").split("-").pop()
    const choicesSIRET = setUpSiretChoices(field, "top")
    choicesSIRET.passedElement.element.addEventListener("choice", event => {
        modal.querySelector("[id$=siret_etablissement]").value = event.detail.customProperties.siret
        modal.querySelector("[id$=raison_sociale_etablissement]").value = event.detail.customProperties.raison
        modal.querySelector("[id$=adresse_lieu_dit]").value = event.detail.customProperties.streetData
        modal.querySelector("[id$=pays_etablissement]").value = "FR"
        if (document.choicesInstances[modalId]?.adresseEtablissement) {
            document.choicesInstances[modalId].adresseEtablissement.setValue([event.detail.customProperties.streetData])
        }
        modal.querySelector("[id$=commune_etablissement]").value = event.detail.customProperties.commune
        modal.querySelector("[id$=departement_etablissement]").value =
            event.detail.customProperties.code_commune.substring(0, 2)
        modal.querySelector("[id$=code_insee_etablissement]").value = event.detail.customProperties.code_commune

        modal.querySelector("[id$=sirene-btn]").classList.remove("fr-hidden")
        modal.querySelector(".fr-search-bar").classList.add("fr-hidden")
        modal.querySelector(".fr-search-bar select").innerHTML = ""
        choicesSIRET.destroy()
    })
}

;(() => {
    document.documentElement.addEventListener("dsfr.start", () => {
        setTimeout(() => {
            document.querySelectorAll("[id^=modal-add-lieu-]").forEach(modal => {
                dsfr(modal).modal.node.addEventListener("dsfr.conceal", resetModalWhenClosing)
            })
        }, 500)
    })

    document.querySelector("#add-lieu-bouton").addEventListener("click", showLieuModal)
    document.querySelectorAll(".lieu-save-btn").forEach(button => button.addEventListener("click", saveLieu))
    document.querySelectorAll("[id^=commune-select-]").forEach(communeSelect => {
        const modal = communeSelect.closest("dialog")
        const communeChoice = setUpCommune(communeSelect)
        setUpAdresseLieu(modal, communeChoice)
        setUpAdresseEtablissement(modal)
    })
    document.getElementById("delete-lieu-confirm-btn").addEventListener("click", deleteLieu)
    document
        .querySelectorAll("[id^=modal-add-lieu-]")
        .forEach(modal => modal.addEventListener("dsfr.disclose", saveModalWhenOpening))
    document
        .querySelectorAll("[id^=modal-add-lieu-] .fr-btn--close")
        .forEach(element => element.addEventListener("click", closeDSFRModal))
    document
        .querySelectorAll("[id^=modal-add-lieu-] .lieu-cancel-btn")
        .forEach(element => element.addEventListener("click", closeDSFRModal))

    document.querySelectorAll("[id^=modal-add-lieu-]").forEach(element => {
        setupCharacterCounter(element)
        const data = buildLieuCardFromModal(element)
        if (data.nom) {
            document.lieuxCards.push(data)
        }
    })

    document.querySelectorAll(`[id$="-sirene-btn"]`).forEach(siretLookupBtn => {
        siretLookupBtn.addEventListener("click", event => {
            event.preventDefault()
            siretLookupBtn.classList.add("fr-hidden")
            configureSiretField(siretLookupBtn.nextElementSibling.querySelector("select"))
            siretLookupBtn.nextElementSibling.classList.remove("fr-hidden")
        })
    })
    displayLieuxCards()
})()
