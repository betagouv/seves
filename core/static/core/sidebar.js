document.addEventListener('DOMContentLoaded', function () {

    function openSidebar(sidebar) {
        sidebar.classList.add('open');
        document.querySelector('.main-container').classList.add('open');
    }

    function bindClickToSidebar(clicked_element, sidebar){
        clicked_element.addEventListener("click", event => {
            event.preventDefault()
            document.querySelectorAll(".sidebar").forEach(element=>element.classList.remove('open'))
            openSidebar(sidebar);
        })
    }

    function bindAllCloseSidebar(){
        document.querySelectorAll(".close-sidebar").forEach(element => {
            element.addEventListener("click", event => {
                event.preventDefault()
                element.closest(".sidebar").classList.toggle('open');
                document.querySelector('.main-container').classList.toggle('open')
            })
        })
    }

    function openMessageFromUrl() {
        const urlParams = new URLSearchParams(window.location.search);
        const messageId = urlParams.get('message');
        if (messageId) {
            openSidebar(document.getElementById(`sidebar-message-details-${messageId}`));
        }
    }

    document.querySelectorAll(".fil-de-suivi-sidebar").forEach(element => {
        const messageId = element.dataset.messagePk
        bindClickToSidebar(element, document.getElementById(`sidebar-message-details-${messageId}`))
    })
    document.querySelectorAll(".open-sidebar").forEach(element => {
        bindClickToSidebar(element, document.getElementById('sidebar'))
    })
    bindAllCloseSidebar()
    openMessageFromUrl();
})
