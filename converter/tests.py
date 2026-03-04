from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch, MagicMock
from converter.models.millenium_model import MilleniumFile
from converter.services.millenium_extractor import MilleniumExtractor

User = get_user_model()

class ConverterTests(APITestCase):
    def setUp(self):
        self.upload_url = reverse('millenium-upload-list')
        self.extract_url = reverse('millenium-extract-list')

        self.staff_user = User.objects.create_user(
            username="staff@example.com",
            email="staff@example.com",
            password="password123",
            is_staff=True
        )
        self.client.force_authenticate(user=self.staff_user)

    @patch('django.core.files.storage.FileSystemStorage._save')
    @patch('django.core.files.storage.FileSystemStorage.size')
    @patch('django.core.files.storage.FileSystemStorage.open')
    def test_millenium_pdf_upload(self, mock_open, mock_size, mock_save):
        mock_save.return_value = "converter/millenium/upload/test.pdf"
        mock_size.return_value = 100
        mock_open.return_value = MagicMock()

        pdf_content = b"%PDF-1.4 test content"
        pdf_file = SimpleUploadedFile("statement.pdf", pdf_content, content_type="application/pdf")

        # We need to mock get_sha256 which opens the file
        with patch('converter.serializers.millenium_serializers.MilleniumFileSerializerDetails.get_sha256', return_value="dummy-sha"):
            response = self.client.post(self.upload_url, {"file": pdf_file})
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(MilleniumFile.objects.count(), 1)

    @patch('django.core.files.storage.FileSystemStorage._save')
    @patch('converter.services.millenium_extractor.pdfplumber.open')
    @patch('converter.services.millenium_extractor.load_workbook')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.stat')
    def test_millenium_extraction_logic(self, mock_stat, mock_exists, mock_load_workbook, mock_pdf_open, mock_save):
        mock_save.return_value = "converter/millenium/upload/dummy.pdf"
        mock_exists.return_value = True
        mock_stat.return_value.st_size = 1024

        # 1. Mock PDF text
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = (
            "EXTRATO DE CONTA\n"
            "PERÍODO: 2023/01/01 A 2023/01/31\n"
            "SALDO INICIAL 1 000,00\n"
            "01.01 01.01 COMPRA LOJA 900,00\n"
            "SALDO FINAL 900,00"
        )
        mock_pdf.pages = [mock_page]
        mock_pdf_open.return_value.__enter__.return_value = mock_pdf

        # 2. Mock Excel template and saving
        mock_wb = MagicMock()
        mock_ws = MagicMock()

        # Correctly mock worksheet indexing
        d3_mock = MagicMock()
        d5_mock = MagicMock()

        def mock_getitem(key):
            if key == "D3": return d3_mock
            if key == "D5": return d5_mock
            return MagicMock()

        mock_ws.__getitem__.side_effect = mock_getitem

        mock_load_workbook.return_value = mock_wb
        mock_wb.active = mock_ws

        # 3. Create a dummy PDF file in DB
        millenium_file = MilleniumFile.objects.create(
            file=SimpleUploadedFile("dummy.pdf", b"dummy content"),
            uploaded_by=self.staff_user
        )

        # 4. Run extraction
        extractor = MilleniumExtractor(pdf_path="/tmp/fake.pdf")

        # We need to mock _get_template to return a valid path
        with patch.object(MilleniumExtractor, '_get_template', return_value='/tmp/template.xlsx'):
            with patch('pathlib.Path.mkdir'):
                output_path = extractor.run()

                # Check results
                self.assertIsNotNone(output_path)
                self.assertEqual(d3_mock.value, 1000.0)
                self.assertEqual(d5_mock.value, 900.0)
