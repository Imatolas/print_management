from django.contrib import admin
from django.urls import path
from core import views as v

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", v.dashboard, name="dashboard"),

    # Estoque
    path("estoque/", v.dashboard, name="estoque-home"),  # pode apontar para uma página própria se quiser
    path("estoque/componentes/", v.estoque_componentes_list, name="estoque-componentes"),
    path("estoque/produtos/", v.estoque_produtos_list, name="estoque-produtos"),

    # Componentes – CRUD
    path("componentes/novo/", v.componentes_new, name="componentes-new"),
    path("componentes/<int:pk>/editar/", v.componentes_edit, name="componentes-edit"),
    path("componentes/<int:pk>/excluir/", v.componentes_delete, name="componentes-delete"),

    # Produtos – CRUD
    path("produtos/novo/", v.produtos_new, name="produtos-new"),
    path("produtos/<int:pk>/editar/", v.produtos_edit, name="produtos-edit"),
    path("produtos/<int:pk>/excluir/", v.produtos_delete, name="produtos-delete"),

    # Produção
    path("producao/", v.producao, name="producao"),
    path("producao/<int:pk>/editar/", v.producao_edit, name="producao-edit"),
    path("producao/<int:pk>/excluir/", v.producao_delete, name="producao-delete"),

    # Relatórios e Configurações
    path("relatorios/", v.relatorios, name="relatorios"),
    path("configuracoes/", v.configuracoes, name="configuracoes"),
]
