# TODO est ce que cela a du sens : test_cannot_update_evenement_visibilite_by_other_structures
# def test_cannot_update_evenement_visibilite_by_other_structures(live_server, page: Page, mocked_authentification_user):
#     evenement=  EvenementFactory()
#     mocked_authentification_user.agent.structure = baker.make(Structure)
#     mocked_authentification_user.agent.save()
#
#     page.goto(f"{live_server.url}{fiche_zone.get_absolute_url()}")
#     page.get_by_role("button", name="Actions").click()
#     expect(page.get_by_text("Modifier la visibilité")).not_to_be_visible()

# def test_agent_in_structure_createur_can_update_fiche_zone_delimitee_visibilite_brouillon(
#
#     """Test qu'un agent appartenant à la structure créatrice d'une fiche
# ne peut pas modifier la visibilité de cette fiche si elle est en visibilité local ou national"""
#
#     """Test qu'un agent appartenant à l'AC peut modifier la visibilité d'une fiche de local à national"""
#     """Test qu'un agent appartenant à l'AC peut modifier la visibilité d'une fiche de national à local"""
#
#
# test_fiche_zone_delimitee_brouillon_cannot_change_visibility_through_actions_btn
