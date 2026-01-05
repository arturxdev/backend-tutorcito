from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import jwt
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError
from django.conf import settings
from django.core.cache import cache
from apps.users.models import User
import logging

logger = logging.getLogger(__name__)


class ClerkJWTAuthentication(BaseAuthentication):
    """
    Autenticación usando JWT de Clerk
    """

    def authenticate(self, request):
        logger.info("=" * 60)
        logger.info("🔐 [AUTH] Starting Clerk JWT authentication")

        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        logger.info(f"🔐 [AUTH] Auth header present: {bool(auth_header)}")

        if not auth_header.startswith("Bearer "):
            logger.warning("⚠️  [AUTH] No Bearer token found in Authorization header")
            return None

        token = auth_header.split(" ")[1]
        logger.info(f"🔐 [AUTH] Token length: {len(token)} characters")

        try:
            # Clerk uses RS256 algorithm with JWKS
            jwks_url = settings.CLERK_JWKS_URL
            logger.info(f"🔐 [AUTH] JWKS URL: {jwks_url}")

            # Use PyJWKClient which handles JWKS key selection automatically
            jwks_client = PyJWKClient(jwks_url, cache_keys=True)

            logger.info("🔐 [AUTH] Getting signing key from JWKS...")
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            logger.info(f"✅ [AUTH] Signing key obtained: {signing_key.key_id}")

            logger.info("🔐 [AUTH] Decoding token with signing key...")
            # Clerk tokens don't require audience validation by default
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={"verify_aud": False},
            )

            logger.info("✅ [AUTH] Token validation successful!")

            # Extraer clerk_user_id (sub) y email
            clerk_user_id = payload.get("sub")
            email = payload.get("email", "")

            logger.info(f"✅ [AUTH] Clerk User ID (sub): {clerk_user_id}")
            logger.info(f"✅ [AUTH] Email: {email}")

            if not clerk_user_id:
                logger.error("❌ [AUTH] Token missing 'sub' claim")
                raise AuthenticationFailed("Token inválido: falta sub")

            # Buscar o crear usuario en DB local
            logger.info(f"🔐 [AUTH] Looking up user with clerk_id: {clerk_user_id}")
            user, created = User.objects.get_or_create(
                clerk_id=clerk_user_id, defaults={"email": email}
            )

            if created:
                logger.info(f"✅ [AUTH] New user created: {email} ({clerk_user_id})")
            else:
                logger.info(
                    f"✅ [AUTH] Existing user found: {email} (DB ID: {user.id})"
                )

            # Actualizar email si cambió
            if user.email != email:
                logger.info(
                    f"🔐 [AUTH] Updating user email from '{user.email}' to '{email}'"
                )
                user.email = email
                user.save(update_fields=["email", "updated_at"])

            logger.info(f"✅ [AUTH] Authentication complete for user ID: {user.id}")
            logger.info("=" * 60)
            return (user, token)

        except InvalidTokenError as e:
            logger.error("❌ [AUTH] JWT validation failed")
            logger.error(f"❌ [AUTH] Error type: {type(e).__name__}")
            logger.error(f"❌ [AUTH] Error message: {str(e)}")
            logger.info("=" * 60)
            raise AuthenticationFailed("Token inválido o expirado")
        except Exception as e:
            logger.error("❌ [AUTH] Unexpected error during authentication")
            logger.error(f"❌ [AUTH] Error type: {type(e).__name__}")
            logger.error(f"❌ [AUTH] Error message: {str(e)}")
            logger.info("=" * 60)
            raise AuthenticationFailed("Error de autenticación")


class SupabaseJWTAuthentication(BaseAuthentication):
    """
    Autenticación usando JWT de Supabase con soporte híbrido para ES256 y HS256
    """

    def authenticate(self, request):
        logger.info("=" * 60)
        logger.info("🔐 [AUTH] Starting JWT authentication")

        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        logger.info(f"🔐 [AUTH] Auth header present: {bool(auth_header)}")
        logger.info(
            f"🔐 [AUTH] Auth header starts with 'Bearer ': {auth_header.startswith('Bearer ')}"
        )

        if not auth_header.startswith("Bearer "):
            logger.warning("⚠️  [AUTH] No Bearer token found in Authorization header")
            return None

        token = auth_header.split(" ")[1]
        logger.info(f"🔐 [AUTH] Token length: {len(token)} characters")

        # Decode header WITHOUT validation to see algorithm
        try:
            unverified_header = jwt.get_unverified_header(token)
            alg = unverified_header.get("alg")
            kid = unverified_header.get("kid")

            logger.info(f"🔐 [AUTH] Token algorithm: {alg}")
            logger.info(f"🔐 [AUTH] Token key ID: {kid}")
            logger.info(f"🔐 [AUTH] Token type: {unverified_header.get('typ')}")
            logger.info(f"🔐 [AUTH] Full token header: {unverified_header}")
        except Exception as e:
            logger.error(f"❌ [AUTH] Failed to decode token header: {e}")
            raise AuthenticationFailed("Token inválido")

        # Determine validation method based on algorithm
        try:
            if alg == "HS256":
                logger.info("🔐 [AUTH] Using HS256 validation (legacy symmetric key)")
                payload = self._validate_hs256(token)
            elif alg in ["ES256", "RS256"]:
                logger.info(f"🔐 [AUTH] Using {alg} validation (asymmetric JWKS)")
                payload = self._validate_jwks(token, alg, kid)
            else:
                logger.error(f"❌ [AUTH] Unsupported algorithm: {alg}")
                raise AuthenticationFailed(f"Algoritmo no soportado: {alg}")

            logger.info("✅ [AUTH] Token validation successful!")

            # Extraer user_id (sub) y email
            supabase_user_id = payload.get("sub")
            email = payload.get("email", "")

            logger.info(f"✅ [AUTH] User ID (sub): {supabase_user_id}")
            logger.info(f"✅ [AUTH] Email: {email}")
            logger.info(f"✅ [AUTH] Token issuer: {payload.get('iss')}")
            logger.info(f"✅ [AUTH] Token audience: {payload.get('aud')}")

            if not supabase_user_id:
                logger.error("❌ [AUTH] Token missing 'sub' claim")
                raise AuthenticationFailed("Token inválido: falta sub")

            # Buscar o crear usuario en DB local
            logger.info(
                f"🔐 [AUTH] Looking up user with supabase_id: {supabase_user_id}"
            )
            user, created = User.objects.get_or_create(
                supabase_id=supabase_user_id, defaults={"email": email}
            )

            if created:
                logger.info(f"✅ [AUTH] New user created: {email} ({supabase_user_id})")
            else:
                logger.info(
                    f"✅ [AUTH] Existing user found: {email} (DB ID: {user.id})"
                )

            # Actualizar email si cambió
            if user.email != email:
                logger.info(
                    f"🔐 [AUTH] Updating user email from '{user.email}' to '{email}'"
                )
                user.email = email
                user.save(update_fields=["email", "updated_at"])

            logger.info(f"✅ [AUTH] Authentication complete for user ID: {user.id}")
            logger.info("=" * 60)
            return (user, token)

        except InvalidTokenError as e:
            logger.error("❌ [AUTH] JWT validation failed")
            logger.error(f"❌ [AUTH] Error type: {type(e).__name__}")
            logger.error(f"❌ [AUTH] Error message: {str(e)}")
            logger.error(f"❌ [AUTH] Full error: {repr(e)}")
            logger.info("=" * 60)
            raise AuthenticationFailed("Token inválido o expirado")
        except Exception as e:
            logger.error("❌ [AUTH] Unexpected error during authentication")
            logger.error(f"❌ [AUTH] Error type: {type(e).__name__}")
            logger.error(f"❌ [AUTH] Error message: {str(e)}")
            logger.error(f"❌ [AUTH] Full error: {repr(e)}")
            logger.info("=" * 60)
            raise AuthenticationFailed("Error de autenticación")

    def _validate_hs256(self, token):
        """
        Valida token usando HS256 con JWT secret (método legacy)
        """
        logger.info(
            f"🔐 [AUTH] JWT Secret loaded: {bool(settings.SUPABASE_JWT_SECRET)}"
        )
        logger.info(
            f"🔐 [AUTH] JWT Secret length: {len(settings.SUPABASE_JWT_SECRET)} characters"
        )
        logger.info(
            f"🔐 [AUTH] Expected issuer: {settings.SUPABASE_PROJECT_URL}/auth/v1"
        )
        logger.info(f"🔐 [AUTH] Expected audience: authenticated")

        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            issuer=f"{settings.SUPABASE_PROJECT_URL}/auth/v1",
            audience="authenticated",
        )

        return payload

    def _validate_jwks(self, token, algorithm, kid):
        """
        Valida token usando JWKS con PyJWT (para ES256 y RS256)
        """
        jwks_url = f"{settings.SUPABASE_PROJECT_URL}/auth/v1/.well-known/jwks.json"
        logger.info(f"🔐 [AUTH] JWKS URL: {jwks_url}")
        logger.info(f"🔐 [AUTH] Token algorithm: {algorithm}")
        logger.info(f"🔐 [AUTH] Token key ID: {kid}")
        logger.info(
            f"🔐 [AUTH] Expected issuer: {settings.SUPABASE_PROJECT_URL}/auth/v1"
        )
        logger.info(f"🔐 [AUTH] Expected audience: authenticated")

        # Use PyJWKClient which handles JWKS key selection automatically
        jwks_client = PyJWKClient(jwks_url, cache_keys=True)

        logger.info("🔐 [AUTH] Getting signing key from JWKS...")
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        logger.info(f"✅ [AUTH] Signing key obtained: {signing_key.key_id}")

        logger.info("🔐 [AUTH] Decoding token with signing key...")
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=[algorithm],
            issuer=f"{settings.SUPABASE_PROJECT_URL}/auth/v1",
            audience="authenticated",
        )

        logger.info("✅ [AUTH] Token decoded successfully")
        return payload
