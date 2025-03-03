let pickedDetections = []
let allChoices = []

function rebuildDetectionOptions(detectionChoices){
    detectionChoices.enable()
    const currentChoices = detectionChoices.passedElement.optionsAsChoices()
    const updatedChoices = currentChoices.map(choice => ({
        value: choice.value,
        label: choice.label,
        disabled: pickedDetections.includes(choice.value),
        selected: choice.selected
    }));
    detectionChoices.clearChoices()
    detectionChoices.setChoices(updatedChoices, 'value', 'label', false);
}


function rebuildChoicesOptions(){
    allChoices.forEach(choices => { rebuildDetectionOptions(choices)})
}

function initializeChoices(elementId) {
    options = {
        searchResultLimit: 500,
        classNames: {
            containerInner: 'fr-select',
        },
        removeItemButton: true,
        itemSelectText: '',
        noResultsText: 'Aucun résultat trouvé',
        noChoicesText: 'Aucune fiche détection à sélectionner',
        searchFields: ['label'],
    }
    let choices = new Choices(document.getElementById(elementId), options)
    choices.passedElement.element.addEventListener('change', event=> {
        initializepickedDetections()
        rebuildChoicesOptions()
    })
    allChoices.push(choices)
    rebuildDetectionOptions(choices)
}

function initializeAllChoices() {
    const totalForms = parseInt(document.getElementById('id_zoneinfestee_set-TOTAL_FORMS').value);
    for (let i = 0; i < totalForms; i++) {
        initializeChoices(`id_zoneinfestee_set-${i}-detections`);
    }
}

function initializepickedDetections() {
    pickedDetections = []
    allChoices.forEach((detectionChoice) =>{
        detectionChoice.getValue().forEach((item) =>{
            pickedDetections.push(item.value)
        })
    } )
}


function getNextIdToUse(){
    let num = 0
    while (document.getElementById(`id_zoneinfestee_set-${num}-nom`)) {
        num++
    }
    return num
}

function addZoneInfesteeForm() {
    const nextIdToUse = getNextIdToUse()
    let newTabTemplate = document.getElementById('zone-form-template').innerHTML;
    newTabTemplate = newTabTemplate.replace(/__prefix__/g, nextIdToUse.toString());
    document.getElementById('zones-infestees').insertAdjacentHTML('beforeend', newTabTemplate);
    const newDeleteBtn = document.querySelector(`#modal-delete-zi-confirmation-${nextIdToUse} .delete-zone-infestee`)
    newDeleteBtn.addEventListener("click", removeZoneInfesteeForm)
    initializeChoices(`id_zoneinfestee_set-${nextIdToUse}-detections`)
    updatetotalFormsInput()
}

function updatetotalFormsInput(){
    const totalFormsInput = document.getElementById('id_zoneinfestee_set-TOTAL_FORMS')
    totalFormsInput.value = document.querySelectorAll('[id^="zone-infestee-"]').length
}

function removeZoneInfesteeForm(event){
    const zoneElement = document.getElementById(`zone-infestee-${event.target.dataset.pk}`)
    const isNewZone = zoneElement.dataset.newZone  === "true"
    if (isNewZone) {
        zoneElement.remove()
    } else {
        zoneElement.querySelector('[id^="id_zoneinfestee_set-"][id$="DELETE"]').setAttribute("checked", true)
        zoneElement.classList.add("fr-hidden")
    }

    dsfr(event.target.closest("dialog")).modal.conceal()
    updatetotalFormsInput()

    allChoices.forEach((choices) =>{
        if (zoneElement.contains(choices.passedElement.element)){
            allChoices = allChoices.filter(item => item !== choices)
            const selectedValues = choices.getValue(true)
            pickedDetections = pickedDetections.filter(item => !selectedValues.includes(item))
        }
    })
    rebuildChoicesOptions()
}

function enableAllOptions(){
    // Some options are disabled so that the user can't pick the detection twice in different pickers
    // But we need to re-enabled the options because disabled choices are not sent in the form
    // https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#constructing-the-form-data-set
    allChoices.forEach(detectionChoices =>{
        Array.from(detectionChoices.passedElement.element.options).forEach(option => {
            option.disabled = false
        })
    })
}

document.addEventListener('DOMContentLoaded', function() {

    initializeChoices('id_detections_hors_zone');
    initializeAllChoices();
    initializepickedDetections();
    rebuildChoicesOptions();
    const addZoneButton = document.getElementById('add-zone-infestee');
    addZoneButton.addEventListener('click', function(event) {
        event.preventDefault();
        addZoneInfesteeForm();
    });
    document.querySelectorAll("button.delete-zone-infestee").forEach(element => element.addEventListener("click", removeZoneInfesteeForm))

    document.getElementById("save-btn").addEventListener("click", event =>{
        event.preventDefault()
        enableAllOptions()
        document.getElementById("fiche-zone-delimitee-form").submit()
    })
});
