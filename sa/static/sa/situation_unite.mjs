import {applicationReady} from "Application"
import {BaseFormInModal} from "BaseFormInModal"

let sharedTree = null

function getSharedTree() {
    if (sharedTree === null) {
        const el = document.getElementById("situation-unite-tree")
        sharedTree = el ? JSON.parse(el.textContent) : {}
    }
    return sharedTree
}

function isValidPath(tree, especeId, values) {
    if (!Object.hasOwn(tree, especeId)) return false
    let node = tree[especeId]
    for (const value of values) {
        if (!value) break
        if (!Object.hasOwn(node, value)) return false
        node = node[value]
    }
    return Object.keys(node).length === 0
}

/**
 * @property {HTMLInputElement[]} especeSelectTargets
 * @property {HTMLButtonElement} preciserButtonTarget
 * @property {HTMLElement} cardContainerTarget
 * @property {HTMLElement} errorMessageTarget
 * @property {HTMLSelectElement} typeLieuSelectTarget
 * @property {HTMLElement} modeElevageWrapperTarget
 * @property {HTMLSelectElement} modeElevageSelectTarget
 * @property {HTMLElement} typeProductionWrapperTarget
 * @property {HTMLSelectElement} typeProductionSelectTarget
 * @property {HTMLElement} typeElevageWrapperTarget
 * @property {HTMLSelectElement} typeElevageSelectTarget
 */
class SituationUniteController extends BaseFormInModal {
    static targets = [
        "especeSelect",
        "preciserButton",
        "errorMessage",
        "typeLieuSelect",
        "modeElevageWrapper",
        "modeElevageSelect",
        "typeProductionWrapper",
        "typeProductionSelect",
        "typeElevageWrapper",
        "typeElevageSelect",
    ]

    get levels() {
        return [
            {select: this.typeLieuSelectTarget, wrapper: null},
            {select: this.modeElevageSelectTarget, wrapper: this.modeElevageWrapperTarget},
            {select: this.typeProductionSelectTarget, wrapper: this.typeProductionWrapperTarget},
            {select: this.typeElevageSelectTarget, wrapper: this.typeElevageWrapperTarget},
        ]
    }

    get especeId() {
        const checked = this.especeSelectTargets.find(el => el.checked)
        return checked ? checked.value : ""
    }

    connect() {
        this.refreshSelectionCascade({keepSelection: true})
        if (this.hasCompleteSituation()) {
            this.initCard(this.currentSituation())
        }
    }

    onEspeceChange() {
        this.refreshSelectionCascade({keepSelection: true})

        const cardShown = this.preciserButtonTarget.classList.contains("fr-hidden")
        if (!cardShown) return

        if (this.hasCompleteSituation()) {
            this.cardContainerTarget.innerHTML = this.renderCard(this.currentSituation())
        } else {
            this.revertToButton()
        }
    }

    onLevelChange() {
        this.refreshSelectionCascade({keepSelection: true})
    }

    refreshSelectionCascade({keepSelection}) {
        this.hideError()

        const levels = this.levels
        const captured = levels.map(level => (keepSelection ? level.select.value : ""))
        const tree = getSharedTree()
        const especeId = this.especeId
        let node = Object.hasOwn(tree, especeId) ? tree[especeId] : null

        levels.forEach((level, index) => {
            const options = node !== null ? Object.keys(node) : []

            if (options.length === 0) {
                if (level.wrapper) level.wrapper.classList.add("fr-hidden")
                level.select.innerHTML = ""
                level.select.disabled = true
                node = null
                return
            }

            if (level.wrapper) level.wrapper.classList.remove("fr-hidden")
            level.select.disabled = false
            this.populateSelect(level.select, options)

            const value = captured[index]
            if (value && options.includes(value)) {
                level.select.value = value
                node = node[value]
            } else {
                level.select.value = ""
                node = null
            }
        })

        this.preciserButtonTarget.disabled = !Object.hasOwn(tree, especeId)
    }

    /** @param {HTMLSelectElement} select
     * @param {string[]} values */
    populateSelect(select, values) {
        select.innerHTML = ""

        const placeholder = document.createElement("option")
        placeholder.value = ""
        placeholder.textContent = "Choisir dans la liste"
        select.appendChild(placeholder)

        for (const value of values) {
            const option = document.createElement("option")
            option.value = value
            option.textContent = value
            select.appendChild(option)
        }
    }

    currentSituation() {
        return {
            typeLieu: this.typeLieuSelectTarget.value,
            modeElevage: this.modeElevageSelectTarget.value,
            typeProduction: this.typeProductionSelectTarget.value,
            typeElevage: this.typeElevageSelectTarget.value,
        }
    }

    hasCompleteSituation() {
        const s = this.currentSituation()
        return isValidPath(getSharedTree(), this.especeId, [s.typeLieu, s.modeElevage, s.typeProduction, s.typeElevage])
    }

    onCloseForm() {
        if (!this.keepChangesValue) {
            this.restoreForm()
            this.refreshSelectionCascade({keepSelection: true})
        }
        this.keepChangesValue = false
        super.onCloseForm()
    }

    showError() {
        this.errorMessageTarget.classList.remove("fr-hidden")
    }

    hideError() {
        this.errorMessageTarget.classList.add("fr-hidden")
    }

    clean(_formValues) {
        if (!this.hasCompleteSituation()) {
            this.showError()
            return false
        }
        this.hideError()
        return true
    }

    initCard(_formValues) {
        const situation = this.currentSituation()
        this.cardContainerTarget.innerHTML = this.renderCard(situation)
        this.preciserButtonTarget.classList.add("fr-hidden")
        dsfr(this.dialogTarget).modal.conceal()
    }

    revertToButton() {
        this.cardContainerTarget.innerHTML = ""
        this.preciserButtonTarget.classList.remove("fr-hidden")
    }

    /** @param {Object} situation */
    renderCard(situation) {
        const lines = [situation.typeLieu, situation.modeElevage, situation.typeProduction, situation.typeElevage]
            .filter(Boolean)
            .map(line => `<div>${line}</div>`)
            .join("")

        // language=HTML
        return `
            ${lines}
            <button
                type="button"
                class="fr-btn fr-btn--tertiary fr-btn--sm fr-icon-edit-line fr-btn--icon-left"
                data-action="${this.identifier}#onModify:prevent:default"
                data-testid="modify-situation-unite"
            >Modifier</button>`
    }
}

applicationReady.then(app => {
    app.register("situation-unite", SituationUniteController)
})
