import io
from src.extractors.pdf import extract_text_from_pdf
from src.extractors.docx import extract_text_from_docx

def test_extract_text_from_pdf(monkeypatch):
    class MockPage:
        def extract_text(self):
            return "PDF Test Text"
            
    class MockPdfReader:
        def __init__(self, stream):
            self.pages = [MockPage(), MockPage()]

    monkeypatch.setattr("src.extractors.pdf.PdfReader", MockPdfReader)
    
    dummy_stream = io.BytesIO(b"dummy")
    result = extract_text_from_pdf(dummy_stream)
    assert result == "PDF Test Text\nPDF Test Text"

def test_extract_text_from_docx(monkeypatch):
    class MockPara:
        def __init__(self, text):
            self.text = text
            
    class MockDoc:
        def __init__(self, stream):
            self.paragraphs = [MockPara("Docx"), MockPara("Test"), MockPara("")]

    monkeypatch.setattr("src.extractors.docx.docx.Document", MockDoc)
    
    dummy_stream = io.BytesIO(b"dummy")
    result = extract_text_from_docx(dummy_stream)
    assert result == "Docx\nTest"
