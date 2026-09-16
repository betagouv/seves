import {applicationReady, escapeHTML} from "Application"
import {BaseFormInModal} from "BaseFormInModal"
import {BaseFormSetController} from "BaseFormset"
import {collectFormValues} from "Forms"
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
class PrelevementFormSetController extends BaseFormSetController {
    static targets = ["addButton", "prelevementNotice"]
    static stores = [lieuxStore, prelevementsStore]

    connect() {
        useStore(this)
    }

    onLieuxStoreUpdate(lieux) {
        const noLieu = Object.keys(lieux).length === 0
        this.addButtonTarget.disabled = noLieu
        this.prelevementNoticeTargets.forEach(it => it.classList.toggle("fr-hidden", noLieu))
    }
}

/**
 * ******** Targets ********
 * @property {HTMLElement} errorMessageTarget
 * @property {HTMLSelectElement} laboratoireInputTarget
 * ******** values ********
 * @property {Boolean} confirmationOfficielleValue
 * @property {String} typeAnalyseValue
 */
class PrelevementFormController extends BaseFormInModal {
    static targets = ["errorMessage", "laboratoireInput"]
    static values = {confirmationOfficielle: {type: Boolean, default: false}, typeAnalyse: String}
    static stores = [lieuxStore]

    connect() {
        useStore(this)

        if (this.shouldImmediatelyShowValue) {
            this.openDialog()
        } else {
            this.initCard(
                collectFormValues(this.fieldsetTarget, {
                    nameTransform: name => name.replace(`${this.formPrefixValue}-`, ""),
                    skipValidation: true,
                }),
            )
        }
    }

    confirmationOfficielleValueChanged(value) {
        this.mutateLaboOptiions()
    }

    onTypeAnalyseChange({target: {value}}) {
        this.typeAnalyseValue = value
        this.mutateLaboOptiions()
    }

    onLieuxStoreUpdate(lieux) {}

    mutateLaboOptiions() {
        for (const option of this.laboratoireInputTarget.options) {
            option.disabled = this.confirmationOfficielleValue && this.typeAnalyseValue === "confirmation"
        }
    }

    getDeleteConfirmationSentence(_data) {
        return "Souhaitez-vous réellement supprimer le prélèvement ?"
    }

    getDeleteConfirmationTitle(_data) {
        return "Suppression d'un prélèvement"
    }

    initCard(prelevement) {
        this.shouldImmediatelyShowValue = false
        this.cardContainerTargets.forEach(it => it.remove())
        this.element.insertAdjacentHTML("beforeend", this.renderCard(prelevement))
        this.element.insertAdjacentHTML("beforeend", this.renderDeleteConfirmationDialog(prelevement))
        this.setPrelevementsStoreValue(value => ({...value, [this.formPrefixValue]: prelevement}))
        dsfr(this.dialogTarget).modal.conceal()
    }

    onCloseForm() {
        super.onCloseForm()
        this.errorMessageTargets.forEach(it => it.remove())
    }

    onDuplicate() {}

    /**
     * @param {PrelevementData} prelevement
     * @return {string}
     */
    renderCard(prelevement) {
        const hasErrors = !this.isValidValue

        // language=HTML
        return `<section id="${this.formPrefixValue}--card" class="seves-card" data-${this.identifier}-target="cardContainer">
            ${this.optionalText(
                hasErrors,
                `<div id="${this.formPrefixValue}--error-desc" class="fr-alert fr-alert--error fr-mb-2v" aria-live="polite" data-${this.identifier}-target="errorMessage">
                    <p>Ce formulaire contient des erreurs. Veuillez l'éditer pour les corriger</p>
                </div>`,
            )}
            <div class="fr-card"${this.optionalText(hasErrors, ` aria-labelledby="${this.formPrefixValue}--error-desc"`)} data-testid="prelevement-initial">
                <div class="fr-card__body">
                    <div class="fr-card__content">
                        <h3
                            class="fr-card__title"
                            data-${this.identifier}-target="denomination"
                            aria-labelledby="${this.formPrefixValue}--button-open-modal"
                        >
                            <button
                                id="${this.formPrefixValue}--button-open-modal"
                                class="fr-link"
                                type="button"
                                data-action="${this.identifier}#onModify:prevent:default"
                            >
                                ${escapeHTML(prelevement.structure)}
                            </button>
                        </h3>
                        <div class="fr-card__desc fr-mt-4v fr-flex fr-flex--gap-2v">
                            ${this.optionalText(
                                prelevement.datePrelevement,
                                `<p class="fr-card__detail fr-icon-calendar-2-line fr-mb-3v">
                                    ${prelevement.datePrelevement?.toLocaleDateString("fr") ?? ""}
                                </p>`,
                            )}
                            <p class="fr-card__detail fr-icon-map-pin-2-line">${prelevement.lieu}</p>
                            <section class="prelevement-other-infos">
                                ${this.joinText(
                                    "\n",
                                    [
                                        ["Numéro de l’échantillon", prelevement.numeroEchantillon],
                                        ["Espèce", prelevement.especeEchantillon],
                                        ["Laboratoire", prelevement.laboratoire],
                                    ].map(([label, it]) =>
                                        this.optionalText(
                                            it,
                                            `<p class="prelevement-other-info">${label} : ${it ?? ""}</p>`,
                                        ),
                                    ),
                                )}
                            </section>
                            <section class="fr-mt-1v">
                                <p class="fr-badge fr-badge--info fr-badge--no-icon fr-mt-3v fr-mr-2v">${prelevement.officiel}</p>
                                <p class="fr-badge fr-badge--info fr-badge--no-icon fr-mt-3v fr-mr-2v">${prelevement.resultat}</p>
                            </section>
                        </div>
                        <div class="fr-card__end">
                            <div class="fr-btns-group fr-btns-group--sm fr-btns-group--right fr-btns-group--inline-lg fr-btns-group--icon-left fr-mb-n4v">
                                <button
                                    class="fr-btn fr-btn--secondary fr-icon-edit-line modify-button"
                                    type="button"
                                    data-action="${this.identifier}#onModify:prevent:default"
                                    data-testid="lieu-edit-btn"
                                >
                                    Modifier
                                </button>
                                ${
                                    prelevement.type !== "premiere_intention"
                                        ? ""
                                        : `<button
                                            type="button"
                                            class="fr-btn fr-btn--tertiary fr-icon-ri ri-file-copy-line prelevement-copy-btn"
                                            data-action="${this.identifier}#onDuplicate:prevent:default"
                                            data-testid="prelevement-diplicate-btn"
                                        >
                                            Dupliquer
                                        </button>`
                                }
                                <button
                                    class="fr-btn fr-btn--secondary fr-icon-delete-bin-line delete-button"
                                    type="button"
                                    data-action="${this.identifier}#onDelete:prevent:default"
                                    data-testid="lieu-delete-btn"
                                >
                                    Supprimer
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>`
    }
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

function showModalIfPrelevementEnAttente(resultat) {
    if (resultat === "EN ATTENTE") {
        dsfr(document.getElementById("fr-modal-prelevement-en-attente")).modal.disclose()
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

applicationReady.then(app => {
    app.register("prelevement-formset", PrelevementFormSetController)
    app.register("prelevement-form", PrelevementFormController)
})
