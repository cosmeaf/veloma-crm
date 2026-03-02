# converter/urls.py
from rest_framework.routers import DefaultRouter

from converter.views.file_viewset import ConverterFileViewSet
from converter.views.millenium_viewset import (
    MilleniumUploadViewSet,
    MilleniumExtractViewSet,
)
from converter.views.bradesco_viewset import BradescoUploadViewSet

router = DefaultRouter()

# Registros com prefixos relativos (sem o /converter/ aqui)
router.register(r"files", ConverterFileViewSet, basename="converter-files")
router.register(r"millenium/upload", MilleniumUploadViewSet, basename="millenium-upload")
router.register(r"millenium/extract", MilleniumExtractViewSet, basename="millenium-extract")
router.register(r"bradesco/upload", BradescoUploadViewSet, basename="bradesco-upload")

# Exporta as URLs do router
urlpatterns = router.urls