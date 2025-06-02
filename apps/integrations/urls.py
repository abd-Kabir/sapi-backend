from apps.integrations.endpoints.firebase import urlpatterns as fcm_urls
from apps.integrations.endpoints.multibank import urlpatterns as multibank_urls

app_name = 'integrations'
urlpatterns = []
urlpatterns += fcm_urls
urlpatterns += multibank_urls
