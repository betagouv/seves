document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll(".no-tab-look .fr-tabs__panel").forEach(element =>{
        element.addEventListener('dsfr.conceal', event=>{
            console.log(event)
            document.querySelectorAll('[id^="detection-actions-"]').forEach(actionElement =>{
                actionElement.classList.add("fr-hidden")
            }
            )
        })
    })

});
// TODO gérer le premier affichage
