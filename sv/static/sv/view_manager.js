export class ViewManager {
    #config;
    #elements = {};

    constructor(config) {
        this.#validateConfig(config);
        this.#config = { ...config };
    }

    #validateConfig(config) {
        const requiredFields = ['storageKeyPrefix', 'modes', 'selectors'];
        requiredFields.forEach(field => {
            if (!config[field]) {
                throw new Error(`Missing required config field: ${field}`);
            }
        });
    }

    #getFicheId() {
        return this.#elements.ficheContainer.dataset.ficheId;
    }

    #getElements() {
        this.#elements = {
            detailBtn: document.getElementById(this.#config.selectors.DETAIL_BTN),
            syntheseBtn: document.getElementById(this.#config.selectors.SYNTHESE_BTN),
            detailContent: document.getElementById(this.#config.selectors.DETAIL_CONTENT),
            ficheContainer: document.querySelector('[data-fiche-id]')
        };
    }

    #getStorageKey(id) {
        return `${this.#config.storageKeyPrefix}_${id}`;
    }

    #save(mode, id) {
        localStorage.setItem(this.#getStorageKey(id), mode);
    }

    #get(id) {
        return localStorage.getItem(this.#getStorageKey(id));
    }

    #toggleView(mode) {
        this.#save(mode, this.#getFicheId());
        this.#elements.detailContent.classList.toggle('fr-hidden', mode === this.#config.modes.SYNTHESE);
    }

    #initViewState() {
        const savedViewMode = this.#get(this.#getFicheId());
        const isSynthese = savedViewMode === this.#config.modes.SYNTHESE;

        this.#elements.detailBtn.checked = !isSynthese;
        this.#elements.syntheseBtn.checked = isSynthese;
        this.#elements.detailContent.classList.toggle('fr-hidden', isSynthese);
    }

    #initViewModeButtons() {
        this.#elements.detailBtn.addEventListener('change', this.#handleViewToggle);
        this.#elements.syntheseBtn.addEventListener('change', this.#handleViewToggle);
    }

    #handleViewToggle = (event) => {
        this.#toggleView(event.target.value);
    }

    initialize() {
        this.#getElements();
        if(!this.#elements.detailBtn && !this.#elements.syntheseBtn){
            return
        }
        this.#initViewState();
        this.#initViewModeButtons();
    }
}

export const evenementViewModeConfig = {
    storageKeyPrefix: 'evenementViewMode',
    modes: {
        DETAIL: 'detail',
        SYNTHESE: 'synthese'
    },
    selectors: {
        DETAIL_BTN: 'detail-btn',
        SYNTHESE_BTN: 'synthese-btn',
        DETAIL_CONTENT: 'detail-content'
    }
};
