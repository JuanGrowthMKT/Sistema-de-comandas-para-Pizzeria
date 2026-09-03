from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST 
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Pizza, Pedido, DetallePedido, Jornada
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import Concat, Coalesce, TruncDate, TruncMonth

def jornada_activa():
    return Jornada.objects.filter(fin__isnull=True).first()

def jornada_context():
    return {'jornada': jornada_activa()}

@login_required
def abrir(request):
    # Abre la jornada de trabajo si no hay una abierta
    if request.method == 'POST':
        if not jornada_activa():
            Jornada.objects.create()
        return redirect('dashboard')
    return redirect('pedidos')

@login_required
def pedidos(request):
    # Maneja la creación de pedidos y la visualización de pizzas y pedidos pendientes
    jornada = jornada_activa()
    if request.method == 'POST':
        cliente = (request.POST.get('cliente') or '').strip()
        hora_entrega = request.POST.get('hora_entrega') or None

        import json as _json
        try:
            items = _json.loads(request.POST.get('items_json', '[]'))
        except Exception:
            items = []

        error = None
        # Recolecta items validando de antemano para no crear pedidos rotos
        total_pedido = 0
        detalle_items = []
        pizza_ids = set()
        for it in items:
            try:
                pizza_id = int(it.get('pizza'))
            except (TypeError, ValueError):
                continue
            try:
                cantidad = int(it.get('cantidad', 1) or 1)
            except (TypeError, ValueError):
                cantidad = 1
            if cantidad < 1:
                cantidad = 1
            notas = (it.get('notas') or '').strip()
            mitad = it.get('mitad_y_mitad')

            try:
                pizza2_id = int(it.get('mitad2')) if mitad and it.get('mitad2') else None
            except (TypeError, ValueError):
                pizza2_id = None

            pizza_ids.add(pizza_id)
            if pizza2_id:
                pizza_ids.add(pizza2_id)

            detalle_items.append({
                'pizza_id': pizza_id,
                'pizza2_id': pizza2_id,
                'cantidad': cantidad,
                'notas': notas,
                'mitad': bool(mitad),
            })

        if not cliente:
            error = 'Debes indicar el nombre del cliente.'
        elif not detalle_items:
            error = 'Debes agregar al menos una pizza.'
        else:
            validas = set(Pizza.objects.filter(id__in=pizza_ids).values_list('id', flat=True))
            invalidas = pizza_ids - validas
            if invalidas:
                error = 'Hay pizzas inválidas en el pedido.'

        if error:
            messages.error(request, error)
        else:
            total_pedido = 0
            creados = []
            for det in detalle_items:
                pizza1 = Pizza.objects.get(id=det['pizza_id'])
                pizza2 = Pizza.objects.get(id=det['pizza2_id']) if det['pizza2_id'] else None
                precio = (pizza1.precio + pizza2.precio) / 2 if pizza2 else pizza1.precio
                subtotal = precio * det['cantidad']
                total_pedido += subtotal
                creados.append({
                    'pizza': pizza1,
                    'pizza_mitad2': pizza2,
                    'cantidad': det['cantidad'],
                    'notas': det['notas'],
                    'subtotal': subtotal,
                })

            pedido = Pedido.objects.create(cliente=cliente, total=total_pedido, hora_entrega=hora_entrega, jornada=jornada)
            for det in creados:
                DetallePedido.objects.create(pedido=pedido, **det)
            messages.success(request, f'Comanda de {cliente} cargada correctamente.')

    # Obtiene las pizzas disponibles y los pedidos pendientes para mostrarlos en la plantilla
    pizzas = Pizza.objects.filter(disponible=True)
    pedidos = Pedido.objects.all().prefetch_related('detalles__pizza', 'detalles__pizza_mitad2').order_by('-fecha')
    pizzas_json = [        {
            'id': p.id,
            'nombre': p.nombre,
            'precio': float(p.precio),
            'precio_texto': f"{p.precio:,.0f}".replace(',', '.'),
        }
        for p in pizzas
    ]
    return render(request, 'pedidos/pedidos.html', {
        'pizzas': pizzas,
        'pizzas_json': pizzas_json,
        'pedidos': pedidos,
        'seccion': 'pedidos',
        'jornada': jornada,
    })
    

@require_POST
@login_required
def entregar(request, pedido_id):
    # Marca un pedido como entregado
        # Obtiene el pedido por su ID y cambia su estado a 'entregado'
        pedido = get_object_or_404(Pedido, id=pedido_id)
        pedido.estado = 'entregado'
        pedido.save()
        return redirect('panel')

@require_POST
@login_required
def cerrarCaja(request):
        jornada = jornada_activa()
        if jornada:
            total = int(Pedido.objects.filter(estado__in=['entregado', 'cerrado'], jornada=jornada).aggregate(Sum('total'))['total__sum'] or 0)
            jornada.total = total
            jornada.fin = timezone.now()
            jornada.save()
        Pedido.objects.filter(estado='entregado').update(estado='cerrado')
        return redirect('ventas')

@login_required
def panel(request):
    pedidos = list(Pedido.objects.filter(estado='pendiente').prefetch_related('detalles__pizza', 'detalles__pizza_mitad2'))
    pedidos.sort(key=lambda p: (p.hora_entrega or p.fecha.time(), p.fecha))
    contexto = {'pedidos': pedidos}
    if request.headers.get('HX-Request') == 'true':
        return render(request, 'pedidos/_cards.html', contexto)
    contexto['seccion'] = 'panel'
    contexto['jornada'] = jornada_activa()
    return render(request, 'pedidos/panelpedidos.html', contexto)

@login_required
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
        'jornada': jornada_activa(),
    })

@login_required
def dashboard(request):
    jornada = jornada_activa()

    temporalidad=request.GET.get('periodo', 'dia')
    if temporalidad=='dia':
        # Día = la jornada de trabajo (la abierta, o la última cerrada)
        ultima = Jornada.objects.filter(fin__isnull=False).order_by('-fin').first()
        jornada_dia = jornada or ultima
        if jornada_dia:
            consulta_pedidos=Pedido.objects.filter(estado__in=['entregado', 'cerrado'], jornada=jornada_dia)
            apertura = jornada_dia.inicio
        else:
            consulta_pedidos = Pedido.objects.none()
            apertura = timezone.now()
        total_temporalidad=consulta_pedidos.aggregate(Sum('total'))['total__sum'] or 0
        cantidad_pedidos=consulta_pedidos.count()
        ticket_promedio=(total_temporalidad/cantidad_pedidos) if cantidad_pedidos > 0 else 0
        ranking = analizar_productos_por_jornada(jornada_dia)

    elif temporalidad == 'mes':
        hora = timezone.localtime()
        desde = hora.replace(day=1)
        consulta_pedidos=Pedido.objects.filter(estado__in=['entregado', 'cerrado'], fecha__gte=desde)
        total_temporalidad=consulta_pedidos.aggregate(Sum('total'))['total__sum'] or 0
        cantidad_pedidos=consulta_pedidos.count()
        ticket_promedio=(total_temporalidad/cantidad_pedidos) if cantidad_pedidos > 0 else 0
        ranking = analizar_productos_por_fecha(desde)

    else:
        hora = timezone.localtime()
        desde = hora.replace(month=1, day=1)
        consulta_pedidos=Pedido.objects.filter(estado__in=['entregado', 'cerrado'], fecha__gte=desde)
        total_temporalidad=consulta_pedidos.aggregate(Sum('total'))['total__sum'] or 0
        cantidad_pedidos=consulta_pedidos.count()
        ticket_promedio=(total_temporalidad/cantidad_pedidos) if cantidad_pedidos > 0 else 0   
        ranking = analizar_productos_por_fecha(desde)

    if temporalidad == 'dia':
        resumen = [{'fecha': apertura, 'total': total_temporalidad}]
        periodo_texto = 'Jornada'
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
            'jornada': jornada,
        })

def analizar_productos_por_jornada(jornada):
    detalles = DetallePedido.objects.filter(
    pedido__estado__in=['entregado', 'cerrado'],
    pedido__jornada=jornada
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

def analizar_productos_por_fecha(desde):
    detalles = DetallePedido.objects.filter(
    pedido__estado__in=['entregado', 'cerrado'],
    pedido__fecha__gte=desde
    )

    productos_vendidos = {}
    for detalle in detalles:
        if detalle.pizza_mitad2:
            nombre = f"{detalle.pizza.nombre} + {detalle.pizza_mitad2.nombre}"
        else:
            nombre = detalle.pizza.nombre

        if nombre in productos_vendidos:
            productos_vendidos[nombre] += detalle.cantidad
        else:
            productos_vendidos[nombre] = detalle.cantidad

    if productos_vendidos:
        mas_vendido = max(productos_vendidos, key=productos_vendidos.get)
        menos_vendido = min(productos_vendidos, key=productos_vendidos.get)
    else:
        mas_vendido = '—'
        menos_vendido = '—'

    top_3 = sorted(productos_vendidos.items(), key=lambda x: x[1], reverse=True)[:3]

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
    

