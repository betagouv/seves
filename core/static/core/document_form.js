import { validateFileSize } from './document.js';

document.addEventListener('DOMContentLoaded', () => {
    const uploadModal = document.getElementById('fr-modal-add-doc');
    const fileInput = uploadModal.querySelector('input[type="file"]');
    fileInput.addEventListener('change', () => validateFileSize(fileInput));
});
