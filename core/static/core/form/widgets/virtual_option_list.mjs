import {normalize} from "Utils"

const ROW_HEIGHT = 44
const OVERSCAN = 6
const VIEWPORT_MAX_HEIGHT = 320

/**
 * Renders a large flat list of {id, name} radio/checkbox options as a fixed-size pool of
 * recycled DOM rows instead of one element per item, so mounting and filtering stay cheap
 * regardless of how many items there are.
 */
export class VirtualOptionList {
    #container
    #name
    #inputType
    #onChange
    #allItems = []
    #items = []
    #checked = new Set()
    #pool = []
    #viewport
    #spacer
    #rows

    constructor({container, name, inputType = "radio", onChange}) {
        this.#container = container
        this.#name = name
        this.#inputType = inputType
        this.#onChange = onChange
        this.#buildScaffold()
    }

    setItems(items) {
        this.#allItems = items
        this.#show(items)
    }

    clear() {
        this.#checked.clear()
        this.setItems([])
    }

    /**
     * Mirrors the `search(value, minlength, normalizedNeedle)` contract expected by
     * TreeselectGroup#search so this list can be registered as a pseudo-child and take part
     * in the widget's existing search, despite not being made of individually Stimulus-managed
     * option controllers.
     */
    async search(value, minlength, normalizedNeedle) {
        if (value.length < minlength) {
            this.#show(this.#allItems)
            return true
        }
        const matches = this.#allItems.filter(it => normalize(it.name).includes(normalizedNeedle))
        this.#show(matches)
        return matches.length > 0
    }

    #show(items) {
        this.#items = items
        this.#spacer.style.height = `${items.length * ROW_HEIGHT}px`
        this.#viewport.scrollTop = 0
        this.#render()
    }

    #buildScaffold() {
        this.#container.replaceChildren()

        this.#viewport = document.createElement("div")
        this.#viewport.dataset.testid = "virtual-viewport"
        this.#viewport.style.cssText = `max-height:${VIEWPORT_MAX_HEIGHT}px;overflow-y:auto;position:relative`

        this.#spacer = document.createElement("div")
        this.#spacer.style.position = "relative"

        this.#rows = document.createElement("div")
        this.#rows.style.cssText = "position:absolute;top:0;left:0;right:0"

        this.#spacer.appendChild(this.#rows)
        this.#viewport.appendChild(this.#spacer)
        this.#container.appendChild(this.#viewport)

        const poolSize = Math.ceil(VIEWPORT_MAX_HEIGHT / ROW_HEIGHT) + OVERSCAN * 2
        for (let i = 0; i < poolSize; i++) {
            const row = document.createElement("div")
            row.className = "fr-treeselect__element"
            row.style.cssText = `height:${ROW_HEIGHT}px;box-sizing:border-box;display:flex;align-items:center`
            row.hidden = true

            const group = document.createElement("div")
            group.className = this.#inputType === "checkbox" ? "fr-checkbox-group" : "fr-radio-group"
            group.style.margin = "0"

            const input = document.createElement("input")
            input.type = this.#inputType
            input.name = this.#name

            const label = document.createElement("label")
            label.className = "fr-label"

            group.append(input, label)
            row.appendChild(group)
            this.#rows.appendChild(row)
            this.#pool.push({row, input, label})
        }

        this.#viewport.addEventListener("scroll", () => this.#render(), {passive: true})
        this.#rows.addEventListener("change", e => this.#onRowChange(e))
    }

    #onRowChange(e) {
        const input = e.target
        if (input.type !== this.#inputType) return
        if (input.type === "radio") this.#checked.clear()
        if (input.checked) this.#checked.add(input.value)
        else this.#checked.delete(input.value)
        this.#onChange?.(input)
    }

    #render() {
        const scrollTop = this.#viewport.scrollTop
        const maxStart = Math.max(0, this.#items.length - this.#pool.length)
        const start = Math.min(maxStart, Math.max(0, Math.floor(scrollTop / ROW_HEIGHT) - OVERSCAN))
        this.#rows.style.transform = `translateY(${start * ROW_HEIGHT}px)`

        this.#pool.forEach(({row, input, label}, i) => {
            const item = this.#items[start + i]
            if (!item) {
                row.hidden = true
                return
            }
            row.hidden = false
            const id = `id_${this.#name}_virtual_${start + i}`
            input.id = id
            input.value = item.id
            input.checked = this.#checked.has(String(item.id))
            label.htmlFor = id
            label.textContent = item.name
        })
    }
}
