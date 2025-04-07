function closeDSFRModal(event){
    // Normally using type="button" show be enough to avoid submitting the form and still closing the modal
    // https://github.com/GouvernementFR/dsfr/issues/1040
    const modal =
        dsfr(event.target.closest("dialog")).modal.conceal();
}


function showOrHidePrelevementUI(){
    if (document.getElementById("lieux-list").childElementCount === 0){
        document.getElementById("no-lieux-text").classList.remove("fr-hidden")
        document.getElementById("btn-add-prelevment").disabled = true
    } else {
        document.getElementById("no-lieux-text").classList.add("fr-hidden")
        document.getElementById("btn-add-prelevment").disabled = false
    }
}
