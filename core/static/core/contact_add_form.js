import choicesDefaults from "choicesDefaults"

document.addEventListener("DOMContentLoaded", function () {
    const options = {
        ...choicesDefaults,
        removeItemButton: true,
        placeholderValue: "Choisir dans la liste",
        searchPlaceholderValue: "Choisir dans la liste",
        noChoicesText: "Aucun contact à sélectionner",
    }

    document.querySelectorAll("#id_contacts_structures, #id_contacts_agents").forEach((el) => {
        el.style.visibility = "visible"
        new Choices(el, options)
    })
})
