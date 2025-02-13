document.addEventListener('DOMContentLoaded', function () {

    function bindClickToSidebar(clicked_element, sidebar){
        clicked_element.addEventListener("click", event => {
            event.preventDefault()
            document.querySelectorAll(".sidebar").forEach(element=>element.classList.remove('open'))
            sidebar.classList.add('open');
            document.querySelector('.main-container').classList.add('open')
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
    document.querySelectorAll(".fil-de-suivi-sidebar").forEach(element => {
        const messageId = element.dataset.messagePk
        bindClickToSidebar(element, document.getElementById(`sidebar-message-details-${messageId}`))
    })
    document.querySelectorAll(".message-panel").forEach(element => {
        bindClickToSidebar(element, document.getElementById('sidebar'))
    })
    bindAllCloseSidebar()
})
