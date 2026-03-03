import choicesDefaults from "choicesDefaults"
import {evenementViewModeConfig, ViewManager} from "ViewManager"

const viewManager = new ViewManager(evenementViewModeConfig, "evenementViewMode")
viewManager.initialize()

if (document.querySelector("#id_transfered_to")) {
    new Choices(document.querySelector("#id_transfered_to"), choicesDefaults)
}
