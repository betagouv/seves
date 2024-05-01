document.addEventListener('DOMContentLoaded', function() {
    const element = document.getElementById('organisme-nuisible-input');
    const choices = new Choices(element, {
        classNames: {
            containerInner: 'fr-select',
        }
    });
});

document.addEventListener('alpine:init', () => {

    const MODAL_ADD_EDIT_LOCALISATION = document.getElementById('modal-add-edit-localisation');
    const MODAL_ADD_EDIT_PRELEVEMENT = document.getElementById('modal-add-edit-prelevement');

    Alpine.data('app', () => ({

		// Données de référence pour les listes déroulantes
        departements: JSON.parse(document.getElementById('departements').textContent),
        unites: JSON.parse(document.getElementById('unites').textContent),
        statutsEvenement: JSON.parse(document.getElementById('statuts-evenement').textContent),
        organismesNuisibles: JSON.parse(document.getElementById('organismes-nuisibles').textContent),
        statutsReglementaires: JSON.parse(document.getElementById('statuts-reglementaires').textContent),
        contextes: JSON.parse(document.getElementById('contextes').textContent),
        structuresPreleveurs: JSON.parse(document.getElementById('structures-preleveurs').textContent),
        sitesInspections: JSON.parse(document.getElementById('sites-inspections').textContent),
        matricesPrelevees: JSON.parse(document.getElementById('matrices-prelevees').textContent),
        especesEchantillon: JSON.parse(document.getElementById('especes-echantillon').textContent),
        laboratoiresAgrees: JSON.parse(document.getElementById('laboratoires-agrees').textContent),
        laboratoiresConfirmationOfficielle: JSON.parse(document.getElementById('laboratoires-confirmation-officielle').textContent),

		// Données du formulaire de la fiche détection (champs fiche détection et listes des localisations et prélèvements)
        ficheDetection: {
            numero: '',
            createurId: '',
            statutEvenementId: '',
            organismeNuisibleId: '',
            statutReglementaireId: '',
            contexteId: '',
            datePremierSignalement: '',
            commentaire: '',
            mesuresConservatoiresImmediates: '',
            mesuresConsignation: '',
            mesuresPhytosanitaires: '',
            mesuresSurveillanceSpecifique: '',
        },

        localisations: [
			//{ id: '0c5bed5c-9f3f-4e0d-83b8-e52e89b9eb09', nomLocalisation: 'Localisation 1', adresseLieuDit: 'Adresse 1', commune: 'Commune 1', codeINSEE: '12345', departementId: '1', coordGPSLambert93Latitude: '6000000', coordGPSLambert93Longitude: '200000', coordGPSWGS84Latitude: '0', coordGPSWGS84Longitude: '0' },
			//{ id: 'e16e5305-76c0-4758-a0c7-e6674cff5086', nomLocalisation: 'Localisation 2', adresseLieuDit: 'Adresse 2', commune: 'Commune 2', codeINSEE: '54321', departementId: '2', coordGPSLambert93Latitude: '6000000', coordGPSLambert93Longitude: '200000', coordGPSWGS84Latitude: '0', coordGPSWGS84Longitude: '0' },
			//{ id: 'b5492275-a960-477a-aeca-af50932ca21e', nomLocalisation: 'Localisation 3', adresseLieuDit: 'Adresse 3', commune: 'Commune 3', codeINSEE: '54321', departementId: '3', coordGPSLambert93Latitude: '6000000', coordGPSLambert93Longitude: '200000', coordGPSWGS84Latitude: '0', coordGPSWGS84Longitude: '0' },
        ],

        prelevements: [
			/*{
				id: crypto.randomUUID(),
				nom: 'Prélèvement 1',
				localisationId: '0c5bed5c-9f3f-4e0d-83b8-e52e89b9eb09',
				isOfficiel: true,
				datePrelevement: '2021-09-01',
				structurePreleveurId: '1',
				siteInspectionId: '1',
			},
			*/
        ],

		// Données du formulaire d'ajout d'une localisation
        localisationForm: {
            id: '',
            nomLocalisation: '',
            adresseLieuDit: '',
            commune: '',
            codeINSEE: '',
            departementId: '',
            region: '',
            coordGPSLambert93Latitude: '',
            coordGPSLambert93Longitude: '',
            coordGPSWGS84Latitude: '',
            coordGPSWGS84Longitude: '',
        },

		// Données du formulaire d'ajout d'un prélèvement
        formPrelevement: {
            id: null,
            pk: null,
            localisationId: null,
            structurePreleveurId: null,
            numeroEchantillon: null,
            datePrelevement: null,
            siteInspectionId: null,
            matricePreleveeId: null,
            especeEchantillonId: null,
            isOfficiel: false,
            numeroPhytopass: null,
            laboratoireAgreeId: null,
            laboratoireConfirmationOfficielleId: null,
        },

		// ID de la localisation en cours de modification
        localisationIdToEdit: null,

		// Index du prélèvement en cours de modification
        prelevementIdToEdit: null,

		// ID de la localisation en cours de suppression
        localisationIdToDelete: null,

		// ID du prélèvement en cours de suppression
        prelevementIdToDelete: null,

        init() {
            MODAL_ADD_EDIT_LOCALISATION.addEventListener('dsfr.conceal', (e) => {
                this.resetLocalisationAddOrEditFormModal();
                this.localisationIdToEdit = null;
            });

            MODAL_ADD_EDIT_PRELEVEMENT.addEventListener('dsfr.conceal', (e) => {
                this.resetPrelevementAddOrEditFormModal();
                this.prelevementIdToEdit = null;
            });

            this.ficheDetection = {
                numero: this.getValueById('numeroFiche'),
                createurId: this.getValueById('createur-id'),
                statutEvenementId: this.getValueById('statut-evenement-id'),
                organismeNuisibleId: this.getValueById('organisme-nuisible-id'),
                statutReglementaireId: this.getValueById('statut-reglementaire-id'),
                contexteId: this.getValueById('contexte-id'),
                datePremierSignalement: this.getValueById('date-premier-signalement'),
                commentaire: this.getValueById('commentaire'),
                mesuresConservatoiresImmediates: this.getValueById('mesures-conservatoires-immediates'),
                mesuresConsignation: this.getValueById('mesures-consignation'),
                mesuresPhytosanitaires: this.getValueById('mesures-phytosanitaires'),
                mesuresSurveillanceSpecifique: this.getValueById('mesures-surveillance-specifique')
            };

			// Récupération et initialisation des localisations (si modification d'une fiche de détection existante)
            const lieux = JSON.parse(document.getElementById('lieux').textContent);
            if(lieux) {
                this.localisations = lieux.map(lieu => {
                    return {
                        id: lieu.id.toString(),
                        pk: lieu.id,
                        ficheDetectionId: lieu.fiche_detection_id,
                        nomLocalisation: lieu.nom,
                        adresseLieuDit: lieu.adresse_lieu_dit,
                        commune: lieu.commune,
                        codeINSEE: lieu.code_insee,
                        departementId: lieu.departement_id,
                        coordGPSLambert93Latitude: lieu.coordGPSLambert93Latitude,
                        coordGPSLambert93Longitude: lieu.coordGPSLambert93Longitude,
                        coordGPSWGS84Latitude: lieu.wgs84_latitude,
                        coordGPSWGS84Longitude: lieu.wgs84_longitude,
                    };
                });
            }

			// Récupération et initialisation des prélèvements (si modification d'une fiche de détection existante)
            const prelevementsData = JSON.parse(document.getElementById('prelevements').textContent);
            if (prelevementsData) {
                this.prelevements = this.mapPrelevements(prelevementsData);
            }
        },

        getValueById(id) {
            const element = document.getElementById(id);
            return element ? element.value : null;
        },

        mapPrelevements(prelevementsData) {
            return prelevementsData.map(prelevement => {
                return {
                    id: prelevement.uuid,
                    pk: prelevement.id,
                    localisationId: prelevement.lieu_id.toString(),
                    structurePreleveurId: prelevement.structure_preleveur_id,
                    numeroEchantillon: prelevement.numero_echantillon,
                    datePrelevement: prelevement.date_prelevement,
                    siteInspectionId: prelevement.site_inspection_id,
                    matricePreleveeId: prelevement.matrice_prelevee_id,
                    especeEchantillonId: prelevement.espece_echantillon_id,
                    isOfficiel: prelevement.isOfficiel,
                    numeroPhytopass: prelevement.numero_phytopass,
                    laboratoireAgreeId: prelevement.laboratoire_agree_id,
                    laboratoireConfirmationOfficielleId: prelevement.laboratoire_confirmation_officielle_id,
                };
            });
        },

        getNumeroIfExist() {
            const numero = document.getElementById('fiche-detection-numero');
            return numero ? numero.textContent : '';
        },

		/**
		 * Affichage du formulaire d'édition d'une localisation
		 * et remplissage des champs avec les données de la localisation à modifier
		 * @param {string} localisationId
		 */
        fillLocalisationEditForm(localisationId) {
            const localisationToEdit = this.localisations.find(localisation => localisation.id === localisationId);
            this.localisationForm = {...localisationToEdit};
            this.localisationIdToEdit = localisationId;
        },

		/**
		 * Ajout ou modification d'une localisation.
		 * Si localisationIdToEdit est null, il s'agit d'une nouvelle localisation.
		 * Sinon, met à jour la localisation existante.
		 * @param {string} localisationIdToEdit
		 */
        addOrEditLocalisation(localisationIdToEdit) {
			// Si le formulaire n'est pas valide, afficher les messages d'erreur
            if (!this.$refs.localisationForm.checkValidity()) {
                this.$refs.localisationForm.reportValidity();
                return;
            }

			// Ajout d'une nouvelle localisation
            if (localisationIdToEdit === null) {
                this.localisationForm.id = crypto.randomUUID();
                this.localisations.push({...this.localisationForm});
            }
			// Mise à jour de la localisation existante
            else {
                this.localisations = this.localisations.map(localisation =>
                    localisation.id === localisationIdToEdit ? {...this.localisationForm} : localisation
                );
            }
            dsfr(MODAL_ADD_EDIT_LOCALISATION).modal.conceal();
        },

		/**
		 * Réinitialise le formulaire lors de la fermerture de la
		 * modal d'ajout ou de modification d'une localisation
		 */
        resetLocalisationAddOrEditFormModal() {
			// Réinitialise le formulaire
            this.localisationForm = {
                id: '',
                nomLocalisation: '',
                adresseLieuDit: '',
                commune: '',
                codeINSEE: '',
                departementId: '',
                region: '',
                coordGPSLambert93Latitude: '',
                coordGPSLambert93Longitude: '',
                coordGPSWGS84Latitude: '',
                coordGPSWGS84Longitude: '',
            };
        },

		/**
		 * Vérifie si une localisation peut être supprimée.
		 * Si la localisation est liée à un prélèvement, afficher un message d'erreur.
		 * Sinon, afficher la modal de confirmation de suppression.
		 * @param {string} localisationId
		 */
        canDeleteLocalisation(localisationId) {
			// Vérifier si la localisation est liée à un prélèvement
            let localisationisLinkToAPrelevement = this.prelevements.some(prelevement => prelevement.localisationId === localisationId);

            if (localisationisLinkToAPrelevement) {
				// Si la localisation est liée à un prélèvement, afficher un message d'erreur
                dsfr(document.getElementById('fr-modal-suppression-localisation')).modal.disclose();
                return;
            }

			// Si la localisation n'est pas liée à un prélèvement, afficher la modal de confirmation de suppression
            this.localisationIdToDelete = localisationId;
            dsfr(document.getElementById('fr-modal-cant-delete-localisation')).modal.disclose();
        },

		/**
		 * Supprime une localisation.
		 * @param {string} localisationIdToDelete
		 */
        deleteLocalisation(localisationIdToDelete) {
            this.localisations = this.localisations.filter(localisation => localisation.id !== localisationIdToDelete);
            dsfr(document.getElementById('fr-modal-cant-delete-localisation')).modal.conceal();
            this.localisationIdToDelete = null;
        },

		/**
		 * Retourne le nom d'une localisation à partir de son ID
		 * @param {string} localisationId
		 * @returns le nom de la localisation
		 */
        getLocalisationNameFromId(localisationId) {
			// ⚠️ localisation.id est de type number, localisationId est de type string
            const localisation = this.localisations.find(localisation => localisation.id == localisationId);
            return localisation ? localisation.nomLocalisation : '';
        },

		/**
		 * Selectionne la première localisation de la liste
		 * avant d'afficher le formulaire d'ajout d'un prélèvement
		 */
        addPrelevementForm() {

            if (!this.formPrelevement.localisationId && this.localisations.length > 0) {
                this.formPrelevement.localisationId = this.localisations[0].id;
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
                localisationId: '',
                pk: null,
                structurePreleveurId: '',
                numeroEchantillon: '',
                datePrelevement: '',
                siteInspectionId: '',
                matricePreleveeId: '',
                especeEchantillonId: '',
                isOfficiel: false,
                numeroPhytopass: '',
                laboratoireAgreeId: '',
                laboratoireConfirmationOfficielleId: '',
            };
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
		 * Retourne le nom d'un site d'inspection à partir de son ID
		 * @param {string} siteInspectionId
		 * @returns le nom du site d'inspection
		 */
        getSiteInspectionNameFromId(siteInspectionId) {
			// ⚠️ siteInspection.id est de type number, siteInspectionId est de type string
            const siteInspection = this.sitesInspections.find(siteInspection => siteInspection.id == siteInspectionId);
            return siteInspection ? siteInspection.nom : '';
        },

		/**
		 * Retourne la date de prélèvement formatée (jj/mm/aaaa)
		 * @param {string} datePrelevement
		 * @returns la date de prélèvement formatée
		 */
        getDatePrelevementFormated(datePrelevement) {
            return datePrelevement ? new Date(datePrelevement).toLocaleDateString('fr-FR') : '';
        },

        saveFicheDetection() {
            if(!this.$refs.fichedetectionForm.checkValidity()) {
                this.$refs.fichedetectionForm.reportValidity();
                return;
            }

            let formData = new FormData();
            formData.append('createurId', this.ficheDetection.createurId);
            formData.append('statutEvenementId', this.ficheDetection.statutEvenementId);
            formData.append('organismeNuisibleId', this.ficheDetection.organismeNuisibleId.value ? this.ficheDetection.organismeNuisibleId.value : '');
            formData.append('statutReglementaireId', this.ficheDetection.statutReglementaireId);
            formData.append('contexteId', this.ficheDetection.contexteId);
            formData.append('datePremierSignalement', this.ficheDetection.datePremierSignalement);
            formData.append('commentaire', this.ficheDetection.commentaire);
            formData.append('mesuresConservatoiresImmediates', this.ficheDetection.mesuresConservatoiresImmediates);
            formData.append('mesuresConsignation', this.ficheDetection.mesuresConsignation);
            formData.append('mesuresPhytosanitaires', this.ficheDetection.mesuresPhytosanitaires);
            formData.append('mesuresSurveillanceSpecifique', this.ficheDetection.mesuresSurveillanceSpecifique);
            formData.append('localisations', JSON.stringify(this.localisations));
            formData.append('prelevements', JSON.stringify(this.prelevements));

            const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
            const url = document.getElementById('fiche-detection-form-url').dataset.url;

            fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken,
                },
            })
                .then(response => {
                    if (!response.ok) {
                        response.text().then(errorText => {
                            console.log(errorText);
                        });
                    }
                    window.location.href = response.url;
                })
                .catch(error => {
                    console.error(error);
                });
        },

    }));

});
