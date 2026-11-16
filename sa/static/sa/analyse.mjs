import {applicationReady} from "Application"
import {BaseFormInModal} from "BaseFormInModal"
import {BaseFormSetController} from "BaseFormset"
import {collectFormValues} from "Forms"

const VOWEL_SOUND = /^[aeiouyàâäéèêëïîôöùûü]/i
const RESULTAT_EN_ATTENTE = "en_attente"

/**
 * @property {HTMLSelectElement} laboratoireSelectTarget
 * @property {HTMLSelectElement} methodeSelectTarget
 * @property {HTMLSelectElement} resultatSelectTarget
 * @property {Object} methodesParLaboratoireValue
 * @property {Object} laboratoiresTypesValue
 * @property {Object} laboratoiresFrequentsParMaladieValue
 */
class AnalyseFormController extends BaseFormInModal {
    static targets = ["laboratoireSelect", "methodeSelect", "confirmationInput", "resultatSelect", "dateResultatInput"]
    static values = {
        methodesParLaboratoire: Object,
        laboratoiresTypes: Object,
        laboratoiresFrequentsParMaladie: Object,
    }

    /** @type {HTMLElement[] | undefined} */
    #laboratoireElements

    connect() {
        this.refreshLaboratoireGroups()
        this.updateMethodeRequired()
        this.updateDateResultatState()
        if (this.shouldImmediatelyShowValue) {
            this.openDialog()
        } else {
            this.refreshMethodeOptions({keepSelection: true})
            this.initCard(
                collectFormValues(this.fieldsetTarget, {
                    nameTransform: name => name.replace(`${this.formPrefixValue}-`, ""),
                    skipValidation: true,
                }),
            )
        }
    }

    clean() {
        const maladieTreeselect = this.application.getControllerForElementAndIdentifier(
            this.fieldsetTarget.querySelector('[data-controller~="treeselect"]'),
            "treeselect",
        )
        const event = new Event("submit", {cancelable: true})
        maladieTreeselect.onValidate(event)
        return !event.defaultPrevented
    }

    onMaladieChange() {
        this.refreshLaboratoireGroups()
        // Groups visibility from a previous search no longer matches their new content
        this.application
            .getControllerForElementAndIdentifier(this.getLaboratoireTreeselect(), "treeselect")
            ?.onEraseSearch()
    }

    onLaboratoireChange() {
        this.refreshMethodeOptions({keepSelection: true})
        this.updateMethodeRequired()
    }

    getMaladieId() {
        return this.fieldsetTarget.querySelector(`input[name="${this.formPrefixValue}-maladie"]:checked`)?.value ?? ""
    }

    getLaboratoireTreeselect() {
        return this.fieldsetTarget.querySelector('.fr-treeselect[id$="-laboratoire"]')
    }

    /**
     * Moves the laboratoires associated with the selected maladie into the group "Les plus fréquents", the others
     * into "Autres" (without any associated laboratoire, the full list is displayed without groups).
     */
    refreshLaboratoireGroups() {
        const treeselect = this.getLaboratoireTreeselect()
        const [frequentContainer, otherContainer] = treeselect.querySelectorAll('[data-testid="group-container"]')
        this.#laboratoireElements ??= Array.from(treeselect.querySelectorAll(".fr-treeselect__element"))

        const frequentIds = new Set((this.laboratoiresFrequentsParMaladieValue[this.getMaladieId()] ?? []).map(String))
        const isFrequent = element => frequentIds.has(element.querySelector("input").value)
        const frequent = this.#laboratoireElements.filter(isFrequent)
        frequentContainer.replaceChildren(...frequent)
        otherContainer.replaceChildren(...this.#laboratoireElements.filter(it => !isFrequent(it)))

        for (const header of treeselect.querySelectorAll(".fr-treeselect__group-header")) {
            header.classList.toggle("fr-hidden", frequent.length === 0)
        }
    }

    onResultatChange() {
        this.updateMethodeRequired()
        this.updateDateResultatState()
    }

    updateMethodeRequired() {
        this.methodeSelectTarget.required = this.resultatSelectTarget.value !== RESULTAT_EN_ATTENTE
    }

    updateDateResultatState() {
        const isEnAttente = this.resultatSelectTarget.value === RESULTAT_EN_ATTENTE
        this.dateResultatInputTarget.disabled = isEnAttente
        this.dateResultatInputTarget.required = !isEnAttente
        if (isEnAttente) {
            this.dateResultatInputTarget.value = ""
        }
    }

    getLaboratoireId() {
        return (
            this.fieldsetTarget.querySelector(`input[name="${this.formPrefixValue}-laboratoire"]:checked`)?.value ?? ""
        )
    }

    refreshMethodeOptions({keepSelection}) {
        const laboratoireId = this.getLaboratoireId()
        const previousValue = keepSelection ? this.methodeSelectTarget.value : ""
        const methodes = this.methodesParLaboratoireValue[laboratoireId] || []

        this.methodeSelectTarget.innerHTML = ""
        const placeholder = document.createElement("option")
        placeholder.value = ""
        placeholder.textContent = "Choisir dans la liste"
        this.methodeSelectTarget.appendChild(placeholder)

        for (const methode of methodes) {
            const option = document.createElement("option")
            option.value = methode.value
            option.textContent = methode.label
            this.methodeSelectTarget.appendChild(option)
        }

        this.methodeSelectTarget.disabled = !laboratoireId
        if (previousValue) {
            this.methodeSelectTarget.value = previousValue
        }
    }

    getLaboratoireType() {
        return this.laboratoiresTypesValue[this.getLaboratoireId()]
    }

    /** @param {Object} analyse */
    initCard(analyse) {
        this.shouldImmediatelyShowValue = false
        this.cardContainerTargets.forEach(it => it.remove())
        this.element.insertAdjacentHTML("beforeend", this.renderCard(analyse))
        this.element.insertAdjacentHTML("beforeend", this.renderDeleteConfirmationDialog(analyse))
        if (this.confirmationInputTarget.checked === true) {
            this.element.dispatchEvent(
                new CustomEvent("resultConfirmed", {
                    detail: {
                        date: this.dateResultatInputTarget.value,
                    },
                    bubbles: true,
                }),
            )
        }
        dsfr(this.dialogTarget).modal.conceal()
    }

    forceDelete() {
        super.forceDelete()
        this.dispatch("deleted")
    }

    getDeleteConfirmationTitle() {
        return "Suppression d'une analyse"
    }

    /** @param {Object} analyse */
    getDeleteConfirmationSentence(analyse) {
        const maladie = analyse.maladie || ""
        const article = VOWEL_SOUND.test(maladie) ? "d’" : "de "
        return `Confirmez-vous vouloir supprimer l'analyse ${article}${maladie} ?`
    }

    /** @param {Object} analyse */
    renderCard(analyse) {
        const laboratoireType = this.getLaboratoireType()
        const badges = [analyse.resultat]
        if (laboratoireType && laboratoireType.type !== "autre") {
            badges.push(laboratoireType.label)
        }

        // language=HTML
        return `
            <div class="analyse-card fr-card" data-${this.identifier}-target="cardContainer">
                <div class="fr-card__body">
                    <div class="fr-card__content">
                        <h3 class="fr-card__title">
                            <a href="#${this.formPrefixValue}" data-action="${this.identifier}#onModify:prevent:default">
                                ${analyse.maladie}
                            </a>
                        </h3>
                        <p class="fr-text--sm card-subtitle">Laboratoire : ${analyse.laboratoire}</p>
                        <div class="fr-card__desc">
                            <p class="fr-mb-4v">${analyse.resultat}</p>
                            ${this.renderBadges(badges)}
                        </div>
                    </div>
                    <div class="fr-card__footer">
                        <div class="fr-btns-group fr-btns-group--inline fr-btns-group--sm fr-btns-group--right fr-btns-group--icon-left">
                            <button
                                class="fr-btn fr-btn--secondary fr-icon-edit-line fr-mb-0 modify-button"
                                type="button"
                                data-action="${this.identifier}#onModify:prevent:default"
                            >Modifier</button>
                            <button
                                class="fr-btn fr-btn--secondary fr-icon-delete-bin-line fr-mb-0 delete-button"
                                type="button"
                                data-action="${this.identifier}#onDelete:prevent:default"
                            >Supprimer</button>
                        </div>
                    </div>
                </div>
            </div>`
    }
}

class AnalyseFormSetController extends BaseFormSetController {
    static targets = [...BaseFormSetController.targets, "addButton"]
    static values = {...BaseFormSetController.values, maxAnalyses: Number}

    connect() {
        super.connect()
        this.refreshAddButton()
    }

    onAddForm() {
        const card = super.onAddForm()
        this.refreshAddButton()
        return card
    }

    refreshAddButton() {
        if (!this.hasAddButtonTarget) return
        const deleteInputs = this.formsetContainerTarget.querySelectorAll('[data-analyse-form-target="deleteInput"]')
        const activeCount = Array.from(deleteInputs).filter(input => input.value !== "on").length
        this.addButtonTarget.disabled = activeCount >= this.maxAnalysesValue
    }
}

applicationReady.then(app => {
    app.register("analyse-formset", AnalyseFormSetController)
    app.register("analyse-form", AnalyseFormController)
})
