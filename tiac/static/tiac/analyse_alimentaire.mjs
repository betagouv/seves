import {applicationReady} from "Application"
import {BaseFormInModal} from "BaseFormInModal"
import {BaseFormSetController} from "BaseFormset"
import {hideHeader, patchItems, showHeader, tsDefaultOptions} from "CustomTreeSelect"
import {collectFormValues} from "Forms"

/**
 * @typedef AnalyseAlimentaireData
 * @property {String} categorie_danger
 * @property {String} comments
 * @property {String} etat_prelevement
 * @property {String} reference_prelevement
 * @property {String} reference_souche
 * @property {String} sent_to_lnr_cnr
 */

/**
 * @property {Object} categorieDangerValue
 * @property {HTMLInputElement} categorieDangerInputTarget
 * @property {HTMLInputElement} categorieDangerContainerTarget
 * @property {HTMLDivElement} categorieDangerHeaderTarget
 *
 * @property {string[]} categorieDangerValue
 * @property {boolean} customHeaderAddedValue
 * @property {boolean} shouldImmediatelyShowValue
 */
class AlimentFormController extends BaseFormInModal {
    static values = {shouldImmediatelyShow: {type: Boolean, default: false}}

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

    /** @param {AnalyseAlimentaireData} analyse */
    initCard(analyse) {
        this.shouldImmediatelyShowValue = false
        this.cardContainerTargets.forEach(it => it.remove())
        this.element.insertAdjacentHTML("beforeend", this.renderCard(analyse))
        this.element.insertAdjacentHTML("beforeend", this.renderDeleteConfirmationDialog(analyse))
        dsfr(this.dialogTarget).modal.conceal()
    }

    onCloseForm() {
        // this.shouldImmediatelyShowValue indicates that the card has not be rendered yet.
        // In this case, the form is not considered valid and it should be deleted on close
        if (this.shouldImmediatelyShowValue) this.forceDelete()
    }

    /** @param {AnalyseAlimentaireData} analyse */
    getDeleteConfirmationSentence(analyse) {
        return `Confimez-vous vouloir supprimer l'analyse alimentaire ${analyse.reference_prelevement}?`
    }

    getDeleteConfirmationTitle() {
        return "Suppression d'une analyse alimentaire"
    }

    /**
     * @param {AnalyseAlimentaireData} analyse
     * @return {string} HTML
     */
    renderCard(analyse) {
        // language=HTML
        return `
            <div class="analyse-card fr-card" data-${this.identifier}-target="cardContainer">
                <div class="fr-card__body">
                    <div class="fr-card__content">
                        <h3 class="fr-card__title" data-${this.identifier}-target="denomination">
                            <a href="#${analyse.reference_prelevement}" id="${analyse.reference_prelevement}" data-action="${this.identifier}#onModify:prevent:default" >
                            ${analyse.reference_prelevement}
                            </a>
                        </h3>
                        <div class="fr-card__desc">
                            <p class="fr-mb-4v">${analyse.etat_prelevement}</p>
                            ${this.optionalText(analyse.categorie_danger, this.renderBadges(analyse.categorie_danger))}
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

applicationReady.then(app => {
    app.register("analyse-alimentaire-formset", BaseFormSetController)
    app.register("analyse-alimentaire-form", AlimentFormController)
})
