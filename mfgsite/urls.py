from django.contrib import admin
from django.urls import path
from core import views as v
from core import api

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

    # Planejamento de impressão
    path("plan/schedule/", v.plan_schedule, name="plan-schedule"),

    # API
    path("api/printers/", api.PrinterListAPIView.as_view(), name="api-printers"),
    path("api/printers/<int:pk>/toggle/", api.PrinterToggleAPIView.as_view(), name="api-printer-toggle"),
    path("api/schedule/", api.ScheduleAPIView.as_view(), name="api-schedule"),
    path("api/workorders/<int:pk>/tasks/preview/", api.WorkOrderTasksPreviewAPIView.as_view(), name="api-workorder-preview"),
    path("api/products/<int:pk>/components/", api.ProductComponentsAPIView.as_view(), name="api-product-components"),
    path("api/print-time/", api.PrintTimeAPIView.as_view(), name="api-print-time"),
    path("api/logs/", api.ProductionLogCreateAPIView.as_view(), name="api-log-create"),
]
