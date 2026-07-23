import {applicationReady} from "Application"
import {Controller} from "Stimulus"

/**
 * ******** Targets ********
 * @property {HTMLInputElement} precisionsTarget
 * @property {HTMLInputElement[]} analysesTargets
 * ******** Values ********
 * @property {String} analysesValue
 * ******** Outlets ********
 * @property {Treeselect} treeselectOutlet
 */
class AgentsPathogeneController extends Controller {
    static targets = ["precisions", "analyses"]
    static values = {analyses: String}
    static outlets = ["treeselect"]

    initialize() {
        this.analysesValue = this.analysesTargets.find(it => it.checked)?.value ?? ""
    }

    analysesValueChanged(value) {
        if (value === "oui") {
            this.precisionsTarget.disabled = false
            this.treeselectOutlet.setDisabledState(false)
        } else {
            this.precisionsTarget.disabled = true
            this.treeselectOutlet.setDisabledState(true)
            this.treeselectOutlet.unselectAll()
        }
    }

    onAnalyseChange({target}) {
        if (target.checked) {
            this.analysesValue = target.value
        }
    }
}

applicationReady.then(app => {
    app.register("agents-pathogene", AgentsPathogeneController)
})
