from importmap import static

importmaps = {
    "Stimulus": "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.2.2/dist/stimulus.js",
    "StimulusStore": "https://cdn.jsdelivr.net/npm/stimulus-store@0.0.3/dist/bundle.esm.js",
    "Choices": "https://cdn.jsdelivr.net/npm/choices.js@11.0.4/public/assets/scripts/choices.mjs",
    "Application": static("core/stimulus_app.mjs"),
}
