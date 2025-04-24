from apps.authentication.endpoints.auth import urlpatterns as auth_urls

app_name = 'authentication'
urlpatterns = []
urlpatterns += auth_urls
