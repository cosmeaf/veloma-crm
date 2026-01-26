from rest_framework.routers import DefaultRouter
from converter.views.file_viewset import ConverterFileViewSet
from converter.views.millenium_viewset import MilleniumUploadViewSet
from converter.views.bradesco_viewset import BradescoUploadViewSet

router = DefaultRouter()
router.register(r"files", ConverterFileViewSet, basename="converter-files")
router.register(r"millenium/upload", MilleniumUploadViewSet, basename="millenium-upload")
router.register(r"bradesco/upload", BradescoUploadViewSet, basename="bradesco-upload")

urlpatterns = router.urls
