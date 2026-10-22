import {applicationReady} from "Application"
import Quill from "Quill"
import {Controller} from "Stimulus"

class RichTextEditorController extends Controller {
    static targets = ["textarea", "container"]
    static values = {showPlaceholder: Boolean}

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

    getToolbarValues(selector) {
        return Array.from(this.element.querySelectorAll(`${selector} option`))
            .map(option => option.value)
            .filter(Boolean)
    }

    addCustomColorsAsClasses() {
        const Parchment = Quill.import("parchment")

        // Pasted colors are ignored, instead of being turned into invalid class names
        const ColorClass = new Parchment.ClassAttributor("color", this.TEXT_PREFIX, {
            scope: Parchment.Scope.INLINE,
            whitelist: this.getToolbarValues("select.ql-color"),
        })
        Quill.register(ColorClass, true)

        const BackgroundClass = new Parchment.ClassAttributor("background", this.BACKGROUND_PREFIX, {
            scope: Parchment.Scope.INLINE,
            whitelist: this.getToolbarValues("select.ql-background"),
        })
        Quill.register(BackgroundClass, true)
    }

    convertPastedHeadersToSupportedLevel(quill) {
        quill.clipboard.addMatcher("h1, h3, h4, h5, h6", (node, delta) => {
            delta.ops.forEach(op => {
                if (op.attributes?.header) {
                    op.attributes.header = 2
                }
            })
            return delta
        })
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
        const placeholder = this.showPlaceholderValue
            ? "Seront automatiquement ajoutés à votre message : vos nom et prénom, structure, informations principales de l'évènement et le lien vers la fiche Sèves."
            : ""
        this.addCustomColorsAsClasses()
        const quill = new Quill(this.containerTarget, {
            theme: "snow",
            placeholder: placeholder,
            // Only keep the formats available in the toolbar: pasted content (tables, links, quotes...) is converted
            // to what the editor supports instead of being kept as unsupported HTML
            formats: ["header", "bold", "italic", "underline", "strike", "list", "indent", "color", "background"],
            modules: {
                toolbar: "#toolbar",
            },
        })
        this.allowExistingClassesForColors(quill)
        this.convertPastedHeadersToSupportedLevel(quill)
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
