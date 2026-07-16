import choicesDefaults from "choicesDefaults"

document.addEventListener("DOMContentLoaded", () => {
    new Choices(document.getElementById("id_quantification_unite"), {
        ...choicesDefaults,
        position: "bottom",
    })
})
