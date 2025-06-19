import pytest

from core.factories import DocumentFactory, MessageFactory, ContactStructureFactory
from sv.factories import (
    EvenementFactory,
    FicheDetectionFactory,
    PrelevementFactory,
    FicheZoneFactory,
    ZoneInfesteeFactory,
    LieuFactory,
)

BASE_NUM_QUERIES = 22  # Please note a first call is made without assertion to warm up any possible cache


@pytest.mark.django_db
def test_empty_evenement_performances(client, django_assert_num_queries):
    evenement = EvenementFactory()
    client.get(evenement.get_absolute_url())

    with django_assert_num_queries(BASE_NUM_QUERIES):
        client.get(evenement.get_absolute_url())


@pytest.mark.django_db
def test_evenement_performances_with_messages_from_same_user(
    client, django_assert_num_queries, mocked_authentification_user
):
    evenement = EvenementFactory()
    client.get(evenement.get_absolute_url())

    sender = mocked_authentification_user.agent.contact_set.get()
    MessageFactory(content_object=evenement, sender=sender, recipients=[], recipients_copy=[])

    with django_assert_num_queries(BASE_NUM_QUERIES + 4):
        client.get(evenement.get_absolute_url())

    MessageFactory.create_batch(3, content_object=evenement, sender=sender, recipients=[], recipients_copy=[])

    with django_assert_num_queries(BASE_NUM_QUERIES + 7):
        response = client.get(evenement.get_absolute_url())

    assert len(response.context["message_list"]) == 4


@pytest.mark.django_db
def test_evenement_performances_with_multiple_messages_with_documents(
    client, django_assert_max_num_queries, mocked_authentification_user
):
    evenement = EvenementFactory()
    client.get(evenement.get_absolute_url())

    MessageFactory(content_object=evenement)
    with django_assert_max_num_queries(BASE_NUM_QUERIES + 14):
        client.get(evenement.get_absolute_url())

    message_1, message_2, message_3 = MessageFactory.create_batch(3, content_object=evenement)
    DocumentFactory(content_object=message_1)
    DocumentFactory(content_object=message_1)
    DocumentFactory(content_object=message_2)
    DocumentFactory(content_object=message_3)

    with django_assert_max_num_queries(BASE_NUM_QUERIES + 14):
        response = client.get(evenement.get_absolute_url())

    assert len(response.context["message_list"]) == 4


@pytest.mark.django_db
def test_evenement_performances_with_lieux(client, django_assert_num_queries):
    evenement = EvenementFactory()
    fiche_detection = FicheDetectionFactory(evenement=evenement)
    client.get(evenement.get_absolute_url())

    with django_assert_num_queries(BASE_NUM_QUERIES + 6):
        client.get(evenement.get_absolute_url())

    LieuFactory.create_batch(3, fiche_detection=fiche_detection)
    with django_assert_num_queries(BASE_NUM_QUERIES + 12):
        client.get(evenement.get_absolute_url())


@pytest.mark.django_db
def test_evenement_performances_with_document(client, django_assert_num_queries):
    evenement = EvenementFactory()
    client.get(evenement.get_absolute_url())

    with django_assert_num_queries(BASE_NUM_QUERIES):
        client.get(evenement.get_absolute_url())

    DocumentFactory.create_batch(3, content_object=evenement)
    with django_assert_num_queries(BASE_NUM_QUERIES + 1):
        client.get(evenement.get_absolute_url())


@pytest.mark.django_db
def test_evenement_performances_with_prelevement(client, django_assert_num_queries):
    evenement = EvenementFactory()

    fiche_detection = FicheDetectionFactory(evenement=evenement)
    client.get(evenement.get_absolute_url())

    with django_assert_num_queries(BASE_NUM_QUERIES + 6):
        client.get(evenement.get_absolute_url())

    PrelevementFactory.create_batch(3, lieu__fiche_detection=fiche_detection)

    with django_assert_num_queries(BASE_NUM_QUERIES + 13):
        client.get(evenement.get_absolute_url())


@pytest.mark.django_db
def test_evenement_performances_when_adding_structure(client, django_assert_num_queries):
    evenement = EvenementFactory()
    client.get(evenement.get_absolute_url())

    with django_assert_num_queries(BASE_NUM_QUERIES):
        client.get(evenement.get_absolute_url())

    for structure in ContactStructureFactory.create_batch(10):
        evenement.contacts.add(structure)

    with django_assert_num_queries(BASE_NUM_QUERIES + 2):
        client.get(evenement.get_absolute_url())


@pytest.mark.django_db
def test_evenement_fiche_zone_delimitee_with_one_detection_in_hors_zone_infestee(
    client, django_assert_num_queries, mocked_authentification_user
):
    evenement = EvenementFactory()
    FicheDetectionFactory.create_batch(3, hors_zone_infestee=evenement.fiche_zone_delimitee)
    client.get(evenement.get_absolute_url())

    with django_assert_num_queries(BASE_NUM_QUERIES):
        client.get(evenement.get_absolute_url())


@pytest.mark.django_db
def test_fiche_zone_delimitee_with_multiple_zone_infestee(
    client, django_assert_num_queries, mocked_authentification_user
):
    evenement = EvenementFactory(fiche_zone_delimitee=FicheZoneFactory())
    zone_infestee = ZoneInfesteeFactory(fiche_zone_delimitee=evenement.fiche_zone_delimitee)
    FicheDetectionFactory.create_batch(3, zone_infestee=zone_infestee, evenement=evenement)

    client.get(evenement.get_absolute_url())

    with django_assert_num_queries(BASE_NUM_QUERIES + 23):
        client.get(evenement.get_absolute_url())
