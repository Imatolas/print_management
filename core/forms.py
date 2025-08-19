from django import forms
from django.forms import inlineformset_factory
from .models import Component, Product, BOMItem, ProductionOrder, ProductionLog

class ComponentForm(forms.ModelForm):
    # Entrada sempre em minutos
    class Meta:
        model = Component
        fields = ['code', 'name', 'description', 'material', 'unit_cost', 'print_time_min', 'qty_on_hand']
        widgets = {
            'description': forms.Textarea(attrs={'rows':3}),
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['code', 'name', 'description', 'qty_on_hand']
        widgets = {
            'description': forms.Textarea(attrs={'rows':3})
        }

class ComponentSelect(forms.Select):
    """Select que oculta a opção em branco e desabilita mensagens."""

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value == "":
            option["attrs"]["hidden"] = True
        if value == "__none__":
            option["attrs"]["disabled"] = True
        return option


class BOMItemForm(forms.ModelForm):
    component = forms.ModelChoiceField(
        queryset=Component.objects.all(),
        empty_label="",
        widget=ComponentSelect,
        required=False,
    )

    class Meta:
        model = BOMItem
        fields = ["component", "quantity"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields["component"]
        if not field.queryset.exists():
            field.choices = [("", ""), ("__none__", "Nenhum componente cadastrado")]

BOMFormSet = inlineformset_factory(Product, BOMItem, form=BOMItemForm, extra=1, can_delete=True)

class ProductionOrderForm(forms.ModelForm):
    class Meta:
        model = ProductionOrder
        fields = ['product', 'quantity', 'due_date', 'notes']

class ProductionLogForm(forms.ModelForm):
    class Meta:
        model = ProductionLog
        fields = ['component', 'quantity']
