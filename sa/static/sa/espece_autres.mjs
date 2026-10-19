import {applicationReady} from "Application"
import {Controller} from "Stimulus"
import {VirtualOptionList} from "VirtualOptionList"

const OTHER_GROUP_LABEL = "Autres"

const autresEspecesBySource = new Map()

function getAutresEspeces(sourceId) {
    if (!autresEspecesBySource.has(sourceId)) {
        const el = document.getElementById(sourceId)
        autresEspecesBySource.set(sourceId, el ? JSON.parse(el.textContent) : [])
    }
    return autresEspecesBySource.get(sourceId)
}

/**
 * As "Autres" group contains quite a lot of especes, it is only rendered server-side with the selected espece,
 * and is filled with a virtualized list the first time the widget is used.
 * @property {String} nameValue
 * @property {String} sourceValue id of the json_script element containing the "Autres" especes
 */
class EspeceAutresController extends Controller {
    static values = {name: String, source: String}

    #virtualOther = null

    get treeselectElement() {
        return this.element.querySelector('[data-controller~="treeselect"]')
    }

    loadAutres() {
        if (this.#virtualOther) return

        const treeselectElement = this.treeselectElement
        const otherGroup = [...treeselectElement.querySelectorAll(".fr-treeselect__group")].find(
            it => it.querySelector(".fr-treeselect__group-header")?.textContent.trim() === OTHER_GROUP_LABEL,
        )
        const container = otherGroup?.querySelector('[data-testid="group-container"]')
        if (!container) return

        const treeselect = this.application.getControllerForElementAndIdentifier(treeselectElement, "treeselect")
        const checked = [...container.querySelectorAll("input:checked")].map(it => it.value)
        this.#virtualOther = new VirtualOptionList({
            container,
            name: this.nameValue,
            onChange: input => treeselect?.onChange({target: input}),
            treeselectElement,
        })
        this.#virtualOther.setItems(getAutresEspeces(this.sourceValue))
        this.#virtualOther.setChecked(checked)
        this.application
            .getControllerForElementAndIdentifier(otherGroup, "treeselect-group")
            ?.registerChild("virtual-other", this.#virtualOther)
    }
}

applicationReady.then(app => app.register("espece-autres", EspeceAutresController))
