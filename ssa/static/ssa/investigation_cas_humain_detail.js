import {evenementViewModeConfig, ViewManager} from "ViewManager"

document.addEventListener("DOMContentLoaded", () => {
    const viewManager = new ViewManager(evenementViewModeConfig, "SSAInvestigationCasHumainViewMode")
    viewManager.initialize()
})
