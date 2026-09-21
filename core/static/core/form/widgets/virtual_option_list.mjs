import {normalize} from "Utils"

const ROW_HEIGHT = 44
const OVERSCAN = 6
const VIEWPORT_MAX_HEIGHT = 320
const PAGE_SIZE = Math.max(1, Math.floor(VIEWPORT_MAX_HEIGHT / ROW_HEIGHT))

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
    #allItems = [] // full unfiltered list
    #items = [] // currently displayed (post-search) list
    #checked = new Set()
    #pool = [] // fixed-size recycled DOM rows, reused regardless of item count
    #viewport // scrollable container
    #spacer // full-height element sized to the length of the items, so the scrollbar reflects the real list size
    #rows // absolutely-positioned window (translated to the current scroll offset)
    #status
    #pinnedContainer // stores the selected items, regardless of their presence/absence in the DOM
    #pinned = new Map() // value -> {input, label}
    #currentStart = 0 // index of the first item currently rendered in the #pool
    #focusedIndex = null // logical focused item index (independent of DOM recycling)

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
        this.#focusedIndex = null
        this.#spacer.style.height = `${items.length * ROW_HEIGHT}px`
        this.#viewport.scrollTop = 0
        this.#render()
        this.#status.textContent = `${items.length} espèce${items.length > 1 ? "s" : ""}`
    }

    #buildScaffold() {
        this.#container.replaceChildren()

        this.#status = document.createElement("div")
        this.#status.className = "fr-sr-only"
        this.#status.setAttribute("aria-live", "polite")
        this.#container.appendChild(this.#status)

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

        this.#pinnedContainer = document.createElement("div")
        this.#pinnedContainer.hidden = true
        this.#container.appendChild(this.#pinnedContainer)

        const poolSize = PAGE_SIZE + OVERSCAN * 2
        for (let i = 0; i < poolSize; i++) {
            const row = document.createElement("div")
            row.className = "fr-treeselect__element"
            row.style.cssText = `height:${ROW_HEIGHT}px;box-sizing:border-box;align-items:center;display:none`

            const group = document.createElement("div")
            group.className = this.#inputType === "checkbox" ? "fr-checkbox-group" : "fr-radio-group"
            group.style.margin = "0"

            const input = document.createElement("input")
            input.type = this.#inputType
            input.name = this.#name
            input.addEventListener("change", e => this.#onRowChange(e))

            const label = document.createElement("label")
            label.className = "fr-label"

            group.append(input, label)
            row.appendChild(group)
            this.#rows.appendChild(row)
            this.#pool.push({row, input, label})
        }

        this.#viewport.addEventListener("scroll", () => this.#render(), {passive: true})
        this.#rows.addEventListener("focusin", e => this.#onFocusIn(e))
        this.#rows.addEventListener("keydown", e => this.#onKeyDown(e))
    }

    #onRowChange(e) {
        const input = e.target
        if (input.type !== this.#inputType) return
        if (input.type === "radio") this.#checked.clear()
        if (input.checked) this.#checked.add(input.value)
        else this.#checked.delete(input.value)
        this.#onChange?.(input)
    }

    #onFocusIn(e) {
        const i = this.#pool.findIndex(({input}) => input === e.target)
        if (i === -1) return
        this.#focusedIndex = this.#currentStart + i
    }

    #onKeyDown(e) {
        if (!this.#pool.some(({input}) => input === e.target)) return

        const current = this.#focusedIndex ?? this.#currentStart
        let target
        if (e.key === "ArrowDown") target = current + 1
        else if (e.key === "ArrowUp") target = current - 1
        else if (e.key === "PageDown") target = current + PAGE_SIZE
        else if (e.key === "PageUp") target = current - PAGE_SIZE
        else if (e.key === "Home") target = 0
        else if (e.key === "End") target = this.#items.length - 1
        else return

        // Out of range (let the browser handle this natively)
        if (target < 0 || target > this.#items.length - 1) {
            return
        }
        e.preventDefault()
        this.#focusIndex(target)
    }

    #focusIndex(index) {
        if (this.#items.length === 0) return
        const clamped = Math.max(0, Math.min(this.#items.length - 1, index))
        this.#scrollIndexIntoView(clamped)
        this.#render()

        const slot = this.#pool[clamped - this.#currentStart]
        if (!slot) return
        slot.input.focus({preventScroll: true})
        this.#focusedIndex = clamped

        if (this.#inputType === "radio" && !slot.input.checked) {
            slot.input.checked = true
            this.#checked.clear()
            this.#checked.add(slot.input.value)
            this.#onChange?.(slot.input)
        }
    }

    #scrollIndexIntoView(index) {
        const rowTop = index * ROW_HEIGHT
        const rowBottom = rowTop + ROW_HEIGHT
        const viewTop = this.#viewport.scrollTop
        const viewBottom = viewTop + this.#viewport.clientHeight
        if (rowTop < viewTop) {
            this.#viewport.scrollTop = rowTop
        } else if (rowBottom > viewBottom) {
            this.#viewport.scrollTop = rowBottom - this.#viewport.clientHeight
        }
    }

    #render() {
        const scrollTop = this.#viewport.scrollTop
        const maxStart = Math.max(0, this.#items.length - this.#pool.length)
        const start = Math.min(maxStart, Math.max(0, Math.floor(scrollTop / ROW_HEIGHT) - OVERSCAN))
        this.#currentStart = start
        this.#rows.style.transform = `translateY(${start * ROW_HEIGHT}px)`

        const mounted = new Set()
        this.#pool.forEach(({row, input, label}, i) => {
            const item = this.#items[start + i]
            if (!item) {
                row.hidden = true
                row.style.display = "none"
                return
            }
            row.hidden = false
            row.style.display = "flex"
            const id = `id_${this.#name}_virtual_${start + i}`
            const value = String(item.id)
            input.id = id
            input.value = value
            const checked = this.#checked.has(value)
            input.checked = checked
            if (checked) mounted.add(value)
            input.setAttribute("aria-setsize", String(this.#items.length))
            input.setAttribute("aria-posinset", String(start + i + 1))
            label.htmlFor = id
            label.textContent = item.name
        })
        this.#syncPinned(mounted)
    }

    #syncPinned(mounted) {
        for (const [value, {input, label}] of this.#pinned) {
            if (!this.#checked.has(value) || mounted.has(value)) {
                input.remove()
                label.remove()
                this.#pinned.delete(value)
            }
        }
        for (const value of this.#checked) {
            if (mounted.has(value) || this.#pinned.has(value)) continue
            const input = document.createElement("input")
            input.type = this.#inputType
            input.name = this.#name
            input.value = value
            const id = `id_${this.#name}_pinned_${value}`
            input.id = id
            input.addEventListener("change", e => this.#onRowChange(e))
            const label = document.createElement("label")
            label.htmlFor = id
            label.textContent = this.#allItems.find(it => String(it.id) === value)?.name ?? ""

            this.#pinnedContainer.append(input, label)
            this.#pinned.set(value, {input, label})
            input.checked = true
        }
    }
}
