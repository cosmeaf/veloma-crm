from django.urls import path
from api.views.millennium_view import MillenniumUploadView

urlpatterns = [
    path("millennium/upload/", MillenniumUploadView.as_view(), name="millennium-upload"),
]
