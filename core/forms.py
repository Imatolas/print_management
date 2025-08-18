from django import forms
from django.forms import inlineformset_factory
from .models import Component, Product, BOMItem, ProductionOrder, ProductionLog

class ComponentForm(forms.ModelForm):
    # Entrada sempre em minutos
    class Meta:
        model = Component
        fields = ['code', 'name', 'description', 'unit_cost', 'print_time_min', 'qty_on_hand']
        widgets = {
            'description': forms.Textarea(attrs={'rows':3})
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['code', 'name', 'description', 'qty_on_hand']
        widgets = {
            'description': forms.Textarea(attrs={'rows':3})
        }

class BOMItemForm(forms.ModelForm):
    class Meta:
        model = BOMItem
        fields = ['component', 'quantity']

BOMFormSet = inlineformset_factory(Product, BOMItem, form=BOMItemForm, extra=1, can_delete=True)

class ProductionOrderForm(forms.ModelForm):
    class Meta:
        model = ProductionOrder
        fields = ['product', 'quantity', 'due_date', 'notes']

class ProductionLogForm(forms.ModelForm):
    class Meta:
        model = ProductionLog
        fields = ['component', 'quantity']
