let rappelConso = []
document.documentElement.addEventListener('dsfr.ready', () => {
    const rappelPart1Container = document.getElementById("rappel-1")
    const rappelPart2Container = document.getElementById("rappel-2")
    const rappelPart3Container = document.getElementById("rappel-3")
    const rappelContainer = [rappelPart1Container, rappelPart2Container, rappelPart3Container]
    const addRappelConsoBtn = document.getElementById("rappel-submit")
    const submitDraftBtn = document.getElementById("submit_draft")
    const submitPublishBtn = document.getElementById("submit_publish")

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

    function disableSourceOptions(typeEvenementInput, sourceInput) {
        const isHumanCase = typeEvenementInput.value === "investigation_cas_humain";
        sourceInput.querySelectorAll('option').forEach(option => {
            if (option.value !== "autre") {
                option.disabled = (option.getAttribute('data-for-human-case') === 'true') !== isHumanCase;
            }
        });
        sourceInput.selectedIndex = 0;
    }

    function getNextIdToUse() {
        let num = 0
        while (document.getElementById(`id_etablissements-${num}-raison_sociale`)) {
            num++
        }
        return num
    }


    function showEtablissementModal() {
        const nextIdToUse = getNextIdToUse()

        let template = document.getElementById('etablissement-template').innerHTML
        template = template.replace(/__prefix__/g, nextIdToUse.toString())
        document.getElementById("main-form").insertAdjacentHTML('beforeend', template)

        const modal = document.getElementById("fr-modal-etablissement" + nextIdToUse.toString())
        modal.querySelector('[id$=raison_sociale]').required = true
        setTimeout(() => {
            dsfr(modal).modal.disclose()
            dsfr(modal).modal.node.addEventListener('dsfr.conceal', event => {
                removeRequired(modal)
                const originalTarget = event.explicitOriginalTarget
                if (!originalTarget.classList.contains("save-btn")) {
                    resetForm(modal)
                }
            });
        }, 10)

        modal.querySelector("[id^=etablissement-save-btn-]").addEventListener("click", event => {
            event.preventDefault()
            submitFormAndAddEtablissementCard(event)
        })
    }

    function getSelectedLabel(element) {
        if (!element.value) {
            return null
        }
        return element.options[element.selectedIndex].innerText;
    }

    function submitFormAndAddEtablissementCard(event) {
        const currentModal = event.target.closest("dialog")
        if (formIsValid(currentModal) === false) {
            return
        }

        const clone = document.getElementById('etablissement-card-template').content.cloneNode(true);
        clone.querySelector('.raison-sociale').textContent = currentModal.querySelector('[id$=raison_sociale]').value

        const typeExploitant = getSelectedLabel(currentModal.querySelector('[id$=type_exploitant]'))
        if (typeExploitant != null) {
            clone.querySelector('.type-exploitant').innerText = typeExploitant
            clone.querySelector('.type-exploitant').classList.remove("fr-hidden")
        }

        const pays = getSelectedLabel(currentModal.querySelector('[id$=pays]'))
        if (pays != null) {
            clone.querySelector('.pays').innerText = pays
            clone.querySelector('.pays').classList.remove("fr-hidden")
        }

        const structure = `Département : ${currentModal.querySelector('[id$=departement]').value || 'nc.'}`
        clone.querySelector('.structure').textContent = structure

        const numeroAgrement = `N° d'agrément : ${currentModal.querySelector('[id$=numero_agrement]').value || 'nc.'}`
        clone.querySelector('.numero-agrement').textContent = numeroAgrement

        const positionDossierInput = currentModal.querySelector('[id$=position_dossier]')
        const positionDossier = getSelectedLabel(positionDossierInput)
        if (positionDossier != null) {
            clone.querySelector('.position-dossier').innerText = positionDossier
            clone.querySelector('.position-dossier').classList.remove("fr-hidden")
            const extraClass = positionDossierInput.options[positionDossierInput.selectedIndex].dataset.extraClass
            clone.querySelector('.position-dossier').classList.add(extraClass)
        }

        document.getElementById("etablissement-card-container").appendChild(clone);
        dsfr(currentModal).modal.conceal()
        removeRequired(currentModal)
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

    const typeEvenementInput = document.getElementById('id_type_evenement')
    const sourceInput = document.getElementById('id_source')
    typeEvenementInput.addEventListener("change", event => {
        disableSourceOptions(typeEvenementInput, sourceInput)
    })
    disableSourceOptions(typeEvenementInput, sourceInput)

    document.getElementById('add-etablissement').addEventListener("click", event => {
        event.preventDefault()
        showEtablissementModal()
    })
});
