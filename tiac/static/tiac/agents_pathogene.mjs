import {applicationReady} from "Application"
import "TreeSelect"
import {Controller} from "Stimulus";
import {patchItems, showHeader, hideHeader, tsDefaultOptions, findPath, shortcutClicked} from "CustomTreeSelect"

class AgentsPathogeneController extends Controller {
    static targets = ["jsonConfig", "categorieDangerInput", "categorieDangerContainer", "categorieDangerHeader"]

    connect() {
        this.setupCategorieDanger()
    }

    onShortcut(event){
        shortcutClicked(event, this.element, this.treeselect, this.categorieDangerInputTarget)
    }

    setupCategorieDanger() {
        const options = JSON.parse(this.jsonConfigTarget.textContent)
        const controller = this
        const treeselect = new Treeselect({
            parentHtmlContainer: this.categorieDangerContainerTarget,
            value: this.categorieDangerInputTarget.value.split("||").map(v => v.trim()),
            options: options,
            isSingleSelect: false,
            isIndependentNodes: true,
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
            if (e.detail.length === 0) {
                this.element.querySelectorAll("[id^='shortcut_']").forEach(checkbox =>{
                    checkbox.checked = false
                })
            } else {
                this.categorieDangerInputTarget.value = e.detail.join("||")
            }
        })
    }
}

applicationReady.then(app => {
    app.register("agents-pathogene", AgentsPathogeneController)
})
