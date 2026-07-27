from django import forms
from django.contrib.gis.geos import Point


class LatLonWidget(forms.MultiWidget):
    template_name = "sa/widgets/latlon.html"

    def __init__(self, attrs=None):
        widgets = (
            forms.TextInput(
                attrs={
                    "step": "any",
                    "placeholder": "Latitude",
                    "inputmode": "numeric",
                    "pattern": "^-?[0-9]+(\\.[0-9]+)?$",
                    "data-map-target": "latitudeInput",
                    "data-action": "map#onCoordinateChange",
                    "data-address-search-autocomplete-target": "latitude",
                }
            ),
            forms.TextInput(
                attrs={
                    "step": "any",
                    "placeholder": "Longitude",
                    "inputmode": "numeric",
                    "pattern": "^-?[0-9]+(\\.[0-9]+)?$",
                    "data-map-target": "longitudeInput",
                    "data-action": "map#onCoordinateChange",
                    "data-address-search-autocomplete-target": "longitude",
                }
            ),
        )
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if isinstance(value, Point):
            return [value.y, value.x]
        return [None, None]

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["subwidgets"][0]["label"] = "Latitude"
        context["widget"]["subwidgets"][1]["label"] = "Longitude"
        return context


class LatLonField(forms.MultiValueField):
    widget = LatLonWidget

    def __init__(self, *args, **kwargs):
        fields = (
            forms.FloatField(min_value=-90, max_value=90),
            forms.FloatField(min_value=-180, max_value=180),
        )
        super().__init__(fields=fields, require_all_fields=True, *args, **kwargs)

    def compress(self, data_list):
        if not data_list:
            return None

        lat, lon = data_list
        if lat is None or lon is None:
            return None

        return Point(lon, lat, srid=4326)
