import logging
import os
from pathlib import Path

from django.db import transaction
from django.http import FileResponse, Http404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.permissions import IsStaffOrAdmin
from converter.models.millenium_model import MilleniumFile, MilleniumExtraction
from converter.serializers.millenium_serializers import (
    MilleniumFileSerializer,
    MilleniumFileSerializerDetails,
    MilleniumExtractionSerializer,
)
from converter.services.millenium_extractor import MilleniumExtractor

logger = logging.getLogger(__name__)


class MilleniumUploadViewSet(ModelViewSet):
    """ViewSet para upload de arquivos PDF do Millennium."""

    queryset = MilleniumFile.objects.all().order_by("-created_at")
    permission_classes = [IsStaffOrAdmin]

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return MilleniumFileSerializerDetails
        return MilleniumFileSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if MilleniumFile.objects.exists():
            logger.warning(
                "Usuário %s substituiu PDF anterior. Registros apagados: %s",
                request.user,
                MilleniumFile.objects.count()
            )
            MilleniumFile.objects.all().delete()

        millenium_file = MilleniumFile.objects.create(
            file=serializer.validated_data["file"],
            uploaded_by=request.user,
        )

        out_data = MilleniumFileSerializerDetails(
            millenium_file,
            context={"request": request}
        ).data

        return Response(
            {
                "ok": True,
                "bank": "millenium",
                "data": out_data
            },
            status=status.HTTP_201_CREATED
        )


class MilleniumExtractViewSet(ModelViewSet):
    """ViewSet para extração de dados e download do Millennium."""

    queryset = MilleniumExtraction.objects.all().order_by("-created_at")
    serializer_class = MilleniumExtractionSerializer
    permission_classes = [IsStaffOrAdmin]
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        extractor = MilleniumExtractor(bank_name="millenium")

        try:
            output_path = extractor.run()

            if not output_path.exists():
                raise FileNotFoundError(f"Arquivo não foi gerado: {output_path}")

        except Exception as exc:
            logger.exception("Falha durante extração Millennium")
            return Response(
                {
                    "ok": False,
                    "bank": "millenium",
                    "error": str(exc),
                    "detail": "Erro ao processar extração."
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        extraction = MilleniumExtraction.objects.create(
            uuid=extractor.job_id,
            extracted_file=str(output_path),
        )

        data_response = {
            "uuid": str(extraction.uuid),
            "source_pdf": "",
            "extracted_file": extraction.extracted_file,
            "created_at": extraction.created_at.isoformat() + "Z"
        }

        return Response(
            {
                "ok": True,
                "bank": "millenium",
                "data": data_response
            },
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, uuid=None):
        """Download do arquivo XLSX com nome padronizado: millenium_[uuid].xlsx"""

        try:
            extraction = self.get_object()
        except Http404:
            return Response(
                {
                    "ok": False,
                    "bank": "millenium",
                    "error": "Extração não encontrada",
                    "detail": f"UUID {uuid} não existe"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        file_path = Path(extraction.extracted_file)

        if not extraction.extracted_file:
            return Response(
                {
                    "ok": False,
                    "bank": "millenium",
                    "error": "Nenhum arquivo gerado"
                },
                status=status.HTTP_410_GONE
            )

        if not file_path.exists():
            logger.warning("Arquivo esperado não encontrado: %s", file_path)
            return Response(
                {
                    "ok": False,
                    "bank": "millenium",
                    "error": "Arquivo não encontrado no servidor"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        download_filename = f"millenium_{extraction.uuid}.xlsx"

        try:
            response = FileResponse(
                open(file_path, "rb"),
                as_attachment=True,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            # Força o nome do arquivo no cabeçalho - isso resolve o problema na maioria dos navegadores
            response["Content-Disposition"] = f'attachment; filename="{download_filename}"'
            return response

        except Exception as exc:
            logger.exception("Erro ao servir arquivo: %s", file_path)
            return Response(
                {
                    "ok": False,
                    "bank": "millenium",
                    "error": "Erro ao baixar o arquivo",
                    "detail": str(exc)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["get"], url_path="status")
    def status(self, request, uuid=None):
        """Retorna status da extração para polling."""

        extraction = self.get_object()
        file_path = Path(extraction.extracted_file) if extraction.extracted_file else None
        file_ready = bool(file_path and file_path.exists())

        download_url = None
        if file_ready:
            download_url = request.build_absolute_uri(
                f"/ap1/v1/converter/millenium/extract/{extraction.uuid}/download/"
            )

        return Response({
            "ok": True,
            "bank": "millenium",
            "status": "ready" if file_ready else "processing_or_failed",
            "file_exists": file_ready,
            "download_available": file_ready,
            "download_url": download_url,
            "created_at": extraction.created_at,
        })