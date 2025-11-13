import {Controller} from "Stimulus";
import {applicationReady} from "Application";
import {resetForm} from "Forms"
import choicesDefaults from "choicesDefaults"
import {patchItems, tsDefaultOptions, showHeader, addLevel2CategoryIfAllChildrenAreSelected, shortcutClicked, addCategoryHeader} from "CustomTreeSelect"


class SearchFormController extends Controller {
    static targets = ["agent_contact", "structure_contact", "sidebar", "counter", "dangerSyndromique", "with_free_links", "numero",
        "jsonConfig",
        "categorieProduitInput",
        "categorieProduitContainer",
        "jsonConfigAnalyse",
        "categorieDangerAnalyseInput",
        "categorieDangerAnalyseContainer",
        "categorieDangerHeader",
        "agentsPathogenesInput",
        "agentsPathogenesContainer",
        "agentsPathogenesHeader",
        "jsonConfigSelectedHazard",
        "selectedHazardInput",
        "selectedHazardContainer",
    ]

    onReset(){
        resetForm(this.element)
        this.choicesAgentContact.setChoiceByValue('');
        this.choicesStructureContact.setChoiceByValue('');
        this.treeselectSelectedHazard.updateValue()
        this.element.submit()
    }

    onSidebarClear(){
        resetForm(this.sidebarTarget)
        this.dangerSyndromique.removeActiveItems();
        this.treeselectAgentsPathogenes.updateValue()
        this.treeselectDanger.updateValue()
        this.treeselectCategorieProduit.updateValue()
    }

    onSidebarAdd() {
        const inputs = this.sidebarTarget.querySelectorAll('input, textarea, select');
        let isValid = true;
        inputs.forEach(input => {
            if (!input.checkValidity()) {
                input.reportValidity();
                isValid = false;
            }
        });
        if (isValid){
            this.sidebarTarget.classList.toggle('open');
            document.querySelector('.main-container').classList.toggle('open')
        }
    }

    disableCheckboxIfNeeded(){
        this.with_free_linksTarget.disabled = !this.numeroTarget.value
    }

    updateFilterCounter(){
        let filledFields = [...this.sidebarTarget.querySelectorAll('input, select')]
        filledFields = filledFields.filter(el => el.value.trim() !== '');

        if (filledFields.length === 0){
            this.counterTarget.classList.add("fr-hidden")
        } else {
            this.counterTarget.innerText = filledFields.length
            this.counterTarget.classList.remove("fr-hidden")
        }
    }
    treeselectOpenCallback() {
        patchItems(this.treeselectDanger.srcElement)
        if (this.customHeaderAddedValue) {
            showHeader(this.treeselectDanger.srcElement, ".categorie-danger-header")
            return;
        }
        const list = this.categorieDangerAnalyseContainerTarget.querySelector(".treeselect-list")
        if (list) {
            const fragment = this.categorieDangerHeaderTarget.content.cloneNode(true);
            fragment.querySelectorAll("[for^='shortcut_']").forEach(label =>{
                if (this.treeselectDanger.value.includes(label.innerText)){
                    fragment.querySelector(`[id='${label.getAttribute('for')}']`).checked = true
                }
            })
            list.prepend(fragment);
            this.customHeaderAddedValue = true
        }
    }

    treeselectOpenCallbackAgentsPathogenes() {
        patchItems(this.treeselectAgentsPathogenes.srcElement)
        if (this.customHeaderAddedValueAgentsPathogeneValue) {
            showHeader(this.treeselectAgentsPathogenes.srcElement, ".categorie-danger-header")
            return;
        }
        const list = this.agentsPathogenesContainerTarget.querySelector(".treeselect-list")
        if (list) {
            const fragment = this.agentsPathogenesHeaderTarget.content.cloneNode(true);
            fragment.querySelectorAll("[for^='shortcut_']").forEach(label =>{
                if (this.treeselectAgentsPathogenes.value.includes(label.innerText)){
                    fragment.querySelector(`[id='${label.getAttribute('for')}']`).checked = true
                }
            })
            list.prepend(fragment);
            this.customHeaderAddedValueAgentsPathogeneValue = true
        }
    }

    setupCategorieDanger() {
        const options = JSON.parse(this.jsonConfigAnalyseTarget.textContent)
        this.treeselectDanger = new Treeselect({
            ...tsDefaultOptions,
            parentHtmlContainer: this.categorieDangerAnalyseContainerTarget,
            value: this.categorieDangerAnalyseInputTarget.value.split("||").map(v => v.trim()),
            options: options,
            isSingleSelect: false,
            openCallback: this.treeselectOpenCallback.bind(this),
            placeholder: "Chercher ou choisir dans la liste",
            searchCallback: item => {
                if (item.length === 0) {
                    showHeader(this.treeselectDanger.srcElement, ".categorie-danger-header")
                } else {
                    hideHeader(this.treeselectDanger.srcElement, ".categorie-danger-header")
                }
            },
        })
        this.treeselectDanger.srcElement.addEventListener("update-dom", () => {
            patchItems(this.treeselectDanger.srcElement)
        })
        this.treeselectDanger.srcElement.addEventListener('input', (e) => {
            if (e.detail.length === 0) {
                this.element.querySelectorAll("[id^='shortcut_']").forEach(checkbox =>{
                    checkbox.checked = false
                })
            } else {
                this.categorieDangerAnalyseInputTarget.value = e.detail.join("||")
            }
        })
        this.treeselectDanger.srcElement.querySelector(".treeselect-input").classList.add("fr-input")
    }

    setupAgentsPathogenes() {
        const options = JSON.parse(this.jsonConfigAnalyseTarget.textContent)
        this.treeselectAgentsPathogenes = new Treeselect({
            ...tsDefaultOptions,
            parentHtmlContainer: this.agentsPathogenesContainerTarget,
            value: this.agentsPathogenesInputTarget.value.split("||").map(v => v.trim()),
            options: options,
            isSingleSelect: false,
            openCallback: this.treeselectOpenCallbackAgentsPathogenes.bind(this),
            placeholder: "Chercher ou choisir dans la liste",
            searchCallback: item => {
                if (item.length === 0) {
                    showHeader(this.treeselectAgentsPathogenes.srcElement, ".categorie-danger-header")
                } else {
                    hideHeader(this.treeselectAgentsPathogenes.srcElement, ".categorie-danger-header")
                }
            },
        })
        this.treeselectAgentsPathogenes.srcElement.addEventListener("update-dom", () => {
            patchItems(this.treeselectAgentsPathogenes.srcElement)
        })
        this.treeselectAgentsPathogenes.srcElement.addEventListener('input', (e) => {
            if (e.detail.length === 0) {
                this.element.querySelectorAll("[id^='shortcut_']").forEach(checkbox =>{
                    checkbox.checked = false
                })
            } else {
                this.agentsPathogenesInputTarget.value = e.detail.join("||")
            }
        })
        this.treeselectAgentsPathogenes.srcElement.querySelector(".treeselect-input").classList.add("fr-input")
    }

    onShortcut(event){
        shortcutClicked(event, this.treeselectDanger, this.categorieDangerAnalyseInputTarget)
    }

    onShortcutAgentsPathogenes(event){
        shortcutClicked(event, this.treeselectAgentsPathogenes, this.agentsPathogenesInputTarget)
    }


    setupCategorieProduit(){
        const options = JSON.parse(this.jsonConfigTarget.textContent)
        const selectedValues = this.categorieProduitInputTarget.value.split("||").map(v => v.trim())
        const treeselectCategorieProduit = new Treeselect({
            parentHtmlContainer: this.categorieProduitContainerTarget,
            value: selectedValues,
            options: options,
            isSingleSelect: false,
            openCallback() {
                patchItems(treeselectCategorieProduit.srcElement)
            },
            ...tsDefaultOptions
        })
        this.treeselectCategorieProduit = treeselectCategorieProduit
        patchItems(this.treeselectCategorieProduit.srcElement)
        this.treeselectCategorieProduit.srcElement.addEventListener("update-dom", ()=>{patchItems(this.treeselectCategorieProduit.srcElement)})
        this.categorieProduitContainerTarget.querySelector(".treeselect-input").classList.add("fr-input")

        this.treeselectCategorieProduit.srcElement.addEventListener('input', (e) => {
            if (!e.detail) return
            const values = addLevel2CategoryIfAllChildrenAreSelected(options, e.detail)
            this.categorieProduitInputTarget.value = values.join("||")
        })
    }

    setupSelectedHazard(){
        const options = JSON.parse(this.jsonConfigSelectedHazardTarget.textContent)
        const selectedValues = this.selectedHazardInputTarget.value.split("||").map(v => v.trim())
        const treeselectSelectedHazard = new Treeselect({
            parentHtmlContainer: this.selectedHazardContainerTarget,
            value: selectedValues,
            options: options,
            isSingleSelect: false,
            openCallback() {
                patchItems(treeselectSelectedHazard.srcElement)
                addCategoryHeader(treeselectSelectedHazard.srcElement, "Dangers syndromiques", 0)
                addCategoryHeader(treeselectSelectedHazard.srcElement, "Liste complète des dangers alimentaires", 11)
                treeselectSelectedHazard.srcElement.dataset.headerAdded = "true"
            },
            ...tsDefaultOptions
        })
        this.treeselectSelectedHazard = treeselectSelectedHazard
        patchItems(this.treeselectSelectedHazard.srcElement)
        this.treeselectSelectedHazard.srcElement.addEventListener("update-dom", ()=>{patchItems(this.treeselectSelectedHazard.srcElement)})
        this.selectedHazardContainerTarget.querySelector(".treeselect-input").classList.add("fr-input")

        this.treeselectSelectedHazard.srcElement.addEventListener('input', (e) => {
            if (!e.detail) return
            const values = addLevel2CategoryIfAllChildrenAreSelected(options, e.detail)
            this.selectedHazardInputTarget.value = values.join("||")
        })
    }


    connect(){
        this.choicesAgentContact = new Choices(this.agent_contactTarget, choicesDefaults)
        this.choicesStructureContact = new Choices(this.structure_contactTarget, choicesDefaults)
        this.dangerSyndromique = new Choices(this.dangerSyndromiqueTarget, choicesDefaults)
        this.disableCheckboxIfNeeded()
        this.setupSelectedHazard()
        this.setupCategorieProduit()
        this.setupCategorieDanger()
        this.setupAgentsPathogenes()

        this.updateFilterCounter()

        const sidebarClosingObserver = new MutationObserver((mutations) => {
            mutations.forEach(mutation => {
                if (mutation.type !== "attributes" && mutation.attributeName !== "class") return;
                if (!mutation.target.classList.contains("open")){
                    this.updateFilterCounter()
                }
            });
        });
        sidebarClosingObserver.observe(this.sidebarTarget, {attributes: true})
    }
}

applicationReady.then(app => {
    app.register("search-form", SearchFormController)
})
