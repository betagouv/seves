(function() {
    let lieux = []
    const MODAL_ADD_EDIT_LIEU = document.getElementById('modal-add-edit-lieu');
    const innerLieuModal = document.querySelector("#modal-add-edit-lieu .fr-modal__content");

    document.querySelector("#add-lieu-bouton").addEventListener("click", function(){
        const templateForm = document.querySelector('#lieu-form-template')
        innerLieuModal.innerHTML = templateForm.innerHTML
    })

    document.querySelector("#lieu-save-btn").addEventListener("click", function(){
        // TODO pour le moment on ne gére que la création pas l'édition de lieu

        lieuForm = {
            nomLieu: innerLieuModal.querySelector("#id_lieux-__prefix__-nom").value,
            adresseLieuDit: innerLieuModal.querySelector("#id_lieux-__prefix__-adresse_lieu_dit").value,
                // commune: '',
                // codeINSEE: '',
                // departementNom: '',
                // region: '',
            siteInspectionId: innerLieuModal.querySelector("#id_lieux-__prefix__-site_inspection").value,
            coordGPSLambert93Latitude: innerLieuModal.querySelector("#id_lieux-__prefix__-lambert93_latitude").value,
            coordGPSLambert93Longitude: innerLieuModal.querySelector("#id_lieux-__prefix__-lambert93_longitude").value,
            coordGPSWGS84Latitude: innerLieuModal.querySelector("#id_lieux-__prefix__-wgs84_longitude").value,
            coordGPSWGS84Longitude: innerLieuModal.querySelector("#id_lieux-__prefix__-wgs84_latitude").value,
            isEtablissement: innerLieuModal.querySelector("#id_lieux-__prefix__-is_etablissement").value,
            nomEtablissement: innerLieuModal.querySelector("#id_lieux-__prefix__-nom_etablissement").value,
            activiteEtablissement: innerLieuModal.querySelector("#id_lieux-__prefix__-activite_etablissement").value,
            paysEtablissement: innerLieuModal.querySelector("#id_lieux-__prefix__-pays_etablissement").value,
            raisonSocialeEtablissement: innerLieuModal.querySelector("#id_lieux-__prefix__-raison_sociale_etablissement").value,
            adresseEtablissement: innerLieuModal.querySelector("#id_lieux-__prefix__-adresse_etablissement").value,
            siretEtablissement: innerLieuModal.querySelector("#id_lieux-__prefix__-siret_etablissement").value,
            codeInuppEtablissement: innerLieuModal.querySelector("#id_lieux-__prefix__-code_inupp_etablissement").value,
            positionEtablissementId: innerLieuModal.querySelector("#id_lieux-__prefix__-position_chaine_distribution_etablissement").value,
        }
        lieuForm.id = crypto.randomUUID();
        lieux.push({...lieuForm});
        dsfr(MODAL_ADD_EDIT_LIEU).modal.conceal();
        // Redessiner toutes les cartes

    })

})();


/*
Au bouton enregistrer sur la modale: mettre à jour la carte

Permettre d'éditer un lieu

Permettre de supprimer un lieu
 */
