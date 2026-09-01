from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST 
from .models import Pizza, Pedido, DetallePedido
from django.db.models import Sum

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
    return render(request, 'pedidos/dashboard.html', {
        'seccion': 'dashboard',
    })