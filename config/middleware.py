import time

from django.core.cache import cache

MAX_ATTEMPTS = 5
WINDOW_SECONDS = 300
LOCKOUT_SECONDS = 600


class LoginThrottleMiddleware:
    """Limita los intentos fallidos de login por IP para frenar fuerza bruta."""

    def __init__(self, get_response):
        self.get_response = get_response

    def _client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')

    def __call__(self, request):
        if request.method == 'POST' and request.path.rstrip('/').endswith('/login'):
            ip = self._client_ip(request)
            key_attempts = f'login_attempts_{ip}'
            key_locked = f'login_locked_{ip}'

            if cache.get(key_locked):
                import logging
                logging.getLogger('django.security').warning(
                    'Login bloqueado por fuerza bruta (IP %s)', ip)
                # tiempo restante usando el timestamp guardado
                locked_at = cache.get(key_locked) or time.time()
                remaining = LOCKOUT_SECONDS - int(time.time() - locked_at)
                return self._blocked_response(remaining)

            response = self.get_response(request)

            # usuario autenticado correctamente => limpia contadores
            user = getattr(request, 'user', None)
            if user and user.is_authenticated:
                cache.delete(key_attempts)
                return response

            # intento fallido => incrementa
            attempts = cache.get(key_attempts, 0) + 1
            cache.set(key_attempts, attempts, timeout=WINDOW_SECONDS)
            if attempts >= MAX_ATTEMPTS:
                cache.set(key_locked, time.time(), timeout=LOCKOUT_SECONDS)
                cache.delete(key_attempts)
                return self._blocked_response(LOCKOUT_SECONDS)

            return response

        return self.get_response(request)

    def _blocked_response(self, remaining_seconds):
        from django.http import HttpResponseForbidden
        minutes = max(1, int(remaining_seconds // 60))
        return HttpResponseForbidden(
            f'Demasiados intentos. Intentalo de nuevo en {minutes} minuto(s).'
        )
