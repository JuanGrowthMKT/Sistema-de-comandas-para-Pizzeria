from django.urls import path
from . import views

urlpatterns = [
    path('', views.pedidos, name='pedidos'),
    path('panel/', views.panel, name='panel'),
    path('entregar/<int:pedido_id>/', views.entregar, name='entregar'),
    path('limpiar', views.limpiar, name='limpiar'),
]