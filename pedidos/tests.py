import json

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from pedidos.models import Pizza, Pedido, Jornada


class BaseTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='pass1234', is_staff=True, is_superuser=True)
        self.p1 = Pizza.objects.create(nombre='Pepperoni', precio=45000)
        self.p2 = Pizza.objects.create(nombre='Mozzarella', precio=45000)
        self.c = Client()

    def login(self):
        self.c.login(username='admin', password='pass1234')


class LoginRequeridoTest(BaseTestCase):
    def test_pedidos_requiere_login(self):
        r = self.c.get('/')
        self.assertEqual(r.status_code, 302)
        self.assertIn('/login/', r.get('Location', ''))

    def test_panel_requiere_login(self):
        r = self.c.get('/panel/')
        self.assertEqual(r.status_code, 302)


class CrearPedidoTest(BaseTestCase):
    def test_comanda_multiple_items(self):
        self.login()
        Jornada.objects.create()
        data = {
            'cliente': 'Maria',
            'hora_entrega': '20:00',
            'items_json': json.dumps([
                {'pizza': self.p1.id, 'cantidad': 2},
                {'pizza': self.p2.id, 'cantidad': 1, 'mitad_y_mitad': False},
            ]),
        }
        r = self.c.post('/', data)
        self.assertEqual(r.status_code, 200)
        pedido = Pedido.objects.get(cliente='Maria')
        self.assertEqual(pedido.detalles.count(), 2)
        self.assertEqual(int(pedido.total), 135000)

    def test_pedido_sin_items_se_rechaza(self):
        self.login()
        Jornada.objects.create()
        antes = Pedido.objects.count()
        self.c.post('/', {'cliente': 'X', 'items_json': '[]'})
        self.assertEqual(Pedido.objects.count(), antes)

    def test_pedido_sin_cliente_se_rechaza(self):
        self.login()
        Jornada.objects.create()
        antes = Pedido.objects.count()
        self.c.post('/', {'cliente': '', 'items_json': json.dumps([{'pizza': self.p1.id}])})
        self.assertEqual(Pedido.objects.count(), antes)

    def test_pizza_invalida_se_rechaza_sin_404(self):
        self.login()
        Jornada.objects.create()
        antes = Pedido.objects.count()
        r = self.c.post('/', {'cliente': 'X', 'items_json': json.dumps([{'pizza': 99999}])})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Pedido.objects.count(), antes)


class JornadaTest(BaseTestCase):
    def test_cerrar_caja_archiva_jornada(self):
        self.login()
        j = Jornada.objects.create()
        self.c.post('/', {'cliente': 'A', 'items_json': json.dumps([{'pizza': self.p1.id}])})
        self.c.post(reverse('cerrarCaja'))
        j.refresh_from_db()
        self.assertIsNotNone(j.fin)
