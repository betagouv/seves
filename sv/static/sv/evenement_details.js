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

function toggleViewMode(event) {
    const detailContent = document.getElementById('detail-content');
    const viewMode = event.target.value;
    detailContent.classList.toggle('fr-hidden', viewMode === 'synthese');
}

function initViewModeButtons() {
    const detailBtn = document.getElementById('detail-btn');
    const syntheseBtn = document.getElementById('synthese-btn');
    detailBtn.addEventListener('change', toggleViewMode);
    syntheseBtn.addEventListener('change', toggleViewMode);
}

document.addEventListener('DOMContentLoaded', function() {
    initViewModeButtons();
    document.querySelectorAll(".no-tab-look .fr-tabs__panel").forEach(element =>{
        element.addEventListener('dsfr.conceal', event=>{
            const tabId = event.explicitOriginalTarget.getAttribute("id").replace("tabpanel-", "").replace("-panel", "")
            showOnlyActionsForDetection(tabId)
        })
    })

});
