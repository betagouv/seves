document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('search-form')
    searchForm.addEventListener('reset', function (e) {
        e.preventDefault()
        resetForm(searchForm)
        searchForm.submit()
    });

    document.querySelector(".clear-btn").addEventListener("click", (event)=>{
        event.preventDefault()
        resetForm(document.getElementById("sidebar"))
    })

    document.querySelector(".add-btn").addEventListener("click", (event)=>{
        event.preventDefault()
        event.target.closest(".sidebar").classList.toggle('open');
        document.querySelector('.main-container').classList.toggle('open')
    })

    const sidebarClosingObserver = new MutationObserver((mutations) => {
        mutations.forEach(mutation => {
            if (mutation.type !== "attributes" && mutation.attributeName !== "class") return;
            if (!mutation.target.classList.contains("open")){
                let filledFields = [...document.getElementById("sidebar").querySelectorAll('input, select')]
                filledFields = filledFields.filter(el => el.value.trim() !== '');

                if (filledFields.length === 0){
                    document.getElementById("more-filters-btn-counter").classList.add("fr-hidden")
                } else {
                    document.getElementById("more-filters-btn-counter").innerText = filledFields.length
                    document.getElementById("more-filters-btn-counter").classList.remove("fr-hidden")
                }
            }
        });
    });
    sidebarClosingObserver.observe(document.getElementById("sidebar"), {attributes: true})
});
