const collator = (() => {
    const options = {
        usage: "search",
        sensitivity: "base",
    }
    try {
        return new Intl.Collator(navigator.language, options)
    } catch (_) {
        return new Intl.Collator("fr", options)
    }
})()

/**
 * Searches needle in haystack
 * Inspired by https://github.com/idmadj/locale-includes/blob/master/src/index.js
 *
 * @param {String} haystack
 * @param {String} needle
 * @return {boolean}
 */
function search(haystack, needle) {
    const haystackLength = haystack.length
    const needleLength = needle.length
    const lengthDiff = haystackLength - needleLength

    if (lengthDiff < 0) return false

    for (let i = 0; i <= lengthDiff; i++) {
        const subHaystack = haystack.substring(i, i + needleLength)
        if (collator.compare(subHaystack, needle) === 0) {
            return true
        }
    }
    return false
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

export {search, uniqueId}
