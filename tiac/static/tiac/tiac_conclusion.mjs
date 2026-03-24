import {applicationReady} from "Application"
import {hideHeader, patchItems, showHeader, tsDefaultOptions} from "CustomTreeSelect"
import {Controller, defaultSchema} from "Stimulus"

/**
 * @property {string} suspicionConclusionValue
 * @property {string} selectedHazardIdValue
 * @property {boolean} selectedHazardTreeselectInitializedValue
 * @property {HTMLSelectElement} suspicionConclusionTarget
 * @property {HTMLFieldSetElement} selectedHazarContainerTarget
 * @property {HTMLTemplateElement} selectedHazarEmptySelectionTplTarget
 * @property {HTMLTemplateElement} selectedHazarConfirmedTplTarget
 * @property {HTMLTemplateElement} selectedHazarSuspectedTplTarget
 */
class ConclusionFormController extends Controller {
    static targets = [
        "suspicionConclusion",
        "conclusionRepas",
        "conclusionAliment",
        "selectedHazarContainer",
        "selectedHazarEmptySelectionTpl",
        "selectedHazarConfirmedTpl",
        "selectedHazarSuspectedTpl",
    ]
    static values = {suspicionConclusion: String}

    suspicionConclusionTargetConnected(el) {
        el.dispatchEvent(new Event("change"))
    }

    suspicionConclusionValueChanged(value) {
        this.conclusionRepasTarget.disabled = false
        this.conclusionAlimentTarget.disabled = false
        switch (value) {
            case "CONFIRMED":
                this.selectedHazarContainerTarget.innerHTML = this.selectedHazarConfirmedTplTarget.innerHTML
                break
            case "SUSPECTED":
                this.selectedHazarContainerTarget.innerHTML = this.selectedHazarSuspectedTplTarget.innerHTML
                break
            default:
                this.selectedHazarContainerTarget.innerHTML = this.selectedHazarEmptySelectionTplTarget.innerHTML
                break
        }
    }

    onSuspicionConclusionChanged({target: {value}}) {
        this.suspicionConclusionValue = value
    }
}

applicationReady.then(app => app.register("conclusion-form", ConclusionFormController))
