import {ViewManager, evenementViewModeConfig} from '/static/core/view_manager.js';

document.addEventListener('DOMContentLoaded', function() {
    const viewManager = new ViewManager(evenementViewModeConfig, "SSAEvenementProduitViewMode");
    viewManager.initialize()
});
