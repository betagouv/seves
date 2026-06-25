from enum import auto
from unittest.mock import ANY

from django.db.models import TextChoices

from core.mixins import GroupedChoicesMixin
from core.widgets import TreeselectGroup, TreeselectItem


class TestChoices(GroupedChoicesMixin, TextChoices):
    TOULOUSE = auto(), "Europe > France > Toulouse"
    PARIS = auto(), "Europe > France > Paris"
    FRANCE = auto(), "Europe > France"
    MUNICH = auto(), "Europe > Allemagne > Munich"
    BERLIN = auto(), "Europe > Allemagne > Berlin"
    PORTE_DE_BRANDEBOURG = auto(), "Europe > Allemagne > Berlin > Porte de Brandebourg"
    HAMBOURG = auto(), "Europe > Allemagne > Hambourg"
    CHILI = auto(), "Amérique > Amérique du sud > Chili"
    ARGENTINE = auto(), "Amérique > Amérique du sud > Argentine"
    NICARAGUA = auto(), "Amérique > Amérique centrale > Nicaragua"
    MEXIQUE = auto(), "Amérique > Amérique centrale > Mexique"
    BRESIL = auto(), "Amérique > Amérique du sud > Brésil"
    SAO_POLO = auto(), "Amérique > Amérique du sud > Brésil > São Paulo"


def test_treeselect_groups():
    assert TestChoices.treeselect_groups == [
        TreeselectGroup(
            value=ANY,
            label="Europe",
            choices=[
                TreeselectGroup(
                    value="FRANCE",
                    label="France",
                    choices=[
                        TreeselectItem(
                            value="TOULOUSE",
                            label="Toulouse",
                            categorised_label="Europe > France > Toulouse",
                            html_name_prefix=None,
                        ),
                        TreeselectItem(
                            value="PARIS",
                            label="Paris",
                            categorised_label="Europe > France > Paris",
                            html_name_prefix=None,
                        ),
                    ],
                    categorised_label="Europe > France",
                    can_expand=True,
                ),
                TreeselectGroup(
                    value=ANY,
                    label="Allemagne",
                    choices=[
                        TreeselectItem(
                            value="MUNICH",
                            label="Munich",
                            categorised_label="Europe > Allemagne > Munich",
                            html_name_prefix=None,
                        ),
                        TreeselectGroup(
                            value="BERLIN",
                            label="Berlin",
                            choices=[
                                TreeselectItem(
                                    value="PORTE_DE_BRANDEBOURG",
                                    label="Porte de Brandebourg",
                                    categorised_label="Europe > Allemagne > Berlin > Porte de Brandebourg",
                                    html_name_prefix=None,
                                ),
                            ],
                            categorised_label="Europe > Allemagne > Berlin",
                            can_expand=True,
                        ),
                        TreeselectItem(
                            value="HAMBOURG",
                            label="Hambourg",
                            categorised_label="Europe > Allemagne > Hambourg",
                            html_name_prefix=None,
                        ),
                    ],
                    categorised_label=None,
                    can_expand=True,
                ),
            ],
            categorised_label=None,
            can_expand=True,
        ),
        TreeselectGroup(
            value=ANY,
            label="Amérique",
            choices=[
                TreeselectGroup(
                    value=ANY,
                    label="Amérique du sud",
                    choices=[
                        TreeselectItem(
                            value="CHILI",
                            label="Chili",
                            categorised_label="Amérique > Amérique du sud > Chili",
                            html_name_prefix=None,
                        ),
                        TreeselectItem(
                            value="ARGENTINE",
                            label="Argentine",
                            categorised_label="Amérique > Amérique du sud > Argentine",
                            html_name_prefix=None,
                        ),
                        TreeselectGroup(
                            value="BRESIL",
                            label="Brésil",
                            choices=[
                                TreeselectItem(
                                    value="SAO_POLO",
                                    label="São Paulo",
                                    categorised_label="Amérique > Amérique du sud > Brésil > São Paulo",
                                    html_name_prefix=None,
                                ),
                            ],
                            categorised_label="Amérique > Amérique du sud > Brésil",
                            can_expand=True,
                        ),
                    ],
                    categorised_label=None,
                    can_expand=True,
                ),
                TreeselectGroup(
                    value=ANY,
                    label="Amérique centrale",
                    choices=[
                        TreeselectItem(
                            value="NICARAGUA",
                            label="Nicaragua",
                            categorised_label="Amérique > Amérique centrale > Nicaragua",
                            html_name_prefix=None,
                        ),
                        TreeselectItem(
                            value="MEXIQUE",
                            label="Mexique",
                            categorised_label="Amérique > Amérique centrale > Mexique",
                            html_name_prefix=None,
                        ),
                    ],
                    categorised_label=None,
                    can_expand=True,
                ),
            ],
            categorised_label=None,
            can_expand=True,
        ),
    ]
