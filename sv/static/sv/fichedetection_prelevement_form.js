import {applicationReady, escapeHTML} from "Application"
import {Controller} from "Stimulus"
import {useStore} from "StimulusStore"
import {lieuxStore, prelevementsStore} from "SvLieux"

/**
 * @typedef PrelevementData
 * @type {object}
 * @property {string} id
 * @property {string} type
 * @property {string} structure
 * @property {string} lieu
 * @property {string} officiel
 * @property {string} resultat
 * @property {Date|null} datePrelevement
 * @property {string|null} numeroEchantillon
 * @property {string|null} especeEchantillon
 * @property {string|null} laboratoire
 */

let lieuxCards = []
/** @type {PrelevementData[]} */
document.prelevementCards = []
const modalHTMLContent = {}

/**
 * ******** Targets ********
 * @property {HTMLButtonElement} addButtonTarget
 * @property {HTMLElement[]} prelevementNoticeTargets
 * ******** Stores ********
 * @property  {function(value: import("StimulusStore/dist/types/setCallback").SetCallback)}  setLieuxStoreValue
 * @property  {import("StimulusStore/dist/types/updateMethod").UpdateMethod}  onLieuxStoreUpdate
 * @property {Object} lieuxStoreValue
 *
 * @property  {function(value: import("StimulusStore/dist/types/setCallback").SetCallback)}  setPrelevementsStoreValue
 * @property  {import("StimulusStore/dist/types/updateMethod").UpdateMethod}  onPrelevementsStoreUpdate
 * @property {Object} prelevementsStoreValue
 */
class PrelevementController extends Controller {
    static targets = ["addButton", "prelevementNotice"]
    static stores = [lieuxStore, prelevementsStore]

    connect() {
        useStore(this)
        const prelevementCards = document.prelevementCards
        const controller = this
        Object.defineProperty(document, "prelevementCards", {
            get() {
                return controller.prelevementCardsProxy
            },
            set(value) {
                controller.prelevementCardsProxy = new Proxy(value, {
                    set(target, prop, value) {
                        const result = Reflect.set(target, prop, value)
                        controller.setPrelevementsStoreValue(target)
                        return result
                    },

                    get(target, prop) {
                        return (...args) => {
                            const result = Reflect.get(target, prop).call(target, ...args)
                            controller.setPrelevementsStoreValue(target)
                            return result
                        }
                    },
                })
            },
        })
        document.prelevementCards = prelevementCards
    }

    onLieuxStoreUpdate(lieux) {
        const hasLieux = Object.keys(lieux).length === 0
        this.addButtonTarget.disabled = hasLieux
        this.prelevementNoticeTargets.forEach(it => {
            hasLieux ? it.classList.remove("fr-hidden") : it.classList.add("fr-hidden")
        })

        lieuxCards = Object.values(lieux)
    }
}

/** @param {MouseEvent} evt */
function duplicatePrelevement(evt) {
    evt.preventDefault()
    evt.stopPropagation()
    const elToClone = document.querySelector(`#modal-add-edit-prelevement-${evt.target.dataset.id}`)
    const currentModal = getNextAvailablePrelevementModal()
    ;[
        "numero_rapport_inspection",
        "numero_echantillon",
        "lieu",
        "structure_preleveuse",
        "matrice_prelevee",
        "date_prelevement",
    ].forEach(it => {
        const src = elToClone.querySelector(`[name$="${it}"]`)
        currentModal.querySelector(`[name$="${it}"]`).value = src.value
    })
    // espece_echantillon form element is a bit special; its options are populated via HTTP query
    // so we have not choice but to entirely clone the field here
    currentModal.querySelector("#espece-echantillon").innerHTML =
        elToClone.querySelector("#espece-echantillon").innerHTML
    modalHTMLContent[currentModal.dataset.id] = currentModal.querySelector(".fr-modal__content").innerHTML
    populateLieuSelect(currentModal.querySelector(`[id^="id_prelevements-"][id$="-lieu"]`))
    dataRequiredToRequired(currentModal)
    dsfr(currentModal).modal.disclose()
}

function deletePrelevement(event) {
    const id = event.target.dataset.id
    document.prelevementCards = document.prelevementCards.filter(item => item.id !== id)
    resetForm(document.getElementById(`modal-add-edit-prelevement-${id}`))
    displayPrelevementsCards()
    dsfr(document.getElementById("modal-delete-prelevement-confirmation")).modal.conceal()
}

function displayPrelevementsCards() {
    const prelevementListElement = document.getElementById("prelevements-list")
    const prelevementTemplateElement = document.getElementById("prelevement-carte-tpl")
    prelevementListElement.innerHTML = ""

    document.prelevementCards.forEach(card => {
        const datePrelevementHtml =
            card.datePrelevement !== null
                ? `<p class="fr-card__detail fr-icon-calendar-2-line fr-mb-3v">
                        ${card.datePrelevement.toLocaleDateString("fr")}
                    </p>`
                : ""

        const otherInfos = [
            ["Numéro de l’échantillon", card.numeroEchantillon],
            ["Espèce", card.especeEchantillon],
            ["Laboratoire", card.laboratoire],
        ]
            .map(([label, value]) =>
                value !== null ? `<p class="prelevement-other-info">${label} : ${value}</p>` : "",
            )
            .join("")
            .trim()

        const labels = [card.officiel, card.resultat]
            .map(it => `<p class="fr-badge fr-badge--info fr-badge--no-icon fr-mt-3v fr-mr-2v">${it}</p>`)
            .join("")

        const moreBtns =
            card.type === "premiere_intention"
                ? document.querySelector("#prelevement-duplicate-btn-tpl").innerHTML.replaceAll("__card_id__", card.id)
                : ""

        const html = prelevementTemplateElement.innerHTML
            .replaceAll("__card_id__", escapeHTML(card.id))
            .replaceAll("__nom__", escapeHTML(card.structure))
            .replaceAll("__date_prelevement__", datePrelevementHtml)
            .replaceAll("__lieu__", card.lieu)
            .replaceAll("__other_infos__", otherInfos)
            .replaceAll("__labels__", labels)
            .replaceAll("__more_btns__", moreBtns)

        prelevementListElement.insertAdjacentHTML("beforeend", html)

        const deleteBtns = prelevementListElement.querySelectorAll(
            `#prelevements-list .prelevement-delete-btn[data-id="${card.id}"]`,
        )
        for (const it of deleteBtns) {
            it.addEventListener("click", event => {
                dsfr(document.getElementById("modal-delete-prelevement-confirmation")).modal.disclose()
                document
                    .getElementById("delete-prelevement-confirm-btn")
                    .setAttribute("data-id", event.target.dataset.id)
            })
        }

        const duplicateBtns = prelevementListElement.querySelectorAll(
            `#prelevements-list .prelevement-copy-btn[data-id="${card.id}"]`,
        )
        for (const it of duplicateBtns) {
            it.addEventListener("click", duplicatePrelevement)
        }
    })
}

function populateLieuSelect(element) {
    const currentValue = element.value
    element.innerHTML = ""
    lieuxCards.forEach(option => {
        const opt = document.createElement("option")
        opt.value = option.nom
        opt.textContent = option.nom
        element.appendChild(opt)
    })
    element.value = currentValue ? currentValue : element.options[0].value
}

function getNextAvailablePrelevementModal() {
    const elements = document.querySelectorAll("[id^=modal-add-edit-prelevement-]")
    for (const element of elements) {
        const input = element.querySelector(`[id^="id_prelevements-"][id$="-structure_preleveuse"]`)
        if (input && input.value === "") {
            return element
        }
    }
}

function showAddPrelevementmodal(event) {
    event.preventDefault()
    const currentModal = getNextAvailablePrelevementModal()
    modalHTMLContent[currentModal.dataset.id] = currentModal.querySelector(".fr-modal__content").innerHTML
    populateLieuSelect(currentModal.querySelector(`[id^="id_prelevements-"][id$="-lieu"]`))
    dataRequiredToRequired(currentModal)
    dsfr(currentModal).modal.disclose()
}

function buildPrelevementCardFromModal(element) {
    const typeElement = element.querySelector(`[id^="id_prelevements-"][id*="-type_analyse"]:checked`)
    const structureElement = element.querySelector(`[id^="id_prelevements-"][id$="-structure_preleveuse"]`)
    const lieuElement = element.querySelector(`[id^="id_prelevements-"][id$="-lieu"]`)
    const officielElement = element.querySelector(`[id^="id_prelevements-"][id$="-is_officiel"]`)
    const resultatElement = element.querySelector(`input[name*="-resultat"]:checked`)
    const resultats = JSON.parse(document.getElementById("prelevement-resultats").textContent)
    const datePrelevement = element.querySelector('[name$="date_prelevement"]').valueAsDate
    const numeroEchantillon = element.querySelector('[name$="numero_echantillon"]').value
    let especeEchantillon = element.querySelector('[name$="espece_echantillon"]').selectedOptions[0]
    especeEchantillon =
        especeEchantillon !== undefined && especeEchantillon.value !== "" ? especeEchantillon.label : null
    const laboratoireOption = element.querySelector('[name$="laboratoire"]').selectedOptions[0] || null

    return {
        id: element.dataset.id,
        type: typeElement.value,
        structure: structureElement.options[structureElement.selectedIndex].text,
        lieu: lieuElement.options[lieuElement.selectedIndex].text,
        officiel: officielElement.checked === true ? "Prélèvement officiel" : "Prélèvement non officiel",
        resultat: resultats[resultatElement.value].toUpperCase(),
        datePrelevement,
        numeroEchantillon: numeroEchantillon.length > 0 ? numeroEchantillon : null,
        especeEchantillon,
        laboratoire: laboratoireOption?.value !== "" ? laboratoireOption.label : null,
    }
}

function showModalIfPrelevementEnAttente(resultat) {
    if (resultat === "EN ATTENTE") {
        dsfr(document.getElementById("fr-modal-prelevement-en-attente")).modal.disclose()
    }
}

function savePrelevement(event) {
    const id = event.target.dataset.id
    const modal = document.getElementById(`modal-add-edit-prelevement-${id}`)
    if (formIsValid(modal) === false) {
        return
    }

    const data = buildPrelevementCardFromModal(modal)
    const index = document.prelevementCards.findIndex(element => element.id === data.id)
    if (index === -1) {
        document.prelevementCards.push(data)
    } else {
        document.prelevementCards[index] = data
    }
    displayPrelevementsCards()
    removeRequired(modal)
    dsfr(modal).modal.conceal()
    showModalIfPrelevementEnAttente(data.resultat)
}

function saveModalWhenOpening(event) {
    const modalId = event.target.getAttribute("id").split("-").pop()
    populateLieuSelect(event.target.querySelector(`[id^="id_prelevements-"][id$="-lieu"]`))
    // On ne sauvegarde que si ce n'est pas déjà fait (cas de la modification)
    if (!modalHTMLContent[modalId]) {
        modalHTMLContent[modalId] = event.target.querySelector(".fr-modal__content").innerHTML
    }
}

function setIsOfficiel(event) {
    const modal = event.target.closest("dialog")
    const isOfficielCheckbox = modal.querySelector("[id$=is_officiel]")
    const structureElement = modal.querySelector("[id$=structure_preleveuse]")

    if (structureElement.options[structureElement.selectedIndex].text === "Exploitant") {
        isOfficielCheckbox.checked = false
        isOfficielCheckbox.disabled = true
        return
    }

    if (modal.querySelector("input[name$=type_analyse]:checked").value === "confirmation") {
        isOfficielCheckbox.checked = true
        isOfficielCheckbox.disabled = false
    }
    handleChangeIsOfficiel(event)
}

function handleChangeTypeAnalyse(event) {
    setIsOfficiel(event)
    const laboElement = event.target.closest("dialog").querySelector("[id$=laboratoire]")
    const isConfirmation = event.target.value === "confirmation"

    laboElement.querySelectorAll("option").forEach(option => {
        option.disabled = isConfirmation && option.getAttribute("data-confirmation-officielle") === "false"
    })
}

function handleChangeIsOfficiel(event) {
    const isOfficielCheckbox = event.target.closest("dialog").querySelector("[id$=is_officiel]")
    const numeroRIElement = event.target.closest("dialog").querySelector("[id$=numero_rapport_inspection]")
    if (isOfficielCheckbox.checked === false) {
        numeroRIElement.value = ""
        numeroRIElement.disabled = true
    } else {
        numeroRIElement.disabled = false
    }
}

function handleModalClose(event) {
    const modal = event.target.closest("dialog")
    const modalId = modal.id.split("-").pop()
    const modalContent = modal.querySelector(".fr-modal__content")
    // Réinitialise le contenu
    if (modalContent && modalHTMLContent[modalId]) {
        modalContent.innerHTML = modalHTMLContent[modalId]
    }
    dsfr(modal).modal.conceal()
}

function prelevementsinit() {
    document.getElementById("btn-add-prelevment").addEventListener("click", showAddPrelevementmodal)
    document.getElementById("delete-prelevement-confirm-btn").addEventListener("click", deletePrelevement)
    document
        .querySelectorAll(".prelevement-save-btn")
        .forEach(button => button.addEventListener("click", savePrelevement))
    document
        .querySelectorAll("select[id$=structure_preleveuse]")
        .forEach(element => element.addEventListener("change", setIsOfficiel))
    document
        .querySelectorAll("input[name$=type_analyse]")
        .forEach(element => element.addEventListener("change", handleChangeTypeAnalyse))
    document
        .querySelectorAll("input[name$=is_officiel]")
        .forEach(element => element.addEventListener("change", handleChangeIsOfficiel))
    document
        .querySelectorAll("[id^=modal-add-edit-prelevement-]")
        .forEach(modal => modal.addEventListener("dsfr.disclose", saveModalWhenOpening))
    document
        .querySelectorAll(
            "[id^=modal-add-edit-prelevement-] .fr-btn--close, [id^=modal-add-edit-prelevement-] .prelevement-cancel-btn",
        )
        .forEach(button => button.addEventListener("click", handleModalClose))

    document.querySelectorAll("[id^=modal-add-edit-prelevement-]").forEach(element => {
        if (element.dataset.alreadyExisting) {
            const data = buildPrelevementCardFromModal(element)
            document.prelevementCards.push(data)
        }
    })
    displayPrelevementsCards()
}

applicationReady.then(app => {
    app.register("prelevement-form", PrelevementController)
    prelevementsinit()
})
