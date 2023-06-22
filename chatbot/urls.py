from django.contrib import admin
from django.urls import path,include

admin.site.site_header = "M-BOT Admin"
admin.site.site_title = "M-BOT Admin Portal"
admin.site.index_title = "Welcome to M-BOT Researcher Portal"
urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('app.urls')),
]