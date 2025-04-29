let rappelConso = []
document.documentElement.addEventListener('dsfr.ready', () => {
    const rappelPart1Container = document.getElementById("rappel-1")
    const rappelPart2Container = document.getElementById("rappel-2")
    const rappelPart3Container = document.getElementById("rappel-3")
    const rappelContainer = [rappelPart1Container, rappelPart2Container, rappelPart3Container]
    const addRappelConsoBtn = document.getElementById("rappel-submit")
    const submitDraftBtn = document.getElementById("submit_draft")
    const submitPublishBtn = document.getElementById("submit_publish")
    const toNextInput = document.querySelectorAll(".to-next-input")

    function addRappelConso() {
        const numero = `${rappelPart1Container.value}-${rappelPart2Container.value}-${rappelPart3Container.value}`
        rappelConso.push(numero)
        rappelPart1Container.value = null
        rappelPart2Container.value = null
        rappelPart3Container.value = null
        handleDisabledRappelConsoBtn()
    }

    function showRappelConso() {
        const rappelContainer = document.getElementById("rappel-container")
        let innerHtml = ""
        rappelConso.forEach(numero => {
            innerHtml += `<button class="fr-tag fr-mr-2v fr-mb-1w fr-tag--dismiss">${numero}</button>`
        })
        rappelContainer.innerHTML = innerHtml

        rappelContainer.querySelectorAll(".fr-tag--dismiss").forEach(tagElement => {
            tagElement.addEventListener("click", event => {
                event.preventDefault()
                deleteRappelConso(event)
            })
        })
    }

    function deleteRappelConso(event) {
        rappelConso = rappelConso.filter(function (item) {
            return item != event.target.innerText
        })
        showRappelConso()
    }

    function handleDisabledRappelConsoBtn() {
        addRappelConsoBtn.disabled = rappelContainer.some(input => input.value.trim() === '');
    }

    function goToNextIfNeeded(element){
        if (element.value.length == element.maxLength) {
            element.nextElementSibling.focus()
        }
    }

    function addNumeroRappelConsoToHiddenFieldAndSubmit(event) {
        event.preventDefault()
        const form = event.target.closest("form")
        form.reportValidity()

        if (!form.checkValidity()) {
            return
        }
        const values = Array.from(document.querySelectorAll("#rappel-container .fr-tag")).map(e => e.innerText)
        document.getElementById("id_numeros_rappel_conso").value = values.join(",")
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'action';
        input.value = event.target.value
        form.appendChild(input);
        form.submit()
    }

    addRappelConsoBtn.addEventListener("click", event => {
        event.preventDefault()
        for (const input of rappelContainer) {
            if (!input.checkValidity()) {
                input.reportValidity();
                return;
            }
        }
        addRappelConso()
        showRappelConso()
    })

    rappelContainer.forEach(input => input.addEventListener('input', handleDisabledRappelConsoBtn))
    submitDraftBtn.addEventListener("click", addNumeroRappelConsoToHiddenFieldAndSubmit)
    submitPublishBtn.addEventListener("click", addNumeroRappelConsoToHiddenFieldAndSubmit)
    toNextInput.forEach(element => element.addEventListener("keyup", () => goToNextIfNeeded(element)))
})
