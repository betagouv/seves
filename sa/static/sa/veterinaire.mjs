import {applicationReady, escapeHTML} from "Application"
import {BaseFormInModal} from "BaseFormInModal"
import {BaseFormSetController} from "BaseFormset"
import {collectFormValues} from "Forms"

/**
 * Rows of the "Espèces concernées et exposées" (identified by their form prefix,
 * as they may not be saved yet)
 * @return {{prefix: string, label: string}[]}
 */
function getEspecesConcernees() {
    return [...document.querySelectorAll("[data-espece-concernee-prefix]")].flatMap(row => {
        const target = name => row.querySelector(`[data-especes-concernees-row-target="${name}"]`)
        const espece = target("especeField").querySelector('input[type="radio"]:checked')?.labels[0]
        if (target("deleteInput").value === "on" || !espece) return []

        const identifiant = target("identifiantInput").value.trim()
        const especeName = espece.textContent.trim()
        return [
            {
                prefix: row.dataset.especeConcerneePrefix,
                label: identifiant ? `${especeName} (${identifiant})` : especeName,
            },
        ]
    })
}

/**
 * @property {HTMLElement} especesConcerneesTarget
 * @property {HTMLElement} badgesTarget
 * @property {boolean} hasBadgesTarget
 */
class VeterinaireFormController extends BaseFormInModal {
    static targets = [...BaseFormInModal.targets, "especesConcernees", "badges"]

    connect() {
        if (this.shouldImmediatelyShowValue) {
            this.syncEspecesConcernees({keepSelection: false})
            this.openDialog()
        } else {
            this.syncEspecesConcernees()
            this.initCard(this.collectValues())
        }
    }

    collectValues() {
        return collectFormValues(this.fieldsetTarget, {
            nameTransform: name => name.replace(`${this.formPrefixValue}-`, ""),
            skipValidation: true,
        })
    }

    openDialog() {
        this.syncEspecesConcernees()
        super.openDialog()
    }

    onEspecesConcerneesChanged() {
        this.syncEspecesConcernees()
        if (this.hasBadgesTarget) {
            this.badgesTarget.innerHTML = this.renderBadges(this.getBadges(this.collectValues()))
        }
    }

    syncEspecesConcernees({keepSelection = true} = {}) {
        const name = `${this.formPrefixValue}-especes_concernees`
        const container = this.especesConcerneesTarget.querySelector(`#id_${name}`)
        const checked = new Set(
            keepSelection ? [...container.querySelectorAll("input:checked")].map(it => it.value) : [],
        )
        const especesConcernees = getEspecesConcernees()
        const isSingle = especesConcernees.length === 1

        container.replaceChildren(
            ...especesConcernees.map(({prefix, label}, index) => {
                const wrapper = document.createElement("div")
                const input = document.createElement("input")
                input.type = "checkbox"
                input.name = name
                input.value = prefix
                input.id = `${container.id}_${index}`
                input.className = "fr-checkbox-group fr-mt-1w"
                input.checked = isSingle || checked.has(prefix)
                input.disabled = isSingle
                const labelElement = document.createElement("label")
                labelElement.htmlFor = input.id
                labelElement.className = "fr-mb-2v"
                labelElement.textContent = label
                wrapper.append(input, labelElement)
                return wrapper
            }),
        )
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
    getBadges(veterinaire) {
        return [
            (veterinaire.type_veterinaire || "").toUpperCase(),
            ...(veterinaire.especes_concernees || []).map(escapeHTML),
        ]
    }

    /** @param {Object} veterinaire */
    renderCard(veterinaire) {
        const title =
            veterinaire.prenom || veterinaire.nom
                ? `${veterinaire.prenom} ${veterinaire.nom}`
                : veterinaire.nom_structure

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
                        <div class="fr-card__desc" data-${this.identifier}-target="badges">
                            ${this.renderBadges(this.getBadges(veterinaire))}
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
