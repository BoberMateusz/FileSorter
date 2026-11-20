
import os

CHUNK_WORDS = 120   # rozmiar fragmentu (słowa)
OVERLAP = 20        # nakładanie się fragmentów (słowa)
MAX_CHARS = 200_000 # zabezpieczenie przed gigantycznymi plikami

TEXT_EXT = {".txt", ".md", ".csv", ".log", ".json", ".py", ".cpp", ".c", ".h",
            ".java", ".js", ".html", ".xml", ".tex", ".sql"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}


def _read_text_file(path: str) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp1250", "latin-1"):  # cp1250 = polskie Windowsy
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read(MAX_CHARS)
        except UnicodeDecodeError:
            continue
    return ""


def _read_pdf(path: str) -> str:
    try:
        import pymupdf as fitz  # pymupdf
        parts = []
        with fitz.open(path) as doc:
            for page in doc:
                parts.append(page.get_text())
                if sum(map(len, parts)) > MAX_CHARS:
                    break
        return "\n".join(parts)
    except ImportError:
        from pypdf import PdfReader
        return "\n".join((p.extract_text() or "") for p in PdfReader(path).pages)


def _read_docx(path: str) -> str:
    from docx import Document
    doc = Document(path)
    parts = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            parts.append(" | ".join(c.text for c in row.cells))
    return "\n".join(parts)


def _read_image(path: str) -> str:
    try:
        import pytesseract
        from PIL import Image
        return pytesseract.image_to_string(Image.open(path), lang="pol+eng")
    except Exception:
        return ""  # brak OCR = obraz pomijamy, nie wywalamy programu


def extract_text(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return _read_pdf(path)
    if ext == ".docx":
        return _read_docx(path)
    if ext in TEXT_EXT:
        return _read_text_file(path)
    if ext in IMAGE_EXT:
        return _read_image(path)
    return ""


def chunk_text(text: str, size: int = CHUNK_WORDS, overlap: int = OVERLAP) -> list[str]:
    words = text.split()
    if not words:
        return []
    step = max(1, size - overlap)
    chunks = []
    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i + size])
        if len(chunk) > 20:          # wyrzuć śmieciowe, bardzo krótkie fragmenty
            chunks.append(chunk)
        if i + size >= len(words):
            break
    return chunks


def process_file(path: str) -> list[str]:
    """Zwraca fragmenty tekstu pliku. Nigdy nie rzuca wyjątku z powodu zepsutego pliku."""
    try:
        return chunk_text(extract_text(path))
    except Exception as e:
        print(f"[file_processor] nie udało się przetworzyć {path}: {e}")
        return []


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        ch = process_file(p)
        print(f"{p}: {len(ch)} fragmentów")
        if ch:
            print("  ", ch[0][:150], "...")
