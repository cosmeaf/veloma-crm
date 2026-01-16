import pdfplumber
from api.utils.base_extractor import BaseExtractor


class MillenniumExtractor(BaseExtractor):

    def validate_bank(self):
        self.stream.seek(0)
        with pdfplumber.open(self.stream) as pdf:
            text = pdf.pages[0].extract_text().lower()
        return "millennium" in text or "bcp" in text

    def extract_movements(self):
        movimentos = []

        self.stream.seek(0)
        with pdfplumber.open(self.stream) as pdf:

            for page in pdf.pages:
                table = page.extract_table()

                if not table:
                    continue

                linhas = table[1:]  # remove header

                for row in linhas:
                    if not row or len(row) < 6:
                        continue

                    movimentos.append({
                        "data_lanc": row[0],
                        "data_valor": row[1],
                        "descricao": row[2],
                        "debito": self.to_float(row[3]),
                        "credito": self.to_float(row[4]),
                        "saldo": self.to_float(row[5]),
                    })

        return movimentos

    def to_float(self, val):
        if not val:
            return None
        return float(val.replace(".", "").replace(",", "."))
