import io
from pypdf import PdfReader

def extract_text_from_pdf(file_stream: io.BytesIO) -> str:
    reader = PdfReader(file_stream)
    text_blocks = []
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text_blocks.append(extracted)
    return "\n".join(text_blocks)
