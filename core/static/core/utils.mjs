const collator = new Intl.Collator(navigator.language, {
    usage: "search",
    sensitivity: "base",
})

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

function debounce(func, wait, {leading = false} = {}) {
    let timeout = null

    function cb(...args) {
        func(...args)
        timeout = null
    }

    return (...args) => {
        if (leading === true && timeout == null) {
            return cb(...args)
        }
        clearTimeout(timeout)
        timeout = setTimeout(() => cb(...args), wait)
    }
}

export {search, debounce}
