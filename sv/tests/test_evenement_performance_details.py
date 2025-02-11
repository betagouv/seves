import pytest
from model_bakery import baker

from core.models import Message, Document, Structure, Contact
from sv.factories import EvenementFactory, FicheDetectionFactory, PrelevementFactory, FicheZoneFactory
from sv.models import Lieu, ZoneInfestee

BASE_NUM_QUERIES = 18  # Please note a first call is made without assertion to warm up any possible cache


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

    baker.make(Message, content_object=evenement, sender=mocked_authentification_user.agent.contact_set.get())
    with django_assert_num_queries(BASE_NUM_QUERIES + 6):
        client.get(evenement.get_absolute_url())

    baker.make(
        Message,
        content_object=evenement,
        sender=mocked_authentification_user.agent.contact_set.get(),
        _quantity=3,
    )

    with django_assert_num_queries(BASE_NUM_QUERIES + 6):
        response = client.get(evenement.get_absolute_url())

    assert len(response.context["message_list"]) == 4


@pytest.mark.django_db
def test_evenement_performances_with_lieux(client, django_assert_num_queries):
    evenement = EvenementFactory()
    fiche_detection = FicheDetectionFactory(evenement=evenement)
    client.get(evenement.get_absolute_url())

    with django_assert_num_queries(BASE_NUM_QUERIES + 6):
        client.get(evenement.get_absolute_url())

    baker.make(Lieu, fiche_detection=fiche_detection, _quantity=3, _fill_optional=True)
    with django_assert_num_queries(BASE_NUM_QUERIES + 12):
        client.get(evenement.get_absolute_url())


@pytest.mark.django_db
def test_evenement_performances_with_document(client, django_assert_num_queries):
    evenement = EvenementFactory()
    client.get(evenement.get_absolute_url())

    with django_assert_num_queries(BASE_NUM_QUERIES):
        client.get(evenement.get_absolute_url())

    baker.make(Document, content_object=evenement, _quantity=3, _create_files=True)
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

    with django_assert_num_queries(BASE_NUM_QUERIES + 12):
        client.get(evenement.get_absolute_url())


@pytest.mark.django_db
def test_evenement_performances_when_adding_structure(client, django_assert_num_queries):
    evenement = EvenementFactory()
    client.get(evenement.get_absolute_url())

    with django_assert_num_queries(BASE_NUM_QUERIES):
        client.get(evenement.get_absolute_url())

    for _ in range(0, 10):
        structure = baker.make(Structure)
        contact = baker.make(Contact, structure=structure, agent=None)
        evenement.contacts.add(contact)

    with django_assert_num_queries(BASE_NUM_QUERIES + 1):
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
    zone_infestee = baker.make(ZoneInfestee, fiche_zone_delimitee=evenement.fiche_zone_delimitee)
    FicheDetectionFactory.create_batch(3, zone_infestee=zone_infestee, evenement=evenement)

    client.get(evenement.get_absolute_url())

    with django_assert_num_queries(BASE_NUM_QUERIES + 25):
        client.get(evenement.get_absolute_url())
