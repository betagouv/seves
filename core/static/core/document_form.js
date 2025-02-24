import { validateFileSize } from './document.js';

document.addEventListener('DOMContentLoaded', () => {
    const uploadModal = document.getElementById('fr-modal-add-doc');
    if (!!uploadModal){
        const fileInput = uploadModal.querySelector('input[type="file"]');
        fileInput.addEventListener('change', () => validateFileSize(fileInput));
    }
});
