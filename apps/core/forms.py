from django import forms


class MaterialFormMixin:
    """Aplica classes e atributos Material aos widgets dos formulários."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "checkbox")
                continue
            if isinstance(widget, forms.SelectMultiple):
                widget.attrs.setdefault("class", "select select--multiple")
                widget.attrs.setdefault("size", 5)
                continue
            if isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "select")
                continue
            if isinstance(widget, forms.Textarea):
                widget.attrs.setdefault("class", "input textarea")
                widget.attrs.setdefault("rows", 3)
            else:
                widget.attrs.setdefault("class", "input")
            widget.attrs.setdefault("placeholder", " ")
