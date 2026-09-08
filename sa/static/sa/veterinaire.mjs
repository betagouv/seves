import {applicationReady} from "Application"
import {BaseFormInModal} from "BaseFormInModal"
import {BaseFormSetController} from "BaseFormset"
import {collectFormValues} from "Forms"

class VeterinaireFormController extends BaseFormInModal {
    connect() {
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

    forceDelete() {
        super.forceDelete()
        this.dispatch("deleted")
    }

    getDeleteConfirmationTitle() {
        return "Suppression d'une structure vétérinaire"
    }

    /** @param {Object} veterinaire */
    getDeleteConfirmationSentence(veterinaire) {
        return `Confirmez-vous vouloir supprimer la structure ${veterinaire.nom_structure} ?`
    }

    /** @param {Object} veterinaire */
    initCard(veterinaire) {
        this.shouldImmediatelyShowValue = false
        this.cardContainerTargets.forEach(it => it.remove())
        this.element.insertAdjacentHTML("beforeend", this.renderCard(veterinaire))
        this.element.insertAdjacentHTML("beforeend", this.renderDeleteConfirmationDialog(veterinaire))
        dsfr(this.dialogTarget).modal.conceal()
    }

    /** @param {Object} veterinaire */
    renderCard(veterinaire) {
        const title =
            veterinaire.prenom || veterinaire.nom
                ? `${veterinaire.prenom} ${veterinaire.nom}`
                : veterinaire.nom_structure
        const badges = [(veterinaire.type_veterinaire || "").toUpperCase(), ...(veterinaire.especes || [])]

        // language=HTML
        return `
            <div class="veterinaire-card fr-card" data-${this.identifier}-target="cardContainer">
                <div class="fr-card__body">
                    <div class="fr-card__content">
                        <h3 class="fr-card__title">
                            <a href="#${this.formPrefixValue}" data-action="${this.identifier}#onModify:prevent:default">
                                ${title}
                            </a>
                        </h3>
                        <p class="fr-text--sm card-subtitle">${veterinaire.nom_structure}</p>
                        <div class="fr-card__desc">
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

class VeterinaireFormSetController extends BaseFormSetController {
    static targets = [...BaseFormSetController.targets, "addButton"]
    static values = {...BaseFormSetController.values, maxVeterinaires: Number}

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
        const deleteInputs = this.formsetContainerTarget.querySelectorAll(
            '[data-veterinaire-form-target="deleteInput"]',
        )
        const activeCount = Array.from(deleteInputs).filter(input => input.value !== "on").length
        this.addButtonTarget.disabled = activeCount >= this.maxVeterinairesValue
    }
}

applicationReady.then(app => {
    app.register("veterinaire-formset", VeterinaireFormSetController)
    app.register("veterinaire-form", VeterinaireFormController)
})
