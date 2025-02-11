document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll(".btn--close-js").forEach(element => element.addEventListener("click", event =>{
        event.preventDefault()
        const alert = event.target.parentNode;
        alert.parentNode.removeChild(alert)
    }))})

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll(".btn--close-notice-js").forEach(element => element.addEventListener("click", event =>{
        event.preventDefault()
        const notice = event.target.parentNode.parentNode.parentNode;
        notice.parentNode.removeChild(notice)
    }))})
