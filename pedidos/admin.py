from django.contrib import admin
from .models import Pizza, Pedido, DetallePedido

@admin.register(Pizza)
class PizzaAdmin(admin.ModelAdmin):
    list_display=('nombre', 'precio', 'disponible')

class DetalleInline(admin.TabularInline):
    model=DetallePedido
    extra=1 

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display=('id', 'cliente', 'estado', 'fecha', 'total')
    list_filter=('estado',)
    inlines = [DetalleInline]
