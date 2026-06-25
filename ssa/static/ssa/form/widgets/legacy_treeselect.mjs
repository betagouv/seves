import {applicationReady} from "Application"
import {addLevel2CategoryIfAllChildrenAreSelected, patchItems, tsDefaultOptions} from "CustomTreeSelect"
import {Controller} from "Stimulus"

/**
 * @property {Object} dataValue
 * @property {HTMLInputElement} inputTarget
 * @property {HTMLElement} treeselectTarget
 */
class LegacyTreeselectController extends Controller {
    static values = {data: Array}
    static targets = ["input", "treeselect"]

    /** @type {?Treeselect} */
    #treeselect = null
    connect() {
        const openCallback = this.patchItems.bind(this)
        this.#treeselect = new Treeselect({
            parentHtmlContainer: this.treeselectTarget,
            value: this.treeselectTarget.dataset.selected.split("||").map(v => v.trim()),
            options: this.dataValue,
            openCallback,
            ...tsDefaultOptions,
        })
        this.element.querySelector(".treeselect-input").classList.add("fr-input")
        this.patchItems()
    }

    patchItems() {
        if (this.#treeselect !== null) {
            patchItems(this.#treeselect.srcElement)
        }
    }

    onInput(e) {
        const values = addLevel2CategoryIfAllChildrenAreSelected(this.dataValue, e.detail)
        this.inputTarget.value = values.join("||")
    }
}

applicationReady.then(app => app.register("legacy-treeselect", LegacyTreeselectController))
