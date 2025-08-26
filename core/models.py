from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from datetime import timedelta

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
    material = models.CharField("Material", max_length=60, blank=True)
    unit_cost = models.DecimalField("Custo unitário (R$)", max_digits=10, decimal_places=2, default=0)
    production_time = models.DurationField("Tempo de produção", default=timedelta())
    # tempo de impressão por unidade (em MINUTOS) — cadastra em minutos
    print_time_min = models.PositiveIntegerField("Tempo de impressão (min/un)", default=0)

    # novos campos para escalonamento de impressão 3D
    base_time_min = models.PositiveIntegerField("Tempo base (min)", default=0)
    per_plate_time_min = models.PositiveIntegerField("Tempo por prato (min)", default=0)
    batch_size = models.PositiveIntegerField("Qtd por prato", default=1)
    tags_required = models.CharField("Tags requeridas", max_length=120, blank=True)

    qty_on_hand = models.PositiveIntegerField("Qtd em estoque", default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        mat = f" ({self.material})" if self.material else ""
        return f"{self.code} - {self.name}{mat}"

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

    @property
    def total_cost(self) -> float:
        """Custo total somando os componentes do produto."""
        total = 0.0
        for item in self.bom_items.select_related("component"):
            total += float(item.component.unit_cost) * item.quantity
        return total

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

    def time_remaining_minutes(self) -> int:
        """Tempo restante agregado (minutos) para concluir a ordem."""
        items = list(self.product.bom_items.select_related("component"))
        if not items:
            return 0
        times = [
            self.time_remaining_minutes_for_component(item.component)
            for item in items
        ]
        return max(times) if times else 0

    @property
    def time_remaining_hhmm(self) -> str:
        return minutes_to_hhmm(self.time_remaining_minutes())

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


# ======== Impressoras e Ordens de Trabalho ========
class Printer(models.Model):
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)
    speed_factor = models.FloatField(default=1.0, validators=[MinValueValidator(0.01)])
    tags = models.CharField(max_length=120, blank=True)
    volume_x = models.PositiveIntegerField(null=True, blank=True)
    volume_y = models.PositiveIntegerField(null=True, blank=True)
    volume_z = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return self.name


class PrintTask(models.Model):
    order = models.ForeignKey(
        ProductionOrder, related_name="print_tasks", on_delete=models.CASCADE
    )
    component = models.ForeignKey(Component, on_delete=models.PROTECT)
    printer = models.ForeignKey(Printer, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1)]
    )
    status = models.CharField(max_length=20, default="pending")

    def clean(self):
        if self.printer and not self.printer.is_active:
            raise ValidationError(
                "Impressora selecionada está inativa. Escolha outra impressora."
            )
        if self.quantity <= 0:
            raise ValidationError("Quantidade deve ser maior que zero.")
        if self.order_id and self.component_id:
            required = self.order.required_for_component(self.component)
            assigned = (
                self.order.print_tasks.filter(component=self.component)
                .exclude(pk=self.pk)
                .aggregate(models.Sum("quantity"))["quantity__sum"]
                or 0
            )
            total = assigned + self.quantity
            if total > required:
                raise ValidationError(
                    f"A soma das quantidades das tarefas para o componente {self.component.name} ({total}) excede a quantidade necessária ({required}). Ajuste as tarefas."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def t_piece_hours(self) -> float:
        return (self.component.print_time_min or 0) / 60.0

    @property
    def time_hours(self) -> float:
        speed = self.printer.speed_factor or 1.0
        return (self.quantity * self.t_piece_hours) / speed


class WorkOrder(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    due_date = models.DateField(null=True, blank=True)
    priority = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-priority", "due_date"]

    def __str__(self):
        return f"WO #{self.id} - {self.product.code} x{self.quantity}"
