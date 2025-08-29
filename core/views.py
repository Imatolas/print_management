from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib import messages

from .models import Component, Product, BOMItem, ProductionOrder, minutes_to_hhmm
from .forms import ComponentForm, ProductForm, BOMFormSet, ProductionOrderForm

# ----------------------
# Helpers tolerantes a diferenças nos modelos
# ----------------------

def _get_any_attr(obj, names, default=0):
    """Tenta retornar o primeiro atributo existente em names; senão, default."""
    for n in names:
        if hasattr(obj, n):
            val = getattr(obj, n)
            # se for callable (property com @property não é callable), ignora
            try:
                if callable(val):
                    continue
            except Exception:
                pass
            return val if val is not None else default
    return default

def _qty_on_hand_for(obj):
    """
    Tenta descobrir a quantidade em estoque para Component ou Product.
    Primeiro procura um campo direto no objeto; depois tenta objetos relacionados comuns.
    """
    # campos diretos comuns
    direct = _get_any_attr(
        obj,
        ["qty_on_hand", "stock", "quantity", "amount", "qtd", "qtd_estoque", "estoque"],
        default=None,
    )
    if direct is not None:
        try:
            return float(direct)
        except Exception:
            return 0

    # relacionamentos comuns
    related_candidates = [
        "inventory",
        "componentinventory",
        "productinventory",
        "estoque",
        "inventario",
    ]
    for rel in related_candidates:
        if hasattr(obj, rel):
            rel_obj = getattr(obj, rel)
            if rel_obj is None:
                continue
            val = _get_any_attr(
                rel_obj,
                ["qty_on_hand", "stock", "quantity", "amount", "qtd", "qtd_estoque", "estoque"],
                default=None,
            )
            if val is not None:
                try:
                    return float(val)
                except Exception:
                    return 0
    return 0

def _cost_for_component(c):
    """Custo unitário de um componente com nomes de campo comuns."""
    val = _get_any_attr(c, ["cost", "unit_cost", "custo", "preco"], default=0)
    try:
        return float(val)
    except Exception:
        return 0.0

def _time_min_for_component(c):
    """Tempo de impressão (min) por unidade (nomes comuns)."""
    val = _get_any_attr(
        c,
        ["print_time_min", "print_time_minutes", "tempo_min", "tempo_minutos", "time_per_unit_min"],
        default=0,
    )
    try:
        return float(val)
    except Exception:
        return 0.0

def _quantity_for_bom_item(item):
    """Quantidade do item no BOM (nomes comuns)."""
    val = _get_any_attr(item, ["quantity", "qty", "qtd"], default=0)
    try:
        return float(val)
    except Exception:
        return 0.0


# ----------------------
# DASHBOARD
# ----------------------
def dashboard(request):
    # Totais simples
    total_componentes = Component.objects.count()
    total_produtos = Product.objects.count()

    # Valor total em estoque (qtd * custo) sem depender de 'inventory'
    valor_total_estoque = 0.0
    for c in Component.objects.all():
        qty = _qty_on_hand_for(c)
        cost = _cost_for_component(c)
        valor_total_estoque += qty * cost

    # Estoque baixo (exemplo: <= 3 unidades)
    low_components = []
    for c in Component.objects.all():
        if _qty_on_hand_for(c) <= 3:
            low_components.append(c)

    low_products = []
    for p in Product.objects.all():
        if _qty_on_hand_for(p) <= 3:
            low_products.append(p)

    # Progresso de impressão das ordens em andamento
    progress_items = []
    for op in ProductionOrder.objects.filter(status="open").select_related("product"):
        rows = []
        total_required = 0
        total_printed = 0
        total_remaining_min = 0
        for item in op.product.bom_items.select_related("component"):
            comp = item.component
            req = op.required_for_component(comp)
            printed = op.printed_for_component(comp)
            progress = op.progress_for_component(comp)
            rem_min = op.time_remaining_minutes_for_component(comp)
            rows.append(
                {
                    "component": comp,
                    "required": req,
                    "printed": printed,
                    "progress": progress,
                    "time_remaining_hhmm": minutes_to_hhmm(rem_min),
                }
            )
            total_required += req
            total_printed += printed
            if rem_min > total_remaining_min:
                total_remaining_min = rem_min
        progress_items.append(
            {
                "product": op.product,
                "total_required": total_required,
                "total_printed": total_printed,
                "progress_percent": op.progress_percent,
                "time_remaining_hhmm": minutes_to_hhmm(total_remaining_min),
                "rows": rows,
            }
        )

    # Ordens abertas para seleção no modal de progresso
    open_orders = list(
        ProductionOrder.objects.filter(status="open").select_related("product")
    )

    ctx = {
        "total_componentes": total_componentes,
        "total_produtos": total_produtos,
        "valor_total_estoque": valor_total_estoque,
        "low_components": low_components,
        "low_products": low_products,
        "progress_items": progress_items,
        "open_orders": open_orders,
    }
    return render(request, "dashboard.html", ctx)


# ----------------------
# COMPONENTES – LISTAR / EDITAR / EXCLUIR
# ----------------------
def estoque_componentes_list(request):
    q = request.GET.get("q", "").strip()
    qs = Component.objects.all()
    if q:
        qs = qs.filter(Q(code__icontains=q) | Q(name__icontains=q))
    components = list(qs.order_by("code", "name"))
    return render(
        request,
        "estoque/componentes_list.html",
        {"components": components, "q": q},
    )


def componentes_new(request):
    if request.method == "POST":
        form = ComponentForm(request.POST)
        if form.is_valid():
            obj = form.save()
            messages.success(request, f"Componente “{obj.name}” criado.")
            return redirect("estoque-componentes")
    else:
        form = ComponentForm()
    return render(request, "componentes_form.html", {"form": form})


def componentes_edit(request, pk):
    obj = get_object_or_404(Component, pk=pk)
    if request.method == "POST":
        form = ComponentForm(request.POST, instance=obj)
        if form.is_valid():
            obj = form.save()
            messages.success(request, f"Componente “{obj.name}” atualizado.")
            return redirect("estoque-componentes")
    else:
        form = ComponentForm(instance=obj)
    return render(request, "componentes_form.html", {"form": form, "obj": obj})


def componentes_delete(request, pk):
    obj = get_object_or_404(Component, pk=pk)
    if request.method == "POST":
        name = obj.name
        obj.delete()
        messages.success(request, f"Componente “{name}” excluído.")
        return redirect("estoque-componentes")
    return render(request, "confirm_delete.html", {"title": "Excluir componente", "object": obj})


# ----------------------
# PRODUTOS – LISTAR / EDITAR / EXCLUIR
# ----------------------
def estoque_produtos_list(request):
    q = request.GET.get("q", "").strip()
    qs = Product.objects.all()
    if q:
        qs = qs.filter(Q(code__icontains=q) | Q(name__icontains=q))
    products = list(qs.order_by("code", "name"))

    # Calcula tempo total (min), custo total e materiais a partir do BOM
    rows = []
    for p in products:
        qty_on_hand = _qty_on_hand_for(p)

        total_time_min = 0.0
        materials = set()

        for item in BOMItem.objects.filter(product=p).select_related("component"):
            comp = item.component
            qty = _quantity_for_bom_item(item)
            total_time_min += _time_min_for_component(comp) * qty
            if comp.material:
                materials.add(comp.material)

        rows.append(
            {
                "obj": p,
                "qty_on_hand": qty_on_hand,
                "total_cost": p.total_cost,
                "total_time_min": total_time_min,
                "materials": ", ".join(sorted(materials)),
            }
        )
    return render(
        request,
        "estoque/produtos_list.html",
        {"products": rows, "q": q},
    )


def produtos_new(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        product = Product()
        formset = BOMFormSet(request.POST, instance=product)
        if form.is_valid() and formset.is_valid():
            product = form.save()
            formset.instance = product
            formset.save()
            messages.success(request, f"Produto “{product.name}” criado.")
            return redirect("estoque-produtos")
    else:
        form = ProductForm()
        formset = BOMFormSet(instance=Product())
    return render(request, "produtos_form.html", {"form": form, "formset": formset})


def produtos_edit(request, pk):
    obj = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, instance=obj)
        formset = BOMFormSet(request.POST, instance=obj)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f"Produto “{obj.name}” atualizado.")
            return redirect("estoque-produtos")
    else:
        form = ProductForm(instance=obj)
        formset = BOMFormSet(instance=obj)
    return render(request, "produtos_form.html", {"form": form, "formset": formset, "obj": obj})


def produtos_delete(request, pk):
    obj = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        name = obj.name
        obj.delete()
        messages.success(request, f"Produto “{name}” excluído.")
        return redirect("estoque-produtos")
    return render(request, "confirm_delete.html", {"title": "Excluir produto", "object": obj})


# ----------------------
# PRODUÇÃO
# ----------------------
def producao(request):
    form = ProductionOrderForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Ordem de produção criada.")
        return redirect("producao")

    orders = []
    qs = ProductionOrder.objects.filter(status="open").select_related("product")
    for op in qs:
        total_min = op.product.bom_required_minutes(op.quantity)
        comps = []
        for item in op.product.bom_items.select_related("component"):
            req_qty = item.quantity * op.quantity
            time_total = item.component.print_time_min * req_qty
            cost_total = float(item.component.unit_cost) * req_qty
            comps.append(
                {
                    "component": item.component,
                    "required_qty": req_qty,
                    "time_total": minutes_to_hhmm(time_total),
                    "cost_total": cost_total,
                }
            )
        orders.append(
            {
                "obj": op,
                "total_time": minutes_to_hhmm(total_min),
                "components": comps,
            }
        )


    return render(request, "producao.html", {"form": form, "orders": orders})


def producao_edit(request, pk):
    obj = get_object_or_404(ProductionOrder, pk=pk)
    form = ProductionOrderForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Ordem de produção atualizada.")
        return redirect("producao")
    return render(request, "producao_form.html", {"form": form, "obj": obj})


def producao_delete(request, pk):
    obj = get_object_or_404(ProductionOrder, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Ordem de produção excluída.")
        return redirect("producao")
    return render(
        request,
        "confirm_delete.html",
        {"title": "Excluir produção", "object": obj},
    )


# A view específica para editar apenas componentes do produto não é mais necessária,
# pois `produtos_edit` já lida com o formulário principal e o BOM.


def relatorios(request):
    return render(
        request,
        "stub.html",
        {"title": "Relatórios", "text": "Página de relatórios em construção."},
    )


def configuracoes(request):
    return render(
        request,
        "stub.html",
        {"title": "Configurações", "text": "Página de configurações em construção."},
    )


def plan_schedule(request):
    from .models import WorkOrder

    workorders = WorkOrder.objects.all()
    return render(request, "plan/schedule.html", {"workorders": workorders})
