document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".rappel-conso-link").forEach(rappel => {
        fetch(
            `https://data.economie.gouv.fr/api/records/1.0/search/?dataset=rappelconso-v2-gtin-espaces&refine.numero_fiche=${rappel.innerText}`,
            {
                headers: {Accept: "application/json"},
            },
        )
            .then(response => response.json())
            .then(data => {
                if (data.nhits === 1) {
                    const link = document.createElement("a")
                    link.href = `https://rappel.conso.gouv.fr/fiche-rappel/${data.records[0].fields.id}/Interne`
                    link.className = "fr-link"
                    link.target = "_blank"
                    link.rel = "noopener noreferrer"
                    link.textContent = rappel.innerText
                    rappel.replaceChildren(link)
                }
            })
    })
})
