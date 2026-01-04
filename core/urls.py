"""
URL configuration for tutorcito project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.documents.viewsets import DocumentViewSet
from apps.documents.views import DocumentUploadView
from apps.users.viewsets import UserViewSet
from apps.users.views import get_current_user
from django.conf.urls.static import static
from django.conf import settings

router = DefaultRouter()
router.register("users", UserViewSet)
router.register("documents", DocumentViewSet, basename="document")

urlpatterns = (
    [
        path("admin/", admin.site.urls),
        path("", include("apps.docs.urls")),
        path("api/auth/me/", get_current_user, name="current-user"),
        path("api/", include("apps.exams.urls")),
        path(
            "api/documents/upload/",
            DocumentUploadView.as_view(),
            name="document-upload",
        ),
        path("api/", include(router.urls)),
    ]
    + router.urls
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
)
