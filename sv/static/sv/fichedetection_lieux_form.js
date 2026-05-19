import {setUpAddressChoices} from "BanAutocomplete"
import {setUpSiretChoices} from "siret"

document.lieuxCards = []
const modalHTMLContent = {}
document.choicesInstances = {}

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
    document.querySelectorAll("[id^=commune-select-]").forEach(communeSelect => {
        const modal = communeSelect.closest("dialog")
        setUpAdresseEtablissement(modal)
    })

    document.querySelectorAll(`[id$="-sirene-btn"]`).forEach(siretLookupBtn => {
        siretLookupBtn.addEventListener("click", event => {
            event.preventDefault()
            siretLookupBtn.classList.add("fr-hidden")
            configureSiretField(siretLookupBtn.nextElementSibling.querySelector("select"))
            siretLookupBtn.nextElementSibling.classList.remove("fr-hidden")
        })
    })
})()
