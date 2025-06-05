from apps.authentication.endpoints.auth import urlpatterns as auth_urls
from apps.authentication.endpoints.user import urlpatterns as user_urls
from apps.authentication.endpoints.profile import urlpatterns as profile_urls
from apps.authentication.endpoints.admin import urlpatterns as admin_urls

app_name = 'authentication'
urlpatterns = []
urlpatterns += auth_urls
urlpatterns += user_urls
urlpatterns += profile_urls
urlpatterns += admin_urls
