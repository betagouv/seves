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


document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll(".no-tab-look .fr-tabs__panel").forEach(element =>{
        element.addEventListener('dsfr.conceal', event=>{
            const tabId = event.explicitOriginalTarget.getAttribute("id").replace("tabpanel-", "").replace("-panel", "")
            showOnlyActionsForDetection(tabId)
        })
    })

});