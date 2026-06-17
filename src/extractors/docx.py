import io
import docx

def extract_text_from_docx(file_stream: io.BytesIO) -> str:
    doc = docx.Document(file_stream)
    text_blocks = []
    for para in doc.paragraphs:
        if para.text:
            text_blocks.append(para.text)
    return "\n".join(text_blocks)
