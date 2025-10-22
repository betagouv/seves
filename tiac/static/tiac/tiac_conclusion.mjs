import {Controller} from "Stimulus";
import {applicationReady} from "Application";
import {findPath, patchItems, tsDefaultOptions} from "CustomTreeSelect"

/**
 * @property {Object.<string, {value: string, label: string}>} suspicionConclusionValue
 * @property {Object[]} selectedHazardConfirmedChoicesValue
 * @property {Object[]} selectedHazardSuspectedChoicesValue
 * @property {string} selectedHazardIdValue
 * @property {HTMLSelectElement} suspicionConclusionTarget
 * @property {HTMLDivElement} selectedHazardTreeselectTarget
 * @property {HTMLInputElement} selectedHazardTreeselectInputTarget
 * @property {HTMLTemplateElement} selectedHazardSuspectedOptionsTarget
 * @property {HTMLTemplateElement} selectedHazardOtherOptionsTarget
 */
class ConclusionFormController extends Controller {
    static targets = [
        "suspicionConclusion",
        "selectedHazardTreeselect",
        "selectedHazardTreeselectInput",
        "selectedHazardSuspectedOptions",
        "selectedHazardOtherOptions"
    ]
    static values = {suspicionConclusion: Object, selectedHazardConfirmedChoices: Array, selectedHazardSuspectedChoices: Array}

    /** @param {HTMLSelectElement} el */
    selectedHazardTreeselectTargetConnected(el) {
        this.treeselect = new Treeselect({
            parentHtmlContainer: el,
            value: [],
            options: [],
            isSingleSelect: false,
            isIndependentNodes: true,
            openCallback: () => patchItems(this.treeselect.srcElement),
            ...tsDefaultOptions
        })
        this.treeselect.srcElement.querySelector(".treeselect-input").classList.add("fr-input")
        patchItems(this.treeselect.srcElement)
    }

    /** @param {HTMLDivElement} el */
    selectedHazardTreeselectTargetDiconnected(el) {
        this.treeselect.destroy()
        this.treeselect = undefined
    }

    connect () {
        this.suspicionConclusionTarget.dispatchEvent(new Event("change"))
    }

    onUpdateDom() {
        if(this.treeselect === undefined) return;
        patchItems(this.treeselect.srcElement)
    }

    onTreeselectInput({detail}) {
        this.selectedHazardTreeselectInputTarget.value = detail?.join("||") ?? ""
    }

    onSuspicionConclusionChanged({target: {value}}) {
        if (value === this.suspicionConclusionValue.CONFIRMED.value) {
            this.treeselect.disabled = false;
            this.treeselect.options = this.selectedHazardConfirmedChoicesValue;
            this.treeselect.mount()
        } else if (value === this.suspicionConclusionValue.SUSPECTED.value) {
            this.treeselect.disabled = false;
            this.treeselect.options = this.selectedHazardSuspectedChoicesValue;
            this.treeselect.mount()
        } else {
            this.treeselect.options = [];
            this.treeselect.disabled = true;
            this.treeselect.mount()
        }

        this.treeselect.updateValue("")
    }
}

applicationReady.then(app => app.register("conclusion-form", ConclusionFormController))
