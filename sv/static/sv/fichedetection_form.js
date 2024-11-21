function fetchCommunes(query) {
    return fetch(`https://geo.api.gouv.fr/communes?nom=${query}&fields=departement&boost=population&limit=15`)
        .then(response => response.json())
        .then(data => {
            return data.map(item => ({
                value: item.nom,
                label: `${item.nom} (${item.departement.code})` ,
                customProperties: {
                    "departementNom": item.departement.nom,
                    "inseeCode": item.code
                }
            }))
        })
        .catch(error => {
            console.error('Erreur lors de la récupération des données:', error);
            return []
        });
}
function fetchEspecesEchantillon(query) {
    return fetch(`/sv/api/espece/recherche/?q=${query}`)
        .then(response => response.json())
        .then(data => {
            return data.results.map(item => ({
                value: item.id,
                label: item.name ,
            }))
        })
        .catch(error => {
            console.error('Erreur lors de la récupération des données:', error);
            return []
        });
}
function addChoicesEspeceEchantillon(){
    const choicesEspece = new Choices(document.getElementById('espece-echantillon-input'), {
        removeItemButton: true,
        placeholderValue: 'Recherchez...',
        noResultsText: 'Aucun résultat trouvé',
        noChoicesText: 'Aucun résultat trouvé',
        shouldSort: false,
        searchResultLimit: 50,
        classNames: {containerInner: 'fr-select'},
        itemSelectText: '',
    });

    choicesEspece.input.element.addEventListener('input', function (event) {
        const query = choicesEspece.input.element.value
        if (query.length > 2) {
            fetchEspecesEchantillon(query).then(results => {
                choicesEspece.clearChoices()
                choicesEspece.setChoices(results, 'value', 'label', true)
            })
        }
    })
    return choicesEspece
}
document.addEventListener('DOMContentLoaded', function() {
    const statusToNuisibleId =  JSON.parse(document.getElementById('status-to-organisme-nuisible-id').textContent)
    const element = document.getElementById('id_organisme_nuisible');
    const choices = new Choices(element, {
        classNames: {
            containerInner: 'fr-select',
        },
        itemSelectText: ''
    });

    choices.passedElement.element.addEventListener("choice", (event)=> {
        let found = false;
        statusToNuisibleId.forEach((status) =>{
            if (status.nuisibleIds.includes(parseInt(event.detail.choice.value))) {
                document.getElementById('statut-reglementaire-input').value = status.statusID;
                document.getElementById('statut-reglementaire-input').dispatchEvent(new Event('change'));
                found = true;
            }
        })
        if (found === false){
            document.getElementById('statut-reglementaire-input').value="";
            document.getElementById('statut-reglementaire-input').dispatchEvent(new Event('change'));
        }
    })
});

document.addEventListener('alpine:init', () => {
    const MODAL_ADD_EDIT_LIEU = document.getElementById('modal-add-edit-lieu');
    const MODAL_ADD_EDIT_PRELEVEMENT = document.getElementById('modal-add-edit-prelevement');
    const TEMPLATE_LIEU = document.getElementById('lieu-template');

    Alpine.data('app', () => ({

        structuresPreleveurs: JSON.parse(document.getElementById('structures-preleveurs').textContent),
        lieux: [],
        prelevements: [],

        lieuForm: {
            id: '',
            nomLieu: '',
            adresseLieuDit: '',
            commune: '',
            codeINSEE: '',
            departementNom: '',
            region: '',
            coordGPSLambert93Latitude: '',
            coordGPSLambert93Longitude: '',
            coordGPSWGS84Latitude: '',
            coordGPSWGS84Longitude: '',
            isEtablissement: false,
            nomEtablissement: '',
            activiteEtablissement: '',
            paysEtablissement: '',
            raisonSocialeEtablissement: '',
            adresseEtablissement: '',
            siretEtablissement: '',
            codeInuppEtablissement: '',
            siteInspectionId: '',
            positionEtablissementId: '',
        },

		// Données du formulaire d'ajout d'un prélèvement
        formPrelevement: {
            id: null,
            pk: null,
            lieuId: null,
            structurePreleveurId: null,
            numeroEchantillon: null,
            datePrelevement: null,
            matricePreleveeId: null,
            especeEchantillonId: null,
            isOfficiel: false,
            numeroPhytopass: null,
            numeroResytal: null,
            laboratoireAgreeId: null,
            laboratoireConfirmationOfficielleId: null,
            resultat: null,
        },

		// ID du lieu en cours de modification
        lieuIdToEdit: null,

		// Index du prélèvement en cours de modification
        prelevementIdToEdit: null,

		// ID du lieu en cours de suppression
        lieuIdToDelete: null,

		// ID du prélèvement en cours de suppression
        prelevementIdToDelete: null,

        init() {
            MODAL_ADD_EDIT_LIEU.addEventListener('dsfr.conceal', (e) => {
                this.resetLieuAddOrEditFormModal();
                this.lieuIdToEdit = null;
            });

            MODAL_ADD_EDIT_PRELEVEMENT.addEventListener('dsfr.conceal', (e) => {
                this.resetPrelevementAddOrEditFormModal();
                this.prelevementIdToEdit = null;
            });

			// Récupération et initialisation des lieux (si modification d'une fiche de détection existante)
            const lieux = JSON.parse(document.getElementById('lieux-json').textContent);
            if(lieux) {
                this.lieux = lieux.map(lieu => {
                    return {
                        id: lieu.id.toString(),
                        pk: lieu.id,
                        ficheDetectionId: lieu.fiche_detection_id,
                        nomLieu: lieu.nom,
                        adresseLieuDit: lieu.adresse_lieu_dit,
                        commune: lieu.commune,
                        codeINSEE: lieu.code_insee,
                        departementNom: lieu.departement_nom,
                        coordGPSLambert93Latitude: lieu.lambert93_latitude,
                        coordGPSLambert93Longitude: lieu.lambert93_longitude,
                        coordGPSWGS84Latitude: lieu.wgs84_latitude,
                        coordGPSWGS84Longitude: lieu.wgs84_longitude,
                        isEtablissement: lieu.is_etablissement,
                        nomEtablissement: lieu.nom_etablissement,
                        activiteEtablissement: lieu.activite_etablissement,
                        paysEtablissement: lieu.pays_etablissement,
                        raisonSocialeEtablissement: lieu.raison_sociale_etablissement,
                        adresseEtablissement: lieu.adresse_etablissement,
                        siretEtablissement: lieu.siret_etablissement,
                        codeInuppEtablissement: lieu.code_inupp_etablissement,
                        siteInspectionId: lieu.site_inspection_id,
                        positionEtablissementId: lieu.position_chaine_distribution_etablissement_id,
                    };
                });
            }

			// Récupération et initialisation des prélèvements (si modification d'une fiche de détection existante)
            const prelevementsData = JSON.parse(document.getElementById('prelevements').textContent);
            if (prelevementsData) {
                this.prelevements = prelevementsData.map(prelevement => {
                    return {
                        id: prelevement.uuid,
                        pk: prelevement.id,
                        lieuId: prelevement.lieu_id.toString(),
                        structurePreleveurId: prelevement.structure_preleveur_id,
                        numeroEchantillon: prelevement.numero_echantillon,
                        datePrelevement: prelevement.date_prelevement,
                        matricePreleveeId: prelevement.matrice_prelevee_id,
                        especeEchantillonId: prelevement.espece_echantillon_id,
                        especeEchantillonName: prelevement.espece_echantillon_name,
                        isOfficiel: prelevement.is_officiel,
                        numeroPhytopass: prelevement.numero_phytopass,
                        numeroResytal: prelevement.numero_resytal,
                        laboratoireAgreeId: prelevement.laboratoire_agree_id,
                        laboratoireConfirmationOfficielleId: prelevement.laboratoire_confirmation_officielle_id,
                        resultat: prelevement.resultat,
                    };
                });
            }

            const choicesCommunes = new Choices(document.getElementById('commune-select'), {
                removeItemButton: true,
                placeholderValue: 'Recherchez...',
                noResultsText: 'Aucun résultat trouvé',
                noChoicesText: 'Aucun résultat trouvé',
                shouldSort: false,
                searchResultLimit: 10,
                classNames: {containerInner: 'fr-select'},
                itemSelectText: '',
            });

            choicesCommunes.input.element.addEventListener('input', function (event) {
                const query = choicesCommunes.input.element.value
                if (query.length > 2) {
                    fetchCommunes(query).then(results => {
                        choicesCommunes.clearChoices()
                        choicesCommunes.setChoices(results, 'value', 'label', true)
                    })
                }
            })

            choicesCommunes.passedElement.element.addEventListener("choice", (event)=> {
                this.lieuForm.commune = event.detail.choice.value
                this.lieuForm.codeINSEE = event.detail.choice.customProperties.inseeCode
                this.lieuForm.departementNom = event.detail.choice.customProperties.departementNom
            })

            this.choicesCommunes = choicesCommunes

            options = {
                searchResultLimit: 500,
                classNames: {
                    containerInner: 'fr-select',
                },
                removeItemButton: true,
                shouldSort: false,
                itemSelectText: '',
                noResultsText: 'Aucun résultat trouvé',
                noChoicesText: 'Aucune fiche à sélectionner',
                searchFields: ['label'],
            };
            // const freeLinksChoices = new Choices(document.getElementById("free-links"), options);
            // freeLinksChoices.passedElement.element.addEventListener("change", (event)=> {
            //     this.ficheDetection.freeLinksIds = Array.from(freeLinksChoices.getValue(true))
            // })
            // if (!!this.ficheDetection.freeLinksIds) {
            //     this.ficheDetection.freeLinksIds.forEach(value => {
            //         freeLinksChoices.setChoiceByValue(value);
            //     });
            // }

        },

		/**
		 * Affichage du formulaire d'édition d'un lieu
		 * et remplissage des champs avec les données du lieu à modifier
		 * @param {string} lieuId
		 */
        fillLieuEditForm(lieuId) {
            const lieuToEdit = this.lieux.find(lieu => lieu.id === lieuId);
            this.lieuForm = {...lieuToEdit};
            this.lieuIdToEdit = lieuId;
            if (!!this.lieuForm.commune && !!this.lieuForm.departementNom) {
                this.choicesCommunes.setChoices([{ value: this.lieuForm.commune,
                    label: this.lieuForm.commune, selected: true }],'value', 'label', false);
            }
        },

		/**
		 * Ajout ou modification d'un lieu.
		 * Si lieuIdToEdit est null, il s'agit d'un nouveau lieu.
		 * Sinon, met à jour le lieu existant.
		 * @param {string} lieuIdToEdit
		 */
        addOrEditLieu(lieuIdToEdit) {
			// Si le formulaire n'est pas valide, afficher les messages d'erreur
            if (!this.$refs.lieuForm.checkValidity()) {
                this.$refs.lieuForm.reportValidity();
                return;
            }

			// Ajout d'un nouveau lieu
            if (lieuIdToEdit === null) {
                this.lieuForm.id = crypto.randomUUID();
                this.lieux.push({...this.lieuForm});
            }
			// Mise à jour du lieu existant
            else {
                this.lieux = this.lieux.map(lieu =>
                    lieu.id === lieuIdToEdit ? {...this.lieuForm} : lieu
                );
            }
            dsfr(MODAL_ADD_EDIT_LIEU).modal.conceal();
        },

		/**
		 * Réinitialise le formulaire lors de la fermerture de la
		 * modal d'ajout ou de modification d'un lieu
		 */
        resetLieuAddOrEditFormModal() {
			// Réinitialise le formulaire
            this.lieuForm = {
                id: '',
                nomLieu: '',
                adresseLieuDit: '',
                commune: '',
                codeINSEE: '',
                departementNom: '',
                region: '',
                coordGPSLambert93Latitude: '',
                coordGPSLambert93Longitude: '',
                coordGPSWGS84Latitude: '',
                coordGPSWGS84Longitude: '',
                isEtablissement: false,
                nomEtablissement: '',
                activiteEtablissement: '',
                paysEtablissement: '',
                raisonSocialeEtablissement: '',
                adresseEtablissement: '',
                siretEtablissement: '',
                codeInuppEtablissement: '',
                siteInspectionId: '',
                positionEtablissementId: '',

            };
            this.choicesCommunes.clearStore();
        },

		/**
		 * Vérifie si un lieu peut être supprimée.
		 * Si le lieu est liée à un prélèvement, afficher un message d'erreur.
		 * Sinon, afficher la modal de confirmation de suppression.
		 * @param {string} lieuId
		 */
        canDeleteLieu(lieuId) {
			// Vérifier si le lieu est liée à un prélèvement
            let lieuisLinkToAPrelevement = this.prelevements.some(prelevement => prelevement.lieuId === lieuId);

            if (lieuisLinkToAPrelevement) {
				// Si le lieu est liée à un prélèvement, afficher un message d'erreur
                dsfr(document.getElementById('fr-modal-suppression-lieu')).modal.disclose();
                return;
            }

			// Si le lieu n'est pas liée à un prélèvement, afficher la modal de confirmation de suppression
            this.lieuIdToDelete = lieuId;
            dsfr(document.getElementById('fr-modal-cant-delete-lieu')).modal.disclose();
        },

		/**
		 * Supprime un lieu.
		 * @param {string} lieuIdToDelete
		 */
        deleteLieu(lieuIdToDelete) {
            this.lieux = this.lieux.filter(lieu => lieu.id !== lieuIdToDelete);
            dsfr(document.getElementById('fr-modal-cant-delete-lieu')).modal.conceal();
            this.lieuIdToDelete = null;
        },

		/**
		 * Retourne le nom d'un lieu à partir de son ID
		 * @param {string} lieuId
		 * @returns le nom d'un lieu
		 */
        getLieuNameFromId(lieuId) {
			// ⚠️ lieu.id est de type number, lieuId est de type string
            const lieu = this.lieux.find(lieu => lieu.id == lieuId);
            return lieu ? lieu.nomLieu : '';
        },

        addPrelevementForm() {
            choicesEspece = addChoicesEspeceEchantillon()
            choicesEspece.passedElement.element.addEventListener("choice", (event) => {
                this.formPrelevement.especeEchantillonId = event.detail.choice.value
            })
            this.choicesEspece = choicesEspece
            if (!this.formPrelevement.lieuId && this.lieux.length > 0) {
                this.formPrelevement.lieuId = this.lieux[0].id;
            }
        },

		/**
		 * Affiche le formulaire d'édition d'un prélèvement
		 * et rempli les champs avec les données du prélèvement à modifier.
		 * @param {string} prelevementIdToEdit
		 */
        fillPrelevementEditForm(prelevementIdToEdit) {
            const prelevementToEdit = this.prelevements.find(prelevement => prelevement.id === prelevementIdToEdit);
            this.formPrelevement = {...prelevementToEdit};

            this.choicesEspeceEdit = addChoicesEspeceEchantillon()
            this.choicesEspeceEdit.passedElement.element.addEventListener("choice", (event) => {
                this.formPrelevement.especeEchantillonId = event.detail.choice.value
            })
            this.choicesEspeceEdit.setChoices([{
                value: prelevementToEdit.especeEchantillonId,
                label: prelevementToEdit.especeEchantillonName,
                selected: true,
                disabled: false
            }])
            this.prelevementIdToEdit = prelevementIdToEdit;
        },

		/**
		 * Ajout ou modification d'un prélèvement.
		 * Si prelevementIdToEdit est null, il s'agit d'un nouveau prélèvement.
		 * Sinon, met à jour le prélèvement existant.
		 * @param {string} prelevementIdToEdit
		 */
        addOrEditPrelevement(prelevementIdToEdit) {
			// Si le formulaire n'est pas valide, afficher les messages d'erreur
            if(!this.$refs.formPrelevement.checkValidity()) {
                this.$refs.formPrelevement.reportValidity();
                return;
            }

			// Ajout d'un nouveau prélèvement
            if (prelevementIdToEdit === null) {
                this.formPrelevement.id = crypto.randomUUID();
                this.prelevements.push({...this.formPrelevement});
            }
			// Mise à jour du prélèvement existant
            else {
                this.prelevements = this.prelevements.map(prelevement =>
                    prelevement.id === prelevementIdToEdit ? {...this.formPrelevement} : prelevement
                );
            }
            dsfr(MODAL_ADD_EDIT_PRELEVEMENT).modal.conceal();
        },

		/**
		 * Réinitialise le formulaire d'ajout ou de modification d'un prélèvement
		 */
        resetPrelevementAddOrEditFormModal() {
            this.formPrelevement = {
                lieuId: '',
                pk: null,
                structurePreleveurId: '',
                numeroEchantillon: '',
                datePrelevement: '',
                matricePreleveeId: '',
                especeEchantillonId: '',
                isOfficiel: false,
                numeroPhytopass: '',
                numeroResytal: '',
                laboratoireAgreeId: '',
                laboratoireConfirmationOfficielleId: '',
                resultat: '',
            };
            if (this.choicesEspece != undefined) {
                this.choicesEspece.destroy()
            }
            if (this.choicesEspeceEdit != undefined) {
                this.choicesEspeceEdit.destroy()
            }
        },

		/**
		 * Affiche la modal de confirmation de suppression d'un prélèvement
		 * @param {string} prelevementId
		 */
        showDeletePrelevementConfirmationModal(prelevementId) {
            this.prelevementIdToDelete = prelevementId;
            dsfr(document.getElementById('modal-delete-prelevement-confirmation')).modal.disclose();
        },

		/**
		 * Supprime un prélèvement
		 * @param {string} prelevementIdToDelete
		 */
        deletePrelevement(prelevementIdToDelete) {
            this.prelevements = this.prelevements.filter(prelevement => prelevement.id !== prelevementIdToDelete);
            dsfr(document.getElementById('modal-delete-prelevement-confirmation')).modal.conceal();
            this.prelevementIdToDelete = null;
        },

		/**
		 * Retourne le nom d'une structure préleveur à partir de son ID
		 * @param {string} structurePreleveurId
		 * @returns le nom de la structure préleveur
		 */
        getStructurePreleveurNameFromId(structurePreleveurId) {
			// ⚠️ structurePreleveur.id est de type number, structurePreleveurId est de type string
            const structurePreleveur = this.structuresPreleveurs.find(structurePreleveur => structurePreleveur.id == structurePreleveurId);
            return structurePreleveur.nom;
        },

		/**
		 * Retourne la date de prélèvement formatée (jj/mm/aaaa)
		 * @param {string} datePrelevement
		 * @returns la date de prélèvement formatée
		 */
        getDatePrelevementFormated(datePrelevement) {
            return datePrelevement ? new Date(datePrelevement).toLocaleDateString('fr-FR') : '';
        },


    }));

});
