from django.urls import path
from . import views

app_name = "app"

urlpatterns = [
    path("", views.upload_page, name="upload_page"),
]
