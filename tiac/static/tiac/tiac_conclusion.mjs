import {applicationReady} from "Application"
import {Controller} from "Stimulus"

/**
 * @property {Object.<string, {value: string, label: string}>} suspicionConclusionChoicesValue
 * @property {string} suspicionConclusionValue
 * @property {HTMLSelectElement} suspicionConclusionTarget
 */
class ConclusionFormController extends Controller {
    static targets = [
        "suspicionConclusion",
        "conclusionRepas",
        "conclusionAliment",
        "notice",
        "noticeAliment",
        "noticeRepas",
        "selectedHazardConfirmedContainer",
        "selectedHazardSuspectedContainer",
        "requiredProxy",
    ]
    static values = {
        suspicionConclusionChoices: Object,
        suspicionConclusion: String,
        selectedHazardConfirmedChoices: Array,
        selectedHazardSuspectedChoices: Array,
    }
    static outlets = ["treeselect"]

    treeselectOutletConnected(outlet) {
        if (outlet.element.id === "fr-treeselect-id_selected_hazard_confirmed") {
            this.treeselectConfirmedOutlet = outlet
        } else if (outlet.element.id === "fr-treeselect-id_selected_hazard_suspected") {
            this.treeselectSuspectedOutlet = outlet
        }
        outlet.element.addEventListener("treeselect:choices", this.onTreeselectChoicesChanged)
        this.#syncTreeselects()
        this.#syncRequiredProxyValue()
    }

    treeselectOutletDisconnected(outlet) {
        outlet.element.removeEventListener("treeselect:choices", this.onTreeselectChoicesChanged)
    }

    onTreeselectChoicesChanged = () => {
        this.#syncRequiredProxyValue()
    }

    // The hidden field is needed to "fake" a required checkbox, sync the value so that we can submit the modal
    // when we have a value
    #syncRequiredProxyValue() {
        const value = this.suspicionConclusionValue
        if (value === this.suspicionConclusionChoicesValue.CONFIRMED.value) {
            this.requiredProxyTarget.value = this.treeselectConfirmedOutlet?.choices.size > 0 ? "x" : ""
        } else if (value === this.suspicionConclusionChoicesValue.SUSPECTED.value) {
            this.requiredProxyTarget.value = this.treeselectSuspectedOutlet?.choices.size > 0 ? "x" : ""
        }
    }
    suspicionConclusionTargetConnected(el) {
        el.dispatchEvent(new Event("change"))
    }

    #syncTreeselects() {
        if (!this.treeselectConfirmedOutlet || !this.treeselectSuspectedOutlet) return

        const value = this.suspicionConclusionValue
        const isConfirmed = value === this.suspicionConclusionChoicesValue.CONFIRMED.value
        const isSuspected = value === this.suspicionConclusionChoicesValue.SUSPECTED.value

        this.treeselectConfirmedOutlet.setDisabledState(!isConfirmed)
        if (!isConfirmed) this.treeselectConfirmedOutlet.unselectAll()

        this.treeselectSuspectedOutlet.setDisabledState(!isSuspected)
        if (!isSuspected) this.treeselectSuspectedOutlet.unselectAll()
    }

    suspicionConclusionValueChanged(value) {
        const isConfirmed = value === this.suspicionConclusionChoicesValue.CONFIRMED.value
        const isSuspected = value === this.suspicionConclusionChoicesValue.SUSPECTED.value
        const isDiscarded = value === this.suspicionConclusionChoicesValue.DISCARDED.value

        this.conclusionRepasTarget.disabled = isDiscarded
        this.conclusionRepasTarget.required = isConfirmed || isSuspected
        this.requiredProxyTarget.required = isConfirmed || isSuspected
        this.conclusionAlimentTarget.disabled = isDiscarded

        if (isDiscarded) {
            this.conclusionRepasTarget.value = ""
            this.conclusionAlimentTarget.value = ""
        }

        // Still show this fields as a "fake" one for Discarded, Unknwon and no value
        this.selectedHazardConfirmedContainerTarget.classList.toggle("fr-hidden", isSuspected)
        this.selectedHazardConfirmedContainerTarget
            .querySelector("label")
            .classList.toggle("required-field", isConfirmed)

        this.selectedHazardSuspectedContainerTarget.classList.toggle("fr-hidden", !isSuspected)
        this.selectedHazardSuspectedContainerTarget
            .querySelector("label")
            .classList.toggle("required-field", isSuspected)

        if (this.suspicionConclusionTarget.selectedOptions?.[0]?.dataset?.needsNotice === "true") {
            this.noticeTarget.classList.remove("fr-hidden")
        } else {
            this.noticeTarget.classList.add("fr-hidden")
        }
        this.#syncTreeselects()
        this.#syncRequiredProxyValue()
    }

    onSuspicionConclusionChanged({target: {value}}) {
        this.suspicionConclusionValue = value
    }

    conclusionAlimentTargetConnected() {
        if (this.conclusionAlimentTarget.value) {
            this.noticeAlimentTarget.classList.add("fr-hidden")
        } else {
            this.noticeAlimentTarget.classList.remove("fr-hidden")
        }
    }

    conclusionRepasTargetConnected() {
        if (this.conclusionRepasTarget.value) {
            this.noticeRepasTarget.classList.add("fr-hidden")
        } else {
            this.noticeRepasTarget.classList.remove("fr-hidden")
        }
    }

    onAlimentChanged(event) {
        if (event.target.value) {
            this.noticeAlimentTarget.classList.add("fr-hidden")
        } else {
            this.noticeAlimentTarget.classList.remove("fr-hidden")
        }
    }

    onRepasChanged(event) {
        this.noticeRepasTarget.classList.toggle("fr-hidden", event.target.value)
    }
}

applicationReady.then(app => app.register("conclusion-form", ConclusionFormController))
