import {applicationReady} from "Application"
import Quill from "Quill"
import {Controller} from "Stimulus"

class RichTextEditorController extends Controller {
    static targets = ["textarea", "container"]
    bgColors = [
        "var(--yellow-tournesol-925-125)",
        "var(--green-emeraude-950-100)",
        "var(--green-archipel-950-100)",
        "var(--pink-macaron-925-125)",
        "var(--purple-glycine-925-125)",
        "var(--blue-ecume-925-125)",
    ]
    colors = [
        "var(--grey-925-125)",
        "var(--blue-france-sun-113-625)",
        "var(--blue-france-main-525)",
        "var(--success-425-625)",
        "var(--purple-glycine-main-494)",
        "var(--error-425-625)",
    ]

    connect() {
        const quill = new Quill(this.containerTarget, {
            theme: "snow",
            modules: {
                toolbar: [
                    [{header: [2, false]}],
                    ["bold", "italic", "underline", "strike", {list: "bullet"}],
                    [{indent: "-1"}, {indent: "+1"}],
                    [{color: this.colors}, {background: this.bgColors}],
                ],
            },
        })

        quill.on("text-change", () => {
            this.textareaTarget.value = quill.root.innerHTML
        })
    }
}

applicationReady.then(app => {
    app.register("rich-text-editor", RichTextEditorController)
})
