document.addEventListener('DOMContentLoaded', function() {
    document.getElementById("cancel-link").addEventListener("click", (event) => {
        event.preventDefault();
        window.location = document.referrer;
    });
});
