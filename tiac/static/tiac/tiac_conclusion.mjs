import {Controller} from "Stimulus";
import {applicationReady} from "Application";
import {findPath, patchItems, tsDefaultOptions} from "CustomTreeSelect"

/**
 * @property {Object.<string, {value: string, label: string}>} suspicionConclusionValue
 * @property {Object[]} selectedHazardConfirmedValue
 * @property {HTMLSelectElement} suspicionConclusionTarget
 * @property {HTMLSelectElement} selectedHazardSelectTarget
 * @property {HTMLDivElement} selectedHazardTreeselectTarget
 * @property {HTMLInputElement} selectedHazardTreeselectInputTarget
 * @property {HTMLTemplateElement} selectedHazardSuspectedOptionsTarget
 * @property {HTMLTemplateElement} selectedHazardOtherOptionsTarget
 */
class ConclusionFormController extends Controller {
    static targets = [
        "suspicionConclusion",
        "selectedHazardSelect",
        "selectedHazardTreeselect",
        "selectedHazardTreeselectInput",
        "selectedHazardSuspectedOptions",
        "selectedHazardOtherOptions"
    ]
    static values = {suspicionConclusion: Object, selectedHazardConfirmed: Array}

    /** @param {HTMLSelectElement} el */
    selectedHazardTreeselectTargetConnected(el) {
        this.treeselect = new Treeselect({
            parentHtmlContainer: el,
            value: [],
            options: this.selectedHazardConfirmedValue,
            isSingleSelect: false,
            isIndependentNodes: true,
            openCallback: () => patchItems(this.treeselect.srcElement),
            ...tsDefaultOptions
        })
        this.treeselect.srcElement.querySelector(".treeselect-input").classList.add("fr-input")
        patchItems(this.treeselect.srcElement)
        this.treeselect.srcElement.addEventListener("update-dom", ()=> patchItems(this.treeselect.srcElement))
        this.treeselect.srcElement.addEventListener('input', e => {
            if (!e.detail) return
            this.selectedHazardTreeselectInputTarget.value = e.detail.join("||")
        })
    }

    /** @param {HTMLDivElement} el */
    selectedHazardTreeselectTargetDiconnected(el) {
        this.treeselect.destroy()
        this.treeselect = undefined
    }

    connect () {
        this.suspicionConclusionTarget.dispatchEvent(new Event("change"))
    }

    onSuspicionConclusionChanged({target: {value}}) {
        if (value === this.suspicionConclusionValue.SUSPECTED.value) {
            this.selectedHazardSelectTarget.innerHTML = this.selectedHazardSuspectedOptionsTarget.innerHTML;
            this.selectedHazardSelectTarget.disabled = false;
        } else {
            this.selectedHazardSelectTarget.innerHTML = this.selectedHazardOtherOptionsTarget.innerHTML;
            this.selectedHazardSelectTarget.disabled = true;
        }

        if (value === this.suspicionConclusionValue.CONFIRMED.value) {
            this.selectedHazardTreeselectTarget.parentElement.classList.remove("fr-hidden")
            this.selectedHazardTreeselectInputTarget.disabled = false
            this.selectedHazardSelectTarget.parentElement.classList.add("fr-hidden")
        } else {
            this.selectedHazardTreeselectTarget.parentElement.classList.add("fr-hidden")
            this.selectedHazardTreeselectInputTarget.disabled = true
            this.selectedHazardSelectTarget.parentElement.classList.remove("fr-hidden")
        }

        this.treeselect.updateValue("")
        this.selectedHazardSelectTarget.value = "";
    }
}

applicationReady.then(app => app.register("conclusion-form", ConclusionFormController))
