document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".rappel-conso-link").forEach((rappel) => {
        fetch(
            `https://data.economie.gouv.fr/api/records/1.0/search/?dataset=rappelconso-v2-gtin-espaces&refine.numero_fiche=${rappel.innerText}`,
            {
                headers: { Accept: "application/json" },
            },
        )
            .then((response) => response.json())
            .then((data) => {
                if (data["nhits"] === 1) {
                    const element = `<a href="https://rappel.conso.gouv.fr/fiche-rappel/${data["records"][0]["fields"]["id"]}/Interne" class="fr-link" target="_blank">${rappel.innerText}</a>`
                    rappel.innerHTML = element
                }
            })
    })
})
