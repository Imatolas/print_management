from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('relatorios/', views.relatorios, name='relatorios'),
    path('configuracoes/', views.configuracoes, name='configuracoes'),
]