from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status

from api.serializers.millennium_serializer import MillenniumUploadSerializer
from api.utils.millennium.extractor_pdf import MillenniumExtractor


class MillenniumUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = MillenniumUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pdf_file = serializer.validated_data["pdf"]

        extractor = MillenniumExtractor(pdf_file)
        resultado = extractor.extract()

        if "erro" in resultado:
            return Response(resultado, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "mensagem": "Upload processado com sucesso.",
                "dados": resultado
            },
            status=status.HTTP_200_OK
        )
