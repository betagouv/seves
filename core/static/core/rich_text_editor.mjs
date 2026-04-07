import {applicationReady} from "Application"
import Quill from "Quill"
import {Controller} from "Stimulus"

class RichTextEditorController extends Controller {
    static targets = ["textarea", "container"]

    TEXT_PREFIX = "text-color"
    BACKGROUND_PREFIX = "background-color"

    allowExistingClassesForColors(quill) {
        quill.clipboard.addMatcher("SPAN", (node, delta) => {
            node.classList.forEach(cls => {
                if (cls.startsWith(this.TEXT_PREFIX)) {
                    delta.ops.forEach(op => {
                        if (op.insert) {
                            op.attributes = op.attributes || {}
                            op.attributes.color = cls.replace(`${this.TEXT_PREFIX}-`, "")
                        }
                    })
                }
            })
            return delta
        })

        quill.clipboard.addMatcher("SPAN", (node, delta) => {
            node.classList.forEach(cls => {
                if (cls.startsWith(this.BACKGROUND_PREFIX)) {
                    delta.ops.forEach(op => {
                        if (op.insert) {
                            op.attributes = op.attributes || {}
                            op.attributes.background = cls.replace(`${this.BACKGROUND_PREFIX}-`, "")
                        }
                    })
                }
            })
            return delta
        })
    }

    addCustomColorsAsClasses() {
        const Parchment = Quill.import("parchment")

        const ColorClass = new Parchment.ClassAttributor("color", this.TEXT_PREFIX, {
            scope: Parchment.Scope.INLINE,
        })
        Quill.register(ColorClass, true)

        const BackgroundClass = new Parchment.ClassAttributor("background", this.BACKGROUND_PREFIX, {
            scope: Parchment.Scope.INLINE,
        })
        Quill.register(BackgroundClass, true)
    }

    setBackgroundColorForPickers() {
        this.element.querySelectorAll(".ql-picker-item").forEach(el => {
            const value = el.dataset.value

            if (value) {
                el.style.backgroundColor = "var(--" + value + ")"
            }
        })
    }

    connect() {
        const quill = new Quill(this.containerTarget, {
            theme: "snow",
            modules: {
                toolbar: "#toolbar",
            },
        })
        this.addCustomColorsAsClasses()
        this.allowExistingClassesForColors(quill)
        this.setBackgroundColorForPickers()

        quill.clipboard.dangerouslyPasteHTML(this.textareaTarget.value)
        quill.on("text-change", () => {
            this.textareaTarget.value = quill.root.innerHTML
        })
    }
}

applicationReady.then(app => {
    app.register("rich-text-editor", RichTextEditorController)
})
