/**
 * Strips case and diacritics so strings can be compared with a plain substring search.
 */
function normalize(value) {
    return value
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase()
}

const uniqueId = (() => {
    const counters = new Map()
    return prefix => {
        if (!counters.has(prefix)) {
            counters.set(prefix, 0)
        }
        counters.set(prefix, counters.get(prefix) + 1)
        return `${prefix}-${counters.get(prefix)}`
    }
})()

export {normalize, uniqueId}
