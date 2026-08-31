# Sistema Il Forno

Sistema web de gestión de pedidos para pizzería, construido con **Django** (server-rendered) y **Bootstrap 5**.

## Funcionalidades

- **Registro de pedidos** de pizzas, con opción a mitad y mitad.
- **Panel de pedidos** en vivo: las tarjetas se actualizan automáticamente cada 1.5s vía **HTMX**, pensado para verse en una TV en la cocina.
- Estados de pedido: **pendiente** / **entregado**, con botón de entrega directo desde el panel.
- Diseño responsive con tarjetas cuadradas (col-12 col-sm-6 col-lg-4 col-xxl-3).

## Stack

- Python / Django 5.2
- Bootstrap 5.3
- HTMX 2 (solo para la vista del panel)
- SQLite

## Cómo correrlo

```bash
python -m venv venv
venv\Scripts\activate
pip install django

python manage.py migrate
python manage.py runserver 0.0.0.0:8011
```

Abrir `http://localhost:8011/` (o la IP local del PC desde otro dispositivo en la misma red).
