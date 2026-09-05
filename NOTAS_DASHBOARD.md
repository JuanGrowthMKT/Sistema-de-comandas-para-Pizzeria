# Dashboard: cómo calcular "producto más vendido"

## Dos conceptos distintos

1. **Filtro por estado** (`entregado` / `cerrado`): no calcula nada, solo reduce el
   conjunto. Es el WHERE, va al inicio de la query:

   ```python
   DetallePedido.objects.filter(pedido__estado__in=['entregado', 'cerrado'])
   ```

2. **El cálculo**: "más vendido" es una agregación con `Sum`, no con `max` ni `count`.

   - `Count` cuenta líneas de detalle. Si hay `3x Margarita`, cuenta 1, pero vendiste 3.
   - `Sum('cantidad')` suma las unidades. Eso es lo que querés.

## Query completa

```python
from django.db.models import Sum

ranking = (
    DetallePedido.objects
    .filter(pedido__estado__in=['entregado', 'cerrado'])
    .values('pizza__nombre')
    .annotate(unidades=Sum('cantidad'))
    .order_by('-unidades')
)
mas_vendido = ranking.first()  # el "max": primero de la lista ordenada descendente
```

## Dos trampas de este modelo

1. **Mitad y mitad**: la query de arriba ignora `pizza_mitad2`. Un detalle mitad y
   mitad cuenta 1 unidad para cada media pizza (así lo hace el prototipo
   `contarProductos`). Solo `.values('pizza__nombre')` no suma la mitad 2.
   → Hay que sumar la mitad2 aparte (unión de querysets o resolver en Python).

2. **El período** (hoy/mes/año) agrega un filtro por fecha al WHERE, no al cálculo.

## Pregunta pendiente

¿Las unidades de mitad y mitad suman 1 a cada media (como el prototipo) o 0.5 a cada una?