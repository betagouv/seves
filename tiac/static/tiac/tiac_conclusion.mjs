import {Controller} from "Stimulus";
import {applicationReady} from "Application";
import {findPath, hideHeader, patchItems, showHeader, tsDefaultOptions} from "CustomTreeSelect"

/**
 * @property {Object.<string, {value: string, label: string}>} suspicionConclusionChoicesValue
 * @property {string} suspicionConclusionValue
 * @property {Object[]} selectedHazardConfirmedChoicesValue
 * @property {Object[]} selectedHazardSuspectedChoicesValue
 * @property {string} selectedHazardIdValue
 * @property {boolean} selectedHazardTreeselectInitializedValue
 * @property {HTMLSelectElement} suspicionConclusionTarget
 * @property {HTMLDivElement} selectedHazardTreeselectTarget
 * @property {HTMLInputElement} selectedHazardTreeselectInputTarget
 * @property {HTMLTemplateElement} selectedHazardTreeselectHeaderTarget
 */
class ConclusionFormController extends Controller {
    static targets = [
        "suspicionConclusion",
        "conclusionRepas",
        "conclusionAliment",
        "selectedHazardTreeselect",
        "selectedHazardTreeselectInput",
        "selectedHazardTreeselectHeader",
    ]
    static values = {
        suspicionConclusionChoices: Object,
        suspicionConclusion: String,
        selectedHazardConfirmedChoices: Array,
        selectedHazardSuspectedChoices: Array,
        selectedHazardTreeselectInitialized: {type: Boolean, default: false}
    }

    /** @param {HTMLSelectElement} el */
    selectedHazardTreeselectTargetConnected(el) {
        this.treeselect = new Treeselect({
            ...tsDefaultOptions,
            parentHtmlContainer: el,
            value: [],
            options: [],
            isSingleSelect: false,
            isIndependentNodes: true,
            openCallback: this.treeselectOpenCallback.bind(this),
            searchCallback: item => {
                if (item.length === 0) {
                    showHeader(this.treeselect.srcElement, ".categorie-danger-header")
                } else {
                    hideHeader(this.treeselect.srcElement, ".categorie-danger-header")
                }
            },
        })
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
        if (detail.length === 0) {
            this.element.querySelectorAll("[id^='shortcut_']").forEach(checkbox => {
                checkbox.checked = false
            })
        } else {
            this.selectedHazardTreeselectInputTarget.value = detail.join("||")
        }
    }

    treeselectOpenCallback () {
        if (this.suspicionConclusionValue === this.suspicionConclusionChoicesValue.CONFIRMED.value) {
            patchItems(this.treeselect.srcElement)
            if (this.treeselect.srcElement.querySelectorAll(".categorie-danger-header").length !== 0) {
                showHeader(this.treeselect.srcElement, ".categorie-danger-header")
                return;
            }
            const list = this.selectedHazardTreeselectTarget.querySelector(".treeselect-list")
            if (list) {
                const fragment = this.selectedHazardTreeselectHeaderTarget.content.cloneNode(true);
                list.prepend(fragment);
                this.customHeaderAddedValue = true
            }
        }
    }

    onShortcut({target}) {
        const label = target.getElementsByTagName("label")[0]
        const value = label.textContent.trim()
        const checkbox = this.selectedHazardTreeselectTarget.querySelector(`[id$="${label.getAttribute("for")}"]`)
        checkbox.checked = !checkbox.checked

        let valuesToSet = this.treeselect.value
        if (checkbox.checked) {
            valuesToSet.push(value)
        } else {
            valuesToSet.pop(value)
        }

        this.treeselect.updateValue(valuesToSet)
        this.selectedHazardTreeselectInputTarget.value = valuesToSet.join("||")
        let text = ""
        if (valuesToSet.length === 1) {
            text = valuesToSet[0]
        } else {
            text = `${valuesToSet.length} ${this.treeselect.tagsCountText}`
        }
        this.selectedHazardTreeselectTarget.querySelector(".treeselect-input__tags-count").innerText = text
    }

    onSuspicionConclusionChanged({target: {value}}) {
        this.suspicionConclusionValue = value
        this.conclusionRepasTarget.disabled = false;
        this.conclusionAlimentTarget.disabled = false;
        if (value === this.suspicionConclusionChoicesValue.CONFIRMED.value) {
            this.treeselect.disabled = false;
            this.treeselect.placeholder = "Choisir dans la liste d’après les résultats d’analyse";
            this.selectedHazardTreeselectInputTarget.required = true;
            this.treeselect.options = this.selectedHazardConfirmedChoicesValue;
            this.treeselect.mount()
        } else if (value === this.suspicionConclusionChoicesValue.SUSPECTED.value) {
            this.treeselect.disabled = false;
            this.treeselect.placeholder = "Choisir dans la liste parmi les dangers syndromiques";
            this.selectedHazardTreeselectInputTarget.required = true;
            this.treeselect.options = this.selectedHazardSuspectedChoicesValue;
            this.treeselect.mount()
        } else if (value === this.suspicionConclusionChoicesValue.DISCARDED.value) {
            this.treeselect.options = [];
            this.treeselect.placeholder = "Choisir dans la liste";
            this.treeselect.disabled = true;
            this.conclusionRepasTarget.value = '';
            this.conclusionRepasTarget.disabled = true;
            this.conclusionAlimentTarget.value = '';
            this.conclusionAlimentTarget.disabled = true;
            this.selectedHazardTreeselectInputTarget.required = false;
            this.treeselect.mount()
        } else if (value === this.suspicionConclusionChoicesValue.UNKNOWN.value) {
            this.treeselect.options = [];
            this.treeselect.placeholder = "Choisir dans la liste";
            this.treeselect.disabled = true;
            this.selectedHazardTreeselectInputTarget.required = false;
            this.treeselect.mount()
        }

        if(this.selectedHazardTreeselectInitializedValue) {
            this.treeselect.updateValue("")
        } else {
            this.treeselect.updateValue(this.selectedHazardTreeselectInputTarget.value.split("||"))
            this.selectedHazardTreeselectInitializedValue = true
        }
    }
}

applicationReady.then(app => app.register("conclusion-form", ConclusionFormController))
