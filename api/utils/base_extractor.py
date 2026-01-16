import io
from PyPDF2 import PdfReader

class BaseExtractor:
    def __init__(self, pdf_file):
        # pdf_file vem do upload (InMemoryUploadedFile)
        self.pdf_file = pdf_file

        # Criar stream copiável
        self.stream = io.BytesIO(pdf_file.read())
        pdf_file.seek(0)  # reset para evitar problemas

    def validate_bank(self):
        raise NotImplementedError("Implementar validação do banco.")

    def extract_movements(self):
        raise NotImplementedError("Implementar extração.")

    def extract(self):
        # Validação
        if not self.validate_bank():
            return {"erro": "O PDF enviado não pertence ao banco correto."}

        # Extração
        movimentos = self.extract_movements()

        return {
            "banco": self.__class__.__name__.replace("Extractor", "").lower(),
            "movimentos": movimentos
        }
