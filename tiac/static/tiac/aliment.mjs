import {applicationReady} from "Application"
import {BaseFormInModal} from "BaseFormInModal"
import {BaseFormSetController} from "BaseFormset"
import {collectFormValues} from "Forms"

/**
 * @typedef AlimentData
 * @property {string} categorie_produit
 * @property {string} denomination
 * @property {string} description_composition
 * @property {string} description_produit
 * @property {string[]} motif_suspicion
 * @property {string} type_aliment
 */

class AlimentFormController extends BaseFormInModal {
    static targets = [
        "denominationInput",
        "typeAlimentInputContainer",
        "descriptionCompositionInput",
        "descriptionCompositionInputContainer",
        "descriptionProduitInput",
        "descriptionProduitInputContainer",
        "categorieProduitRootContainer",
        "jsonConfig",
    ]
    static values = {categorieProduit: Array}

    connect() {
        if (this.shouldImmediatelyShowValue) {
            this.openDialog()
            this.handleConditionalFields(this.typeAlimentInputContainerTarget.querySelector(":checked").value)
        } else {
            this.initCard(
                collectFormValues(this.fieldsetTarget, {
                    nameTransform: name => name.replace(`${this.formPrefixValue}-`, ""),
                    skipValidation: true,
                }),
            )
        }
    }

    initCard(aliment) {
        this.shouldImmediatelyShowValue = false
        this.cardContainerTargets.forEach(it => it.remove())
        this.element.insertAdjacentHTML("beforeend", this.renderCard(aliment))
        this.element.insertAdjacentHTML("beforeend", this.renderDeleteConfirmationDialog(aliment))
        dsfr(this.dialogTarget).modal.conceal()
    }

    handleConditionalFields(value) {
        if (value === "aliment cuisine") {
            this.descriptionCompositionInputContainerTarget.classList.remove("fr-hidden")
            this.descriptionProduitInputContainerTarget.classList.add("fr-hidden")
            this.categorieProduitRootContainerTarget.classList.add("fr-hidden")
            this.descriptionCompositionInputTarget.value = ""
        } else {
            this.descriptionProduitInputContainerTarget.classList.remove("fr-hidden")
            this.categorieProduitRootContainerTarget.classList.remove("fr-hidden")
            this.descriptionCompositionInputContainerTarget.classList.add("fr-hidden")
            this.descriptionCompositionInputTarget.value = ""
        }
    }

    onTypeAlimentChange(event) {
        this.handleConditionalFields(event.target.value)
    }

    getDeleteConfirmationSentence(aliment) {
        return `Confimez-vous vouloir supprimer l'aliment ${aliment.denomination} ?`
    }

    getDeleteConfirmationTitle(_aliment) {
        return "Suppression d'un aliment"
    }

    /**
     * @param {AlimentData} aliment
     * @return {string} HTML
     */
    renderCard(aliment) {
        // language=HTML
        return `<div class="aliment-card fr-card" data-${this.identifier}-target="cardContainer">
            <div class="fr-card__body">
                <div class="fr-card__content">
                    <h3 class="fr-card__title" data-${this.identifier}-target="denomination">
                    <a href="#${aliment.denomination}" id="${aliment.denomination}" data-action="${this.identifier}#onModify:prevent:default" >
                      ${aliment.denomination}
                    </a>
                    </h3>
                    <div class="fr-card__desc">
                        ${this.optionalText(aliment.motif_suspicion, `<p>${this.joinText(", ", ...aliment.motif_suspicion)}</p>`)}
                        ${this.optionalText(aliment.type_aliment, this.renderBadges([aliment.type_aliment]))}
                    </div>
                </div>
                <div class="fr-card__footer">
                    <div class="fr-btns-group fr-btns-group--inline-lg fr-btns-group--icon-left fr-btns-group--sm fr-btns-group--right">
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

applicationReady.then(app => {
    app.register("aliment-formset", BaseFormSetController)
    app.register("aliment-form", AlimentFormController)
})
