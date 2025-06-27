from django.contrib import admin
from django.urls import path, include

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated

from config.views import MediaPath

schema_view = get_schema_view(
    openapi.Info(
        title="SAPI Swagger",
        default_version='v1',
        description="Swagger foy SAPI project, token authorization: user __/auth/token/__ API "
                    "then click authorize button and type __Bearer {token}__.",
        terms_of_service="https://sapi.com/",
        contact=openapi.Contact(email="help@sapi.com"),
        license=openapi.License(name="SAPI License"),
    ),
    public=True,
    permission_classes=[IsAuthenticated, ],
    authentication_classes=[BasicAuthentication],
)

urlpatterns = [
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),

    path('control-panel/', admin.site.urls),
    path('', include('apps.authentication.urls')),
    path('files/', include('apps.files.urls')),
    path('content/', include('apps.content.urls')),
    path('chat/', include('apps.chat.urls')),
    path('api/', include('apps.integrations.urls')),

    path('media/<path:path>', MediaPath.as_view(), name='serve_private_file'),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
