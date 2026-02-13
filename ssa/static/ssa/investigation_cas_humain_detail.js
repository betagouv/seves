import { ViewManager, evenementViewModeConfig } from "ViewManager"

document.addEventListener("DOMContentLoaded", function () {
    const viewManager = new ViewManager(evenementViewModeConfig, "SSAInvestigationCasHumainViewMode")
    viewManager.initialize()
})
