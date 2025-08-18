from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator

# ======== Helpers ========
def minutes_to_hhmm(total_minutes: int) -> str:
    if total_minutes is None:
        return "0h00"
    h, m = divmod(int(total_minutes), 60)
    return f"{h}h{m:02d}"

# ======== Estoque / Cadastro ========
class Component(models.Model):
    code = models.CharField("Código", max_length=32, unique=True)
    name = models.CharField("Nome", max_length=120)
    description = models.TextField("Descrição", blank=True)
    unit_cost = models.DecimalField("Custo unitário (R$)", max_digits=10, decimal_places=2, default=0)
    # tempo de impressão por unidade (em MINUTOS) — cadastra em minutos
    print_time_min = models.PositiveIntegerField("Tempo de impressão (min/un)", default=0)

    qty_on_hand = models.PositiveIntegerField("Qtd em estoque", default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def print_time_hhmm(self):
        return minutes_to_hhmm(self.print_time_min)

class Product(models.Model):
    code = models.CharField("Código", max_length=32, unique=True)
    name = models.CharField("Nome", max_length=120)
    description = models.TextField("Descrição", blank=True)
    qty_on_hand = models.PositiveIntegerField("Qtd em estoque", default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def bom_required_minutes(self, quantity: int) -> int:
        # minutos totais para imprimir todos componentes deste produto * quantidade
        total = 0
        for item in self.bom_items.all():
            total += (item.component.print_time_min * item.quantity * quantity)
        return total

    def estimated_build_hours(self, quantity: int) -> str:
        return minutes_to_hhmm(self.bom_required_minutes(quantity))

class BOMItem(models.Model):
    product = models.ForeignKey(Product, related_name="bom_items", on_delete=models.CASCADE)
    component = models.ForeignKey(Component, related_name="bom_items", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField("Qtd por produto", default=1, validators=[MinValueValidator(1)])

    class Meta:
        unique_together = ("product", "component")

    def __str__(self):
        return f"{self.product.code} -> {self.component.code} x{self.quantity}"

    @property
    def line_minutes(self):
        return self.component.print_time_min * self.quantity

# ======== Produção ========
class ProductionOrder(models.Model):
    STATUS_CHOICES = [
        ("open", "Aberta"),
        ("done", "Finalizada"),
        ("cancelled", "Cancelada"),
    ]
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="orders")
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="open")
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"OP #{self.id} - {self.product.code} x{self.quantity} ({self.get_status_display()})"

    def required_for_component(self, component: 'Component') -> int:
        try:
            bom = self.product.bom_items.get(component=component)
        except BOMItem.DoesNotExist:
            return 0
        return bom.quantity * self.quantity

    def printed_for_component(self, component: 'Component') -> int:
        agg = self.logs.filter(component=component).aggregate(models.Sum("quantity"))
        return agg["quantity__sum"] or 0

    def progress_for_component(self, component: 'Component') -> float:
        req = self.required_for_component(component)
        if req <= 0:
            return 100.0
        printed = self.printed_for_component(component)
        return min(100.0, (printed / req) * 100.0)

    def time_remaining_minutes_for_component(self, component: 'Component') -> int:
        req = self.required_for_component(component)
        printed = self.printed_for_component(component)
        rem = max(0, req - printed)
        return rem * component.print_time_min

    @property
    def progress_percent(self) -> float:
        # média ponderada por quantidade requerida de cada componente
        items = list(self.product.bom_items.all())
        if not items:
            return 100.0
        total_req = sum(self.required_for_component(i.component) for i in items)
        if total_req == 0:
            return 100.0
        total_printed = sum(self.printed_for_component(i.component) for i in items)
        return min(100.0, (total_printed / total_req) * 100.0)

class ProductionLog(models.Model):
    order = models.ForeignKey(ProductionOrder, related_name="logs", on_delete=models.CASCADE)
    component = models.ForeignKey(Component, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(default=timezone.now)

    # tempo total gasto nesta impressão (em minutos) — calculado a partir do componente
    @property
    def spent_minutes(self) -> int:
        return self.component.print_time_min * self.quantity

    @property
    def spent_hhmm(self) -> str:
        return minutes_to_hhmm(self.spent_minutes)
