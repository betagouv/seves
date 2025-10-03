import {applicationReady} from "Application"
import "TreeSelect"
import {Controller} from "Stimulus";
import {patchItems, showHeader, hideHeader, tsDefaultOptions, findPath} from "CustomTreeSelect"

class AgentsPathogeneController extends Controller {
    static targets = ["jsonConfig", "categorieDangerInput", "categorieDangerContainer", "categorieDangerHeader"]

    connect() {
        this.setupCategorieDanger()
    }

    onShortcut(event){
        const label = event.target.getElementsByTagName("label")[0]
        const value = label.textContent.trim()
        const checkbox = this.element.querySelector('[id$=' + label.getAttribute("for") + ']')
        checkbox.checked = !checkbox.checked

        let valuesToSet = this.treeselect.value
        if (checkbox.checked){
            valuesToSet.push(value)
        } else {
            valuesToSet.pop(value)
        }

        this.treeselect.updateValue(valuesToSet)
        this.categorieDangerInputTarget.value = valuesToSet.join("||")
        let text = ""
        if (valuesToSet.length === 1){
            text = valuesToSet[0]
        } else {
            text = `${valuesToSet.length} ${this.treeselect.tagsCountText}`
        }
        this.element.querySelector(".treeselect-input__tags-count").innerText = text
    }

    setupCategorieDanger() {
        const options = JSON.parse(this.jsonConfigTarget.textContent)
        const controller = this
        const treeselect = new Treeselect({
            parentHtmlContainer: this.categorieDangerContainerTarget,
            value: this.categorieDangerInputTarget.value.split("||").map(v => v.trim()),
            options: options,
            isSingleSelect: false,
            openCallback() {
                patchItems(treeselect.srcElement)
                if (this._customHeaderAdded) {
                    showHeader(treeselect.srcElement, ".categorie-danger-header")
                    return;
                }
                const list = controller.element.querySelector(".treeselect-list")
                if (list) {
                    const fragment = controller.categorieDangerHeaderTarget.content.cloneNode(true);
                    list.prepend(fragment);
                    this._customHeaderAdded = true
                }
            },
            searchCallback(item) {
                if (item.length === 0) {
                    showHeader(treeselect.srcElement, ".categorie-danger-header")
                } else {
                    hideHeader(treeselect.srcElement, ".categorie-danger-header")
                }
            },
            ...tsDefaultOptions,
        })
        this.treeselect = treeselect
        this.element.querySelector(".treeselect-input").classList.add("fr-input")
        treeselect.srcElement.addEventListener("update-dom", () => {
            patchItems(treeselect.srcElement)
        })
        treeselect.srcElement.addEventListener('input', (e) => {
            if (!!e.detail) {
                this.categorieDangerInputTarget.value = e.detail.join("||")
            }
        })
    }
}

applicationReady.then(app => {
    app.register("agents-pathogene", AgentsPathogeneController)
})
