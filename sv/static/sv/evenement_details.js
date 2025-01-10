const VIEW_MODE_KEY = 'evenementViewMode';
const VIEW_MODE = {
    DETAIL: 'detail',
    SYNTHESE: 'synthese'
};
const SELECTORS = {
    DETAIL_BTN: 'detail-btn',
    SYNTHESE_BTN: 'synthese-btn',
    DETAIL_CONTENT: 'detail-content'
};

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

function saveViewMode(viewMode) {
    localStorage.setItem(VIEW_MODE_KEY, viewMode);
}

function getViewMode() {
    return localStorage.getItem(VIEW_MODE_KEY);
}

function toggleViewMode(event) {
    const detailContent = document.getElementById(SELECTORS.DETAIL_CONTENT);
    const viewMode = event.target.value;
    saveViewMode(viewMode);
    detailContent.classList.toggle('fr-hidden', viewMode === VIEW_MODE.SYNTHESE);
}

function initViewState() {
    const savedViewMode = getViewMode();
    const detailBtn = document.getElementById(SELECTORS.DETAIL_BTN);
    const syntheseBtn = document.getElementById(SELECTORS.SYNTHESE_BTN);
    const detailContent = document.getElementById(SELECTORS.DETAIL_CONTENT);

    if (!savedViewMode || savedViewMode === VIEW_MODE.DETAIL) {
        detailBtn.checked = true;
        detailContent.classList.remove('fr-hidden');
    } else {
        syntheseBtn.checked = true;
        detailContent.classList.add('fr-hidden');
    }
}

function initViewModeButtons() {
    const detailBtn = document.getElementById(SELECTORS.DETAIL_BTN);
    const syntheseBtn = document.getElementById(SELECTORS.SYNTHESE_BTN);
    detailBtn.addEventListener('change', toggleViewMode);
    syntheseBtn.addEventListener('change', toggleViewMode);
}

document.addEventListener('DOMContentLoaded', function() {
    initViewState();
    initViewModeButtons();
    document.querySelectorAll(".no-tab-look .fr-tabs__panel").forEach(element =>{
        element.addEventListener('dsfr.conceal', event=>{
            const tabId = event.explicitOriginalTarget.getAttribute("id").replace("tabpanel-", "").replace("-panel", "")
            showOnlyActionsForDetection(tabId)
        })
    })

});
