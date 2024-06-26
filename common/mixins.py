from django import forms


class DSFRFormMixin:
    def apply_input_form_css_classes(self):
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                css_class = "fr-select"
            elif isinstance(field.widget, forms.TextInput):
                css_class = "fr-input"
            else:
                css_class = "fr-default"
            field.widget.attrs.update({"class": css_class})
