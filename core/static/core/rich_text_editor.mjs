import {applicationReady} from "Application"
import Quill from "Quill"
import {Controller} from "Stimulus"

class RichTextEditorController extends Controller {
    static targets = ["textarea", "container"]
    bgColors = ["#b8fec9", "#ffe9e6", "#0063cb"]
    colors = ["#000091", "#ce0500", "#18753c"]

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
