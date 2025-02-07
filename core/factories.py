import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory
from core.models import Structure, Agent, Contact, Document


class StructureFactory(DjangoModelFactory):
    class Meta:
        model = Structure

    niveau1 = factory.Faker("sentence", nb_words=2)
    niveau2 = factory.Faker("sentence", nb_words=2)
    libelle = factory.Faker("sentence", nb_words=2)


class UserFactory(DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@test.fr")


class AgentFactory(DjangoModelFactory):
    class Meta:
        model = Agent

    user = factory.SubFactory(
        UserFactory,
        email=factory.LazyAttribute(
            lambda u: f"{u.factory_parent.nom.lower()}_{u.factory_parent.prenom.lower()}@test.fr"
        ),
    )
    structure = factory.SubFactory(StructureFactory)
    structure_complete = factory.LazyAttribute(lambda obj: f"{obj.structure.niveau1}/{obj.structure.niveau2}")
    prenom = factory.Faker("first_name")
    nom = factory.Faker("last_name")
    fonction_hierarchique = factory.Iterator(
        [
            "Chef de service",
            "Adjoint au chef de service",
            "Chef de bureau",
            "Adjoint au chef de bureau",
            "Chargé de mission",
            "Responsable de pôle",
        ]
    )
    complement_fonction = factory.Iterator(
        [
            "Coordination des projets",
            "Suivi budgétaire",
            "Pilotage de la performance",
            "Gestion des ressources humaines",
            "Relations internationales",
            "Animation du réseau",
            "",
        ]
    )
    telephone = factory.Faker("phone_number", locale="fr_FR")
    mobile = factory.Faker("phone_number", locale="fr_FR")


class ContactAgentFactory(DjangoModelFactory):
    class Meta:
        model = Contact

    agent = factory.SubFactory(AgentFactory)
    structure = None
    email = factory.LazyAttribute(lambda obj: obj.agent.user.email)


class ContactStructureFactory(DjangoModelFactory):
    class Meta:
        model = Contact

    agent = None
    structure = factory.SubFactory(StructureFactory)
    email = factory.Sequence(lambda n: f"contact{n}@test.fr")


class DocumentFactory(DjangoModelFactory):
    class Meta:
        model = Document

    nom = factory.Faker("sentence", nb_words=2)
    file = factory.django.FileField(filename="test.csv")

    @factory.lazy_attribute
    def created_by(self):
        return Agent.objects.get(user__email="test@example.com")

    @factory.lazy_attribute
    def created_by_structure(self):
        return Structure.objects.get(libelle="Structure Test")
