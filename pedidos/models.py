from django.db import models

class Pizza(models.Model):
    nombre=models.CharField(max_length=50)
    precio=models.DecimalField(max_digits=10, decimal_places=2)
    disponible=models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Jornada(models.Model):
    inicio = models.DateTimeField(auto_now_add=True)
    fin = models.DateTimeField(null=True, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f'Jornada {self.inicio:%d/%m/%Y %H:%M}'

class Pedido(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'pendiente en cocina'),
        ('entregado', 'Entregado'),
        ('cerrado', 'Cerrado'),
    ]
    cliente=models.CharField(max_length=100)
    estado=models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha=models.DateTimeField(auto_now_add=True)
    hora_entrega=models.TimeField(null=True, blank=True)
    jornada=models.ForeignKey(Jornada, related_name='pedidos', on_delete=models.SET_NULL, null=True, blank=True)
    total=models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering=['-fecha']

    def __str__(self):
        return f'# {self.id} · {self.cliente}'

class DetallePedido(models.Model):
    pedido=models.ForeignKey(Pedido, related_name='detalles', on_delete=models.CASCADE)
    pizza=models.ForeignKey(Pizza, related_name='mitades1', on_delete=models.PROTECT)
    pizza_mitad2=models.ForeignKey(Pizza, related_name='mitades2', on_delete=models.PROTECT, null=True, blank=True)
    cantidad=models.PositiveIntegerField(default=1)
    notas=models.TextField(blank=True)
    subtotal=models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        if self.pizza_mitad2:
            return f"{self.cantidad}x {self.pizza.nombre} + {self.pizza_mitad2.nombre}"
        return f"{self.cantidad}x {self.pizza.nombre}"