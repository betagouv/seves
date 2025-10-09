import {Controller} from "Stimulus";
import {applicationReady} from "Application";

/**
 * @property {Object.<string, {value: string, label: string}>} suspicionConclusionValue
 * @property {HTMLSelectElement} suspicionConclusionTarget
 * @property {HTMLSelectElement} selectedHazardTarget
 * @property {HTMLTemplateElement} selectedHazardConfirmedSelectTarget
 * @property {HTMLTemplateElement} selectedHazardSuspectedSelectTarget
 * @property {HTMLTemplateElement} selectedHazardOtherSelectTarget
 */
class ConclusionFormController extends Controller {
    static targets = ["suspicionConclusion", "selectedHazard", "selectedHazardConfirmedSelect", "selectedHazardSuspectedSelect", "selectedHazardOtherSelect"]
    static values = {suspicionConclusion: Object}

    suspicionConclusionTargetConnected(el) {
        el.dispatchEvent(new Event("change"))
    }

    onSuspicionConclusionChanged({target: {value}}) {
        if(value === this.suspicionConclusionValue.CONFIRMED.value) {
            this.selectedHazardTarget.innerHTML = this.selectedHazardConfirmedSelectTarget.innerHTML;
        } else if (value === this.suspicionConclusionValue.SUSPECTED.value) {
            this.selectedHazardTarget.innerHTML = this.selectedHazardSuspectedSelectTarget.innerHTML;
        } else {
            this.selectedHazardTarget.innerHTML = this.selectedHazardOtherSelectTarget.innerHTML;
        }

        this.selectedHazardTarget.value = "";

        if (value === this.suspicionConclusionValue.UNKNOWN.value
            || value === this.suspicionConclusionValue.DISCARDED.value) {
                this.selectedHazardTarget.setAttribute("disabled", "disabled");
            } else {
                this.selectedHazardTarget.removeAttribute("disabled");
            }
    }
}

applicationReady.then(app => app.register("conclusion-form", ConclusionFormController))
