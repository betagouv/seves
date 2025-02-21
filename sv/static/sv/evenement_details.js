import {ViewManager, evenementViewModeConfig} from './view_manager.js';

function showOnlyActionsForDetection(detectionId){
    document.querySelectorAll('[id^="detection-actions-"]').forEach(element =>{
        element.classList.add("fr-hidden")
    })
    document.querySelector(`[id^="detection-actions-${detectionId}"]`).classList.remove("fr-hidden")
}

function initializeDetectionTags() {
    const tags = document.querySelectorAll('.fr-tag');

    tags.forEach(tag => {
        tag.addEventListener('click', () => {
            // Retirer la classe selected de tous les tags
            tags.forEach(t => t.classList.remove('selected'));

            // Ajouter la classe selected au tag cliqué
            tag.classList.add('selected');
        });
    });
}

function selectZoneTab() {
    const params = new URLSearchParams(window.location.search);
    if (params.get('tab') === 'zone') {
        const tabzone = document.getElementById("tabpanel-zone-panel");
        dsfr(tabzone).tabPanel.disclose();
    }
}

document.addEventListener('DOMContentLoaded', function() {

    // TODO: merge PR MAJ DSFR v1.13.0 pour utiliser dsfr.ready/dsfr.start
    document.documentElement.addEventListener('dsfr.ready', function() {
        selectZoneTab();
    });

    const viewManager = new ViewManager(evenementViewModeConfig);
    viewManager.initialize();

    document.querySelectorAll(".no-tab-look .fr-tabs__panel").forEach(element =>{
        element.addEventListener('dsfr.disclose', event=>{
            const tabId = event.target.getAttribute("id").replace("tabpanel-", "").replace("-panel", "")
            showOnlyActionsForDetection(tabId)
        })
    })

    const selectedTagDocument = document.querySelector(".no-tab-look .fr-tag.selected")
    showOnlyActionsForDetection(selectedTagDocument.getAttribute("id").replace("tabpanel-", ""))

    initializeDetectionTags();
});
