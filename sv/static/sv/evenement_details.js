import {ViewManager, evenementViewModeConfig} from './view_manager.js';

function showOnlyActionsForDetection(detectionId){
    document.querySelectorAll('[id^="detection-actions-"]').forEach(actionElement =>{

        if (actionElement.getAttribute("id") != "detection-actions-" + detectionId.toString()){

            actionElement.classList.add("fr-hidden")
        } else {
            actionElement.classList.remove("fr-hidden")

        }
    }
    )
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

document.addEventListener('DOMContentLoaded', function() {
    const viewManager = new ViewManager(evenementViewModeConfig);
    viewManager.initialize();

    document.querySelectorAll(".no-tab-look .fr-tabs__panel").forEach(element =>{
        element.addEventListener('dsfr.conceal', event=>{
            const tabId = event.explicitOriginalTarget.getAttribute("id").replace("tabpanel-", "").replace("-panel", "")
            showOnlyActionsForDetection(tabId)
        })
    })

    initializeDetectionTags();
});
