"""Limitador de peticiones por IP.

Se aplica al inicio de sesión y a la recuperación de contraseña para frenar
ataques de fuerza bruta y el abuso del envío de correos.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
