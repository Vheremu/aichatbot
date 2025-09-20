from django.contrib import admin
from django.urls import path,include
from . import views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.chat_view, name='chat'),
    path('send_message/', views.send_message, name='send_message'),
]
