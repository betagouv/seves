import pytest
from model_bakery import baker

from core.models import Message, Document, Structure, Contact
from sv.models import Lieu, Prelevement

BASE_NUM_QUERIES = 15  # Please note a first call is made without assertion to warm up any possible cache


@pytest.mark.django_db
def test_empty_fiche_detection_performances(client, django_assert_num_queries, fiche_detection):
    client.get(fiche_detection.get_absolute_url())

    with django_assert_num_queries(BASE_NUM_QUERIES):
        client.get(fiche_detection.get_absolute_url())


@pytest.mark.django_db
def test_fiche_detection_performances_with_messages_from_same_user(
    client, django_assert_num_queries, mocked_authentification_user, fiche_detection
):
    client.get(fiche_detection.get_absolute_url())

    baker.make(Message, content_object=fiche_detection, sender=mocked_authentification_user.agent.contact_set.get())
    with django_assert_num_queries(BASE_NUM_QUERIES + 6):
        client.get(fiche_detection.get_absolute_url())

    baker.make(
        Message,
        content_object=fiche_detection,
        sender=mocked_authentification_user.agent.contact_set.get(),
        _quantity=3,
    )

    with django_assert_num_queries(BASE_NUM_QUERIES + 6):
        response = client.get(fiche_detection.get_absolute_url())

    assert len(response.context["message_list"]) == 4


@pytest.mark.django_db
def test_fiche_detection_performances_with_lieux(client, django_assert_num_queries, fiche_detection):
    client.get(fiche_detection.get_absolute_url())

    with django_assert_num_queries(BASE_NUM_QUERIES):
        client.get(fiche_detection.get_absolute_url())

    baker.make(Lieu, fiche_detection=fiche_detection, _quantity=3, _fill_optional=True)
    with django_assert_num_queries(BASE_NUM_QUERIES):
        client.get(fiche_detection.get_absolute_url())


@pytest.mark.django_db
def test_fiche_detection_performances_with_document(client, django_assert_num_queries, fiche_detection):
    client.get(fiche_detection.get_absolute_url())

    with django_assert_num_queries(BASE_NUM_QUERIES):
        client.get(fiche_detection.get_absolute_url())

    baker.make(Document, content_object=fiche_detection, _quantity=3, _create_files=True)
    with django_assert_num_queries(BASE_NUM_QUERIES + 1):
        client.get(fiche_detection.get_absolute_url())


@pytest.mark.django_db
def test_fiche_detection_performances_with_prelevement(client, django_assert_num_queries, fiche_detection):
    client.get(fiche_detection.get_absolute_url())

    with django_assert_num_queries(BASE_NUM_QUERIES):
        client.get(fiche_detection.get_absolute_url())

    for _ in range(0, 3):
        lieu = baker.make(Lieu, fiche_detection=fiche_detection)
        baker.make(
            Prelevement,
            lieu=lieu,
            is_officiel=False,
            numero_rapport_inspection="",
            laboratoire_agree=None,
            laboratoire_confirmation_officielle=None,
            _fill_optional=True,
        )

    with django_assert_num_queries(BASE_NUM_QUERIES):
        client.get(fiche_detection.get_absolute_url())


@pytest.mark.django_db
def test_fiche_detection_performances_when_adding_structure(client, django_assert_num_queries, fiche_detection):
    client.get(fiche_detection.get_absolute_url())

    with django_assert_num_queries(BASE_NUM_QUERIES):
        client.get(fiche_detection.get_absolute_url())

    for _ in range(0, 10):
        structure = baker.make(Structure)
        contact = baker.make(Contact, structure=structure, agent=None)
        fiche_detection.contacts.add(contact)

    with django_assert_num_queries(BASE_NUM_QUERIES + 1):
        client.get(fiche_detection.get_absolute_url())
