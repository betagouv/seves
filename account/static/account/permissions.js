document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("cancel-link").addEventListener("click", event => {
        event.preventDefault()
        window.location = document.referrer
    })
})
