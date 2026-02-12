import {BaseFormSetController} from "BaseFormset"
import {BaseFormInModal} from "BaseFormInModal"
import {applicationReady} from "Application";
import {collectFormValues} from 'Forms'


class RepasFormController extends BaseFormInModal {
    static targets = [
        "denominationInput",
        "typeCollectiviteInputContainer",
        "typeCollectiviteInput",
    ]

    connect() {
        if (this.shouldImmediatelyShowValue) {
            this.openDialog()
        } else {
            this.initCard(
                collectFormValues(this.fieldsetTarget, {
                    nameTransform: name => name.replace(`${this.formPrefixValue}-`, ""),
                    skipValidation: true
                })
            )
        }
    }

    onCloseForm() {
        // this.shouldImmediatelyShowValue indicates that the card has not be rendered yet.
        // In this case, the form is not considered valid and it should be deleted on close
        if (this.shouldImmediatelyShowValue) this.forceDelete()
    }

    onTypeRepasChoice(event){
        const selectedOption = event.target.options[event.target.selectedIndex]
        if (selectedOption.getAttribute('data-needs-type-collectivite') === 'true') {
            this.typeCollectiviteInputContainerTarget.classList.remove("fr-hidden")
        } else {
            this.typeCollectiviteInputContainerTarget.classList.add("fr-hidden")
            this.typeCollectiviteInputTarget.value = ""
        }

    }

    initCard(repas) {
        this.shouldImmediatelyShowValue = false;
        this.cardContainerTargets.forEach(it => it.remove())
        this.element.insertAdjacentHTML("beforeend", this.renderCard(repas))
        this.element.insertAdjacentHTML("beforeend", this.renderDeleteConfirmationDialog(repas))
        dsfr(this.dialogTarget).modal.conceal()
    }

    getDeleteConfirmationSentence(repas){
        return `Confimez-vous vouloir supprimer le repas ${repas.denomination} ?`
    }

    getDeleteConfirmationTitle(repas){
        return "Suppression d'un repas"
    }

    /**
     * @return {string} HTML
     */
    renderCard(repas) {
        // language=HTML
        const nbParticpants = `Participants : ${repas.nombre_participant}`
        return `<div class="repas-card fr-card" data-${this.identifier}-target="cardContainer">
            <div class="fr-card__body">
                <div class="fr-card__content">
                    <h3 class="fr-card__title" data-${this.identifier}-target="denomination">
                      ${repas.denomination}
                    </h3>
                    <div class="fr-card__desc">
                        ${this.optionalText(repas.datetime_repas, `<p class="fr-card__detail fr-icon-calendar-2-line fr-my-2v">${this.formatDate(repas.datetime_repas)}</p>`)}
                        ${this.optionalText(repas.type_repas, `<p>${repas.type_repas}</p>`)}
                        ${this.optionalText(repas.nombre_participant, this.renderBadges([nbParticpants]))}
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
    app.register("repas-formset", BaseFormSetController)
    app.register("repas-form", RepasFormController)
})
