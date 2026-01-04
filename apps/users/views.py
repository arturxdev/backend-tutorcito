from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """Retorna información del usuario actual y crea el registro si no existe"""
    user = request.user
    return Response(
        {
            "id": user.id,
            "supabase_id": str(user.supabase_id),
            "email": user.email,
        }
    )
