import {applicationReady} from "Application"
import {BaseFormInModal} from "BaseFormInModal"
import {BaseFormSetController} from "BaseFormset"
import {collectFormValues} from "Forms"

const VOWEL_SOUND = /^[aeiouyàâäéèêëïîôöùûü]/i

/**
 * @property {HTMLSelectElement} laboratoireSelectTarget
 * @property {HTMLSelectElement} methodeSelectTarget
 * @property {Object} methodesParLaboratoireValue
 * @property {Object} laboratoiresTypesValue
 */
class AnalyseFormController extends BaseFormInModal {
    static targets = ["maladieSelect", "laboratoireSelect", "methodeSelect"]
    static values = {
        methodesParLaboratoire: Object,
        laboratoiresTypes: Object,
    }

    connect() {
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

    onLaboratoireChange() {
        this.methodeSelectTarget.value = ""
        this.refreshMethodeOptions({keepSelection: false})
    }

    refreshMethodeOptions({keepSelection}) {
        const laboratoireId = this.laboratoireSelectTarget.value
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
        const laboratoireId = this.laboratoireSelectTarget.value
        return this.laboratoiresTypesValue[laboratoireId]
    }

    /** @param {Object} analyse */
    initCard(analyse) {
        this.shouldImmediatelyShowValue = false
        this.cardContainerTargets.forEach(it => it.remove())
        this.element.insertAdjacentHTML("beforeend", this.renderCard(analyse))
        this.element.insertAdjacentHTML("beforeend", this.renderDeleteConfirmationDialog(analyse))
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
