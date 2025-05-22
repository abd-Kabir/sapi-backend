from apps.integrations.endpoints.firebase import urlpatterns as fcm_urls

app_name = 'integrations'
urlpatterns = []
urlpatterns += fcm_urls
