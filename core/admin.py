from django.contrib import admin
from .models import Component, Product, BOMItem, ProductionOrder, ProductionLog

@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    list_display = ('code','name','unit_cost','print_time_min','qty_on_hand')
    search_fields = ('code','name')

class BOMInline(admin.TabularInline):
    model = BOMItem
    extra = 0

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('code','name','qty_on_hand')
    search_fields = ('code','name')
    inlines = [BOMInline]

@admin.register(ProductionOrder)
class ProductionOrderAdmin(admin.ModelAdmin):
    list_display = ('id','product','quantity','status','created_at','due_date')
    list_filter = ('status',)

@admin.register(ProductionLog)
class ProductionLogAdmin(admin.ModelAdmin):
    list_display = ('id','order','component','quantity','created_at')
    list_filter = ('component',)
