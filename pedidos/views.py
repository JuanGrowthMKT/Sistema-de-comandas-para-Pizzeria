from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST 
from .models import Pizza, Pedido, DetallePedido
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import Concat, Coalesce, TruncDate, TruncMonth

def pedidos(request):
    # Maneja la creación de pedidos y la visualización de pizzas y pedidos pendientes
    if request.method == 'POST':
        cliente = request.POST.get('cliente')
        cantidad = int(request.POST.get('cantidad', 1) or 1)
        notas = request.POST.get('notas', '')
        # Determina si el pedido es mitad y mitad
        mitad_y_mitad = request.POST.get('mitad_y_mitad') == 'on'

        # Calcula el precio según si es mitad y mitad o no
        if mitad_y_mitad:
            pizza1 = get_object_or_404(Pizza, id=request.POST.get('mitad1'))
            pizza2 = get_object_or_404(Pizza, id=request.POST.get('mitad2'))
            precio = (pizza1.precio + pizza2.precio) / 2   # promedio, como tu prototipo
        else:
            pizza1 = get_object_or_404(Pizza, id=request.POST.get('pizza'))
            pizza2 = None
            precio = pizza1.precio

        # Calcula el subtotal
        subtotal = precio * cantidad

        # Crea el pedido y el detalle del pedido
        pedido = Pedido.objects.create(cliente=cliente, total=subtotal)
        DetallePedido.objects.create(
            pedido=pedido,
            pizza=pizza1,
            pizza_mitad2=pizza2,
            cantidad=cantidad,
            notas=notas,
            subtotal=subtotal
        )

    # Obtiene las pizzas disponibles y los pedidos pendientes para mostrarlos en la plantilla
    pizzas = Pizza.objects.filter(disponible=True)
    pedidos = Pedido.objects.all().prefetch_related('detalles__pizza', 'detalles__pizza_mitad2').order_by('-fecha')
    return render(request, 'pedidos/pedidos.html', {
        'pizzas': pizzas,
        'pedidos': pedidos,
        'seccion': 'pedidos',
    })
    

@require_POST
def entregar(request, pedido_id):
    # Marca un pedido como entregado
        # Obtiene el pedido por su ID y cambia su estado a 'entregado'
        pedido = get_object_or_404(Pedido, id=pedido_id)
        pedido.estado = 'entregado'
        pedido.save()
        return redirect('panel')

@require_POST
def cerrarCaja(request):
        Pedido.objects.filter(estado='entregado').update(estado='cerrado')
        return redirect('ventas')

def panel(request):
    pedidos = list(Pedido.objects.filter(estado='pendiente').prefetch_related('detalles__pizza', 'detalles__pizza_mitad2'))
    pedidos.sort(key=lambda p: (0 if p.estado == 'pendiente' else 1, p.fecha))
    contexto = {'pedidos': pedidos}
    if request.headers.get('HX-Request') == 'true':
        return render(request, 'pedidos/_cards.html', contexto)
    contexto['seccion'] = 'panel'
    return render(request, 'pedidos/panelpedidos.html', contexto)

def ventas(request):
   pendientes = Pedido.objects.filter(estado='pendiente').count()
   entregados = Pedido.objects.filter(estado='entregado').count()
   total=int(Pedido.objects.filter(estado='entregado').aggregate(Sum('total'))['total__sum'] or 0)

   estado=request.GET.get('estado')
   pedidos=Pedido.objects.all()
   if estado:
        pedidos= pedidos.filter(estado=estado)

   return render(request,'pedidos/ventas.html', {
        'pendientes':pendientes,
        'entregados':entregados,
        'total':total,
        'seccion':'ventas',
        'pedidos':pedidos,
        'estado_actual': estado or 'todos',
   })

def dashboard(request):
    hora=timezone.now()
    if hora.hour >=15:
         apertura=hora.replace(hour=15, minute=0, second=0, microsecond=0)
    else:
         apertura = (hora - timedelta(days=1)).replace(hour=15, minute=0, second=0, microsecond=0)

    temporalidad=request.GET.get('periodo', 'dia')
    if temporalidad=='dia':
         consulta_pedidos=Pedido.objects.filter(estado__in=['entregado', 'cerrado'], fecha__gte=apertura)
         total_temporalidad=consulta_pedidos.aggregate(Sum('total'))['total__sum'] or 0
         cantidad_pedidos=consulta_pedidos.count()
         ticket_promedio=(total_temporalidad/cantidad_pedidos) if cantidad_pedidos > 0 else 0
         ranking = analizar_productos_vendidos(apertura)

    elif temporalidad == 'mes':
        desde = hora.replace(day=1, hour=15, minute=0, second=0, microsecond=0)
        consulta_pedidos=Pedido.objects.filter(estado__in=['entregado', 'cerrado'], fecha__gte=desde)
        total_temporalidad=consulta_pedidos.aggregate(Sum('total'))['total__sum'] or 0
        cantidad_pedidos=consulta_pedidos.count()
        ticket_promedio=(total_temporalidad/cantidad_pedidos) if cantidad_pedidos > 0 else 0
        ranking = analizar_productos_vendidos(desde)

    else:
        desde = hora.replace(month=1, day=1, hour=15, minute=0, second=0, microsecond=0)
        consulta_pedidos=Pedido.objects.filter(estado__in=['entregado', 'cerrado'], fecha__gte=desde)
        total_temporalidad=consulta_pedidos.aggregate(Sum('total'))['total__sum'] or 0
        cantidad_pedidos=consulta_pedidos.count()
        ticket_promedio=(total_temporalidad/cantidad_pedidos) if cantidad_pedidos > 0 else 0   
        ranking = analizar_productos_vendidos(desde)

    if temporalidad == 'dia':
        resumen = [{'fecha': apertura, 'total': total_temporalidad}]
        periodo_texto = 'Hoy'
    elif temporalidad == 'mes':
        resumen = list(
            consulta_pedidos.annotate(diagrupo=TruncDate('fecha'))
            .values('diagrupo')
            .annotate(total=Sum('total'))
            .order_by('diagrupo')
        )
        periodo_texto = hora.strftime('%B %Y').capitalize()
    else:
        resumen = list(
            consulta_pedidos.annotate(mesgrupo=TruncMonth('fecha'))
            .values('mesgrupo')
            .annotate(total=Sum('total'))
            .order_by('mesgrupo')
        )
        periodo_texto = 'Año ' + str(hora.year)

    return render(request, 'pedidos/dashboard.html', {
            'seccion': 'dashboard',
            'ingresos':total_temporalidad,
            'periodo':temporalidad,
            'periodo_texto':periodo_texto,
            'resumen':resumen,
            'ticket_promedio':ticket_promedio,
            'mas_vendido': ranking['mas_vendido'],
            'menos_vendido': ranking['menos_vendido'],
            'top3': ranking['top3'],
            'top_dias': ranking['top_dias'],
        })

def analizar_productos_vendidos(apertura):
    detalles = DetallePedido.objects.filter(
    pedido__estado__in=['entregado', 'cerrado'],
    pedido__fecha__gte=apertura
    )

    # 2. Agrupar en un diccionario
    productos_vendidos = {}
    for detalle in detalles:
    # Construir el nombre de la combinación
        if detalle.pizza_mitad2:
            nombre = f"{detalle.pizza.nombre} + {detalle.pizza_mitad2.nombre}"
        else:
            nombre = detalle.pizza.nombre

        if nombre in productos_vendidos:
         productos_vendidos[nombre] += detalle.cantidad
        else:
         productos_vendidos[nombre] = detalle.cantidad

# 3. Sacar el más y menos vendido
    if productos_vendidos:
        mas_vendido = max(productos_vendidos, key=productos_vendidos.get)
        menos_vendido = min(productos_vendidos, key=productos_vendidos.get)
    else:
        mas_vendido = '—'
        menos_vendido = '—'

    top_3=sorted(productos_vendidos.items(), key=lambda x: x[1], reverse=True)[:3]

    # 4. Top 3 días históricos con más ventas (sin filtro de periodo = histórico completo)
    top_dias = list(
        Pedido.objects
        .filter(estado__in=['entregado', 'cerrado'])
        .annotate(dia=TruncDate('fecha'))
        .values('dia')
        .annotate(total_dia=Sum('total'))
        .order_by('-total_dia')[:3]
    )

    return {
                'mas_vendido':mas_vendido,
                'menos_vendido':menos_vendido,
                'top3': top_3,
                'top_dias': top_dias,
            }
    

