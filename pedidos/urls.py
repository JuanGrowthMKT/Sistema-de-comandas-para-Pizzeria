from django.urls import path
from . import views

urlpatterns = [
    path('', views.pedidos, name='pedidos'),
    path('panel/', views.panel, name='panel'),
    path('entregar/<int:pedido_id>/', views.entregar, name='entregar'),
    path('cerrarCaja/', views.cerrarCaja, name='cerrarCaja'),
    path('abrir/', views.abrir, name='abrir'),
    path('ventas/', views.ventas, name='ventas'),
    path('dashboard/', views.dashboard, name='dashboard'),
]