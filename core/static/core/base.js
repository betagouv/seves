document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".btn--close-js").forEach(element =>
        element.addEventListener("click", event => {
            event.preventDefault()
            const alert = event.target.parentNode
            alert.parentNode.removeChild(alert)
        }),
    )
})

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".btn--close-notice-js").forEach(element =>
        element.addEventListener("click", event => {
            event.preventDefault()
            const notice = event.target.parentNode.parentNode.parentNode
            notice.parentNode.removeChild(notice)
        }),
    )
})

document.addEventListener("DOMContentLoaded", () => {
    const blockingErrorModal = document.getElementById("fr-modal-blocking-error")
    if (blockingErrorModal) {
        setTimeout(() => {
            dsfr(blockingErrorModal).modal.disclose()
            blockingErrorModal.addEventListener("dsfr.conceal", () => {
                window.location = window.location.href
            })
        }, 1000)
    }
})

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".dismissible-notice-js").forEach(notice => {
        const storageKey = notice.dataset.storageKey
        try {
            if (localStorage.getItem(storageKey)) return notice.remove()
        } catch {}
        notice.classList.remove("fr-hidden")
        notice.querySelector(".fr-btn--close").addEventListener("click", () => {
            try {
                localStorage.setItem(storageKey, new Date().toISOString())
            } catch {}
            notice.remove()
        })
    })
})
