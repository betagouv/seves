import {BaseFormSetController} from "BaseFormset"
import {BaseFormInModal} from "BaseFormInModal"
import {applicationReady} from "Application"
import {patchItems, findPath, tsDefaultOptions} from "CustomTreeSelect"
import {collectFormValues} from 'Forms'

class AlimentFormController extends BaseFormInModal {
    static targets = [
        "denominationInput",
        "typeAlimentInputContainer",
        "categorieProduitInput",
        "categorieProduitContainer",
        "descriptionCompositionInput",
        "descriptionCompositionInputContainer",
        "descriptionProduitInput",
        "descriptionProduitInputContainer",
        "categorieProduitRootContainer",
        "jsonConfig",
    ]
    static values = {categorieProduit: Array}

    connect() {
        this.setupCategorieProduit()
        if (this.shouldImmediatelyShowValue) {
            this.openDialog()
            this.handleConditionalFields(this.typeAlimentInputContainerTarget.querySelector(":checked").value)
        } else {
            this.initCard(
                collectFormValues(this.fieldsetTarget, {
                    nameTransform: name => name.replace(`${this.formPrefixValue}-`, ""),
                    skipValidation: true
                })
            )
        }
    }

    setupCategorieProduit(){
        const treeselect = new Treeselect({
            parentHtmlContainer: this.categorieProduitContainerTarget,
            value: this.categorieProduitInputTarget.value,
            options: this.categorieProduitValue,
            isSingleSelect: true,
            openCallback() {
                patchItems(treeselect.srcElement)
            },
            ...tsDefaultOptions
        })
        patchItems(treeselect.srcElement)
        treeselect.srcElement.addEventListener("update-dom", ()=>{patchItems(treeselect.srcElement)})
        this.categorieProduitContainerTarget.querySelector(".treeselect-input").classList.add("fr-input")

        treeselect.srcElement.addEventListener('input', (e) => {
            if (!e.detail) return
            const result = findPath(e.detail, this.categorieProduitValue)
            this.categorieProduitInputTarget.value = e.detail
            this.categorieProduitContainerTarget.querySelector("#categorie-produit .treeselect-input__tags-count").innerText = result.map(n => n.name).join(' > ')
        })
    }

    initCard(aliment) {
        this.shouldImmediatelyShowValue = false;
        this.cardContainerTargets.forEach(it => it.remove())
        this.element.insertAdjacentHTML("beforeend", this.renderCard(aliment))
        this.element.insertAdjacentHTML("beforeend", this.renderDeleteConfirmationDialog(aliment))
        dsfr(this.dialogTarget).modal.conceal()
    }

    handleConditionalFields(value){
        if (value === "aliment cuisine"){
            this.descriptionCompositionInputContainerTarget.classList.remove("fr-hidden")
            this.categorieProduitInputTarget.value = ''
            this.categorieProduitContainerTarget.querySelector("#categorie-produit .treeselect-input__tags-count").innerText = ''
            this.descriptionProduitInputContainerTarget.classList.add("fr-hidden")
            this.categorieProduitRootContainerTarget.classList.add("fr-hidden")
            this.descriptionCompositionInputTarget.value = ""
        } else {
            this.descriptionProduitInputContainerTarget.classList.remove("fr-hidden")
            this.categorieProduitRootContainerTarget.classList.remove("fr-hidden")
            this.descriptionCompositionInputContainerTarget.classList.add("fr-hidden")
            this.descriptionCompositionInputTarget.value =""
        }
    }

    onCloseForm() {
        // this.shouldImmediatelyShowValue indicates that the card has not be rendered yet.
        // In this case, the form is not considered valid and it should be deleted on close
        if (this.shouldImmediatelyShowValue) this.forceDelete()
    }

    onTypeAlimentChange(event){
        this.handleConditionalFields(event.target.value)
    }

    getDeleteConfirmationSentence(aliment){
        return `Confimez-vous vouloir supprimer l'aliment ${aliment.denomination} ?`
    }

    getDeleteConfirmationTitle(aliment){
        return "Suppression d'un aliment"
    }

    /**
     * @return {string} HTML
     */
    renderCard(aliment) {
        // language=HTML
        return `<div class="aliment-card fr-card" data-${this.identifier}-target="cardContainer">
            <div class="fr-card__body">
                <div class="fr-card__content">
                    <h3 class="fr-card__title" data-${this.identifier}-target="denomination">
                      ${aliment.denomination}
                    </h3>
                    <div class="fr-card__desc">
                        ${this.optionalText(aliment.motif_suspicion, `<p>${this.joinText(', ', ...aliment.motif_suspicion)}</p>`)}
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
