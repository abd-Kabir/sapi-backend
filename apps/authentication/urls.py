from apps.authentication.endpoints.auth import urlpatterns as auth_urls
from apps.authentication.endpoints.user import urlpatterns as user_urls

app_name = 'authentication'
urlpatterns = []
urlpatterns += auth_urls
urlpatterns += user_urls
