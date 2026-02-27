import {applicationReady} from "Application"
import {BaseDocumentFormset, DOCUMENT_FORM_ID, DOCUMENT_FORMSET_ID, DocumentForm} from "DocumentUploads"

class DocumentFormset extends BaseDocumentFormset {
    onModalClose() {
        super.onModalClose()
        this.formsetContainerTarget.innerHTML = ""
    }
}

applicationReady.then(app => {
    app.register(DOCUMENT_FORM_ID, DocumentForm)
    app.register(DOCUMENT_FORMSET_ID, DocumentFormset)
})
