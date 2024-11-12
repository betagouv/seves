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
    const element = document.getElementById('organisme-nuisible-input');
    const choices = new Choices(element, {
        classNames: {
            containerInner: 'fr-select',
        },
        itemSelectText: ''
    });

    choices.passedElement.element.addEventListener("choice", (event)=> {
        statusToNuisibleId.forEach((line) =>{
            if (line.nuisibleIds.includes(parseInt(event.detail.choice.value)))
            {
                document.getElementById('statut-reglementaire-input').value=line.statusID
                document.getElementById('statut-reglementaire-input').dispatchEvent(new Event('change'));
            }
        })

    })
});

document.addEventListener('alpine:init', () => {

    const MODAL_ADD_EDIT_LIEU = document.getElementById('modal-add-edit-lieu');
    const MODAL_ADD_EDIT_PRELEVEMENT = document.getElementById('modal-add-edit-prelevement');

    Alpine.data('app', () => ({

        structuresPreleveurs: JSON.parse(document.getElementById('structures-preleveurs').textContent),
        sitesInspections: JSON.parse(document.getElementById('sites-inspections').textContent),

		// Données du formulaire de la fiche détection (champs fiche détection et listes des lieux et prélèvements)
        ficheDetection: {
            numero: '',
            statutEvenementId: '',
            numeroRasff: '',
            numeroEurophyt: '',
            organismeNuisibleId: '',
            freeLinksIds: '',
            statutReglementaireId: '',
            contexteId: '',
            datePremierSignalement: '',
            commentaire: '',
            vegetauxInfestes: '',
            mesuresConservatoiresImmediates: '',
            mesuresConsignation: '',
            mesuresPhytosanitaires: '',
            mesuresSurveillanceSpecifique: '',
        },

        lieux: [
			//{ id: '0c5bed5c-9f3f-4e0d-83b8-e52e89b9eb09', nomLieu: 'Lieu 1', adresseLieuDit: 'Adresse 1', commune: 'Commune 1', codeINSEE: '12345', departementId: '1', coordGPSLambert93Latitude: '6000000', coordGPSLambert93Longitude: '200000', coordGPSWGS84Latitude: '0', coordGPSWGS84Longitude: '0' },
			//{ id: 'e16e5305-76c0-4758-a0c7-e6674cff5086', nomLieu: 'Lieu 2', adresseLieuDit: 'Adresse 2', commune: 'Commune 2', codeINSEE: '54321', departementId: '2', coordGPSLambert93Latitude: '6000000', coordGPSLambert93Longitude: '200000', coordGPSWGS84Latitude: '0', coordGPSWGS84Longitude: '0' },
			//{ id: 'b5492275-a960-477a-aeca-af50932ca21e', nomLieu: 'Lieu 3', adresseLieuDit: 'Adresse 3', commune: 'Commune 3', codeINSEE: '54321', departementId: '3', coordGPSLambert93Latitude: '6000000', coordGPSLambert93Longitude: '200000', coordGPSWGS84Latitude: '0', coordGPSWGS84Longitude: '0' },
        ],

        prelevements: [
			/*{
				id: crypto.randomUUID(),
				nom: 'Prélèvement 1',
				lieuId: '0c5bed5c-9f3f-4e0d-83b8-e52e89b9eb09',
				isOfficiel: true,
				datePrelevement: '2021-09-01',
				structurePreleveurId: '1',
				siteInspectionId: '1',
			},
			*/
        ],

		// Données du formulaire d'ajout d'un lieu
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
            codeInppEtablissement: '',
            typeEtablissementId: '',
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
            siteInspectionId: null,
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

            this.ficheDetection = {
                numero: this.getValueById('numeroFiche'),
                numeroEurophyt: this.getValueById('numeroEurophyt'),
                numeroRasff: this.getValueById('numeroRasff'),
                statutEvenementId: this.getValueById('statut-evenement-id'),
                organismeNuisibleId: this.getValueById('organisme-nuisible-id'),
                statutReglementaireId: this.getValueById('statut-reglementaire-id'),
                freeLinksIds: JSON.parse(document.getElementById('free-links-id').textContent),
                contexteId: this.getValueById('contexte-id'),
                datePremierSignalement: this.getValueById('date-premier-signalement'),
                commentaire: this.getValueById('commentaire'),
                vegetauxInfestes: this.getValueById('vegetaux-infestes'),
                mesuresConservatoiresImmediates: this.getValueById('mesures-conservatoires-immediates'),
                mesuresConsignation: this.getValueById('mesures-consignation'),
                mesuresPhytosanitaires: this.getValueById('mesures-phytosanitaires'),
                mesuresSurveillanceSpecifique: this.getValueById('mesures-surveillance-specifique')
            };
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
                        codeInppEtablissement: lieu.code_inpp_etablissement,
                        typeEtablissementId: lieu.type_exploitant_etablissement_id,
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
                        siteInspectionId: prelevement.site_inspection_id,
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
                itemSelectText: '',
                noResultsText: 'Aucun résultat trouvé',
                noChoicesText: 'Aucune fiche à sélectionner',
                searchFields: ['label'],
            };
            const freeLinksChoices = new Choices(document.getElementById("free-links"), options);
            freeLinksChoices.passedElement.element.addEventListener("change", (event)=> {
                this.ficheDetection.freeLinksIds = Array.from(freeLinksChoices.getValue(true))
            })
            if (!!this.ficheDetection.freeLinksIds) {
                this.ficheDetection.freeLinksIds.forEach(value => {
                  freeLinksChoices.setChoiceByValue(value);
                });
            }

        },

        getValueById(id) {
            const element = document.getElementById(id);
            return element ? element.value : null;
        },

        getNumeroIfExist() {
            const numero = document.getElementById('fiche-detection-numero');
            return numero ? numero.textContent : '';
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
                codeInppEtablissement: '',
                typeEtablissementId: '',
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
                siteInspectionId: '',
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

        saveFicheDetection(event) {
            if(!this.$refs.fichedetectionForm.checkValidity()) {
                this.$refs.fichedetectionForm.reportValidity();
                return;
            }

            const boutonClique = event.submitter;
            const action = boutonClique.dataset.action;

            let formData = new FormData();
            const organismeNuisibleId = this.ficheDetection.organismeNuisibleId.value ? this.ficheDetection.organismeNuisibleId.value : this.ficheDetection.organismeNuisibleId
            formData.append('statutEvenementId', this.ficheDetection.statutEvenementId);
            formData.append('numeroRasff', this.ficheDetection.numeroRasff);
            formData.append('numeroEurophyt', this.ficheDetection.numeroEurophyt);
            formData.append('organismeNuisibleId', organismeNuisibleId);
            formData.append('statutReglementaireId', this.ficheDetection.statutReglementaireId);
            formData.append('contexteId', this.ficheDetection.contexteId);
            formData.append('datePremierSignalement', this.ficheDetection.datePremierSignalement);
            formData.append('commentaire', this.ficheDetection.commentaire);
            formData.append('vegetauxInfestes', this.ficheDetection.vegetauxInfestes);
            formData.append('mesuresConservatoiresImmediates', this.ficheDetection.mesuresConservatoiresImmediates);
            formData.append('mesuresConsignation', this.ficheDetection.mesuresConsignation);
            formData.append('mesuresPhytosanitaires', this.ficheDetection.mesuresPhytosanitaires);
            formData.append('mesuresSurveillanceSpecifique', this.ficheDetection.mesuresSurveillanceSpecifique);
            formData.append('lieux', JSON.stringify(this.lieux));
            formData.append('prelevements', JSON.stringify(this.prelevements));
            formData.append('action', action);
            for (var i = 0; i < this.ficheDetection.freeLinksIds.length; i++) {
              formData.append('freeLinksIds', this.ficheDetection.freeLinksIds[i]);
            }

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
