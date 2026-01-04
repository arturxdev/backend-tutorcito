from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from jose import jwt
from jose.exceptions import JWTError
import requests
from django.conf import settings
from django.core.cache import cache
from apps.users.models import User
import logging

logger = logging.getLogger(__name__)


class SupabaseJWTAuthentication(BaseAuthentication):
    """
    Autenticación usando JWT de Supabase con validación JWKS
    """

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")

        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]

        try:
            # Obtener JWKS (con cache para evitar requests repetidos)
            jwks = self.get_jwks()

            # Validar y decodificar token
            payload = jwt.decode(
                token,
                jwks,
                algorithms=["RS256"],
                issuer=f"{settings.SUPABASE_PROJECT_URL}/auth/v1",
                audience="authenticated",
            )

            # Extraer user_id (sub) y email
            supabase_user_id = payload.get("sub")
            email = payload.get("email", "")

            if not supabase_user_id:
                raise AuthenticationFailed("Token inválido: falta sub")

            # Buscar o crear usuario en DB local
            user, created = User.objects.get_or_create(
                supabase_id=supabase_user_id, defaults={"email": email}
            )

            if created:
                logger.info(f"Nuevo usuario creado: {email} ({supabase_user_id})")

            # Actualizar email si cambió
            if user.email != email:
                user.email = email
                user.save(update_fields=["email", "updated_at"])

            return (user, token)

        except JWTError as e:
            logger.error(f"Error validando JWT: {e}")
            raise AuthenticationFailed("Token inválido o expirado")

    def get_jwks(self):
        """
        Obtiene JWKS desde Supabase (con cache de 1 hora)
        """
        cache_key = "supabase_jwks"
        jwks = cache.get(cache_key)

        if jwks is None:
            jwks_url = f"{settings.SUPABASE_PROJECT_URL}/auth/v1/.well-known/jwks.json"
            try:
                response = requests.get(jwks_url, timeout=5)
                response.raise_for_status()
                jwks = response.json()

                # Cache por 1 hora (las claves casi nunca cambian)
                cache.set(cache_key, jwks, 3600)
                logger.info(f"JWKS actualizado desde {jwks_url}")
            except requests.RequestException as e:
                logger.error(f"Error obteniendo JWKS: {e}")
                raise AuthenticationFailed(
                    "Error conectando con servidor de autenticación"
                )

        return jwks
