import {BaseFormSetController} from "BaseFormset"
import {BaseFormInModal} from "BaseFormInModal"
import {applicationReady} from "Application"
import {collectFormValues} from "Forms";
import {hideHeader, patchItems, showHeader, tsDefaultOptions} from "CustomTreeSelect"

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
    static targets = ["categorieDangerInput", "categorieDangerContainer", "categorieDangerHeader"]
    static values = {
        shouldImmediatelyShow: {type: Boolean, default: false},
        categorieDanger: Array,
        customHeaderAdded: {type: Boolean, default: false}
    };

    connect() {
        this.setupcategorieDanger()
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

    /** @param {AnalyseAlimentaireData} analyse */
    initCard(analyse) {
        this.shouldImmediatelyShowValue = false;
        this.cardContainerTargets.forEach(it => it.remove())
        this.element.insertAdjacentHTML("beforeend", this.renderCard(analyse))
        this.element.insertAdjacentHTML("beforeend", this.renderDeleteConfirmationDialog(analyse))
        dsfr(this.dialogTarget).modal.conceal()
    }

    setupcategorieDanger() {
        this.treeselect = new Treeselect({
            ...tsDefaultOptions,
            parentHtmlContainer: this.categorieDangerContainerTarget,
            value: this.categorieDangerInputTarget.value.split("||").map(v => v.trim()),
            options: this.categorieDangerValue,
            isSingleSelect: false,
            openCallback: this.treeselectOpenCallback.bind(this),
            searchCallback: item => {
                if (item.length === 0) {
                    showHeader(this.treeselect.srcElement, ".categorie-danger-header")
                } else {
                    hideHeader(this.treeselect.srcElement, ".categorie-danger-header")
                }
            },
        })
        this.treeselect.srcElement.addEventListener("update-dom", () => {
            patchItems(this.treeselect.srcElement)
        })
        this.treeselect.srcElement.addEventListener('input', (e) => {
            if (!!e.detail) {
                this.categorieDangerInputTarget.value = e.detail.join("||")
            }
        })
    }

    onShortcut(event) {
        const label = event.target.getElementsByTagName("label")[0]
        const value = label.textContent.trim()
        const checkbox = this.categorieDangerContainerTarget.querySelector(`[id$="${label.getAttribute("for")}"]`)
        checkbox.checked = !checkbox.checked

        let valuesToSet = this.treeselect.value
        if (checkbox.checked) {
            valuesToSet.push(value)
        } else {
            valuesToSet.pop(value)
        }

        this.treeselect.updateValue(valuesToSet)
        this.categorieDangerInputTarget.value = valuesToSet.join("||")
        let text = ""
        if (valuesToSet.length === 1) {
            text = valuesToSet[0]
        } else {
            text = `${valuesToSet.length} ${this.treeselect.tagsCountText}`
        }
        this.categorieDangerContainerTarget.querySelector(".treeselect-input__tags-count").innerText = text
    }

    onCloseForm() {
        // this.shouldImmediatelyShowValue indicates that the card has not be rendered yet.
        // In this case, the form is not considered valid and it should be deleted on close
        if (this.shouldImmediatelyShowValue) this.forceDelete()
    }

    treeselectOpenCallback() {
        patchItems(this.treeselect.srcElement)
        if (this.customHeaderAddedValue) {
            showHeader(this.treeselect.srcElement, ".categorie-danger-header")
            return;
        }
        const list = this.categorieDangerContainerTarget.querySelector(".treeselect-list")
        if (list) {
            const fragment = this.categorieDangerHeaderTarget.content.cloneNode(true);
            list.prepend(fragment);
            this.customHeaderAddedValue = true
        }
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
            <div class="aliment-card fr-card" data-${this.identifier}-target="cardContainer">
                <div class="fr-card__body">
                    <div class="fr-card__content">
                        <h3 class="fr-card__title" data-${this.identifier}-target="denomination">
                            ${analyse.reference_prelevement}
                        </h3>
                        <div class="fr-card__desc">
                            <p class="fr-mb-4v">${analyse.etat_prelevement}</p>
                            <p class="fr-badge fr-badge--sm fr-badge--info fr-badge--no-icon">
                                ${analyse.categorie_danger}
                            </p>
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
