from importmap import static

importmaps = {
    "Stimulus": "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.2.2/dist/stimulus.js",
    "StimulusStore": "https://cdn.jsdelivr.net/npm/stimulus-store@0.0.3/dist/bundle.esm.js",
    "Choices": "https://cdn.jsdelivr.net/npm/choices.js@11.0.4/public/assets/scripts/choices.mjs",
    "Application": static("core/stimulus_app.mjs"),
    "choicesDefaults": static("core/choices.mjs"),
    "BaseFormset": static("core/base_formset.mjs"),
    "BaseFormInModal": static("core/base_form_in_modal.mjs"),
    "dsfr": static("dsfr/dist/dsfr.module.min.js"),
    "BanAutocomplete": static("core/ban_autocomplete.js"),
    "Forms": static("core/forms.mjs"),
    "ViewManager": static("core/view_manager.js"),
    "CustomTreeSelect": static("ssa/_custom_tree_select.js"),
    "siret": static("core/siret.mjs"),
}
