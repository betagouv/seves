import { ViewManager, evenementViewModeConfig } from "ViewManager"

document.addEventListener("DOMContentLoaded", function () {
    const viewManager = new ViewManager(evenementViewModeConfig, "SSAEvenementProduitViewMode")
    viewManager.initialize()
})
