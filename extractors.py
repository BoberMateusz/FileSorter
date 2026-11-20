import os
import re
from pathlib import Path
from pypdf import PdfReader
from rapidocr_onnxruntime import RapidOCR

# Inicjalizacja instancji RapidOCR (wagi pobierają się przy pierwszym uruchomieniu)
_ocr_engine = None


def _get_ocr_engine() -> RapidOCR:
    global _ocr_engine
    if _ocr_engine is None:
        _ocr_engine = RapidOCR()
    return _ocr_engine


def extract_text(file_path: str) -> str:
    """Ekstrahuje surowy tekst z plików .txt, .md, .pdf oraz obrazów (.png, .jpg, .jpeg, .webp)."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Plik nie istnieje: {file_path}")

    ext = path.suffix.lower()
    extracted_text = ""

    if ext in {".txt", ".md"}:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            extracted_text = f.read()

    elif ext == ".pdf":
        reader = PdfReader(path)
        pages_text = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                pages_text.append(t)
        extracted_text = "\n".join(pages_text)

    elif ext in {".png", ".jpg", ".jpeg", ".webp"}:
        engine = _get_ocr_engine()
        result, _ = engine(str(path))
        if result:
            # result to lista struktur: [bbox, text, score]
            extracted_text = "\n".join([line[1] for line in result if line[1]])

    else:
        raise ValueError(f"Nieobsługiwany format pliku: {ext}")

    # Normalizacja białych znaków
    clean_text = re.sub(r"\s+", " ", extracted_text).strip()
    return clean_text


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """Dzieli tekst na nakładające się fragmenty (chunki) i odrzuca szum (< 30 znaków)."""
    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end].strip()

        # Dodaj chunk tylko jeśli przekracza próg szumu (30 znaków)
        if len(chunk) >= 30:
            chunks.append(chunk)

        # Przesunięcie okna z uwzględnieniem nakładania (overlap)
        start += chunk_size - overlap

    return chunks


def process_file_for_embedding(
    file_path: str, chunk_size: int = 500, overlap: int = 100
) -> list[str]:
    """Główny punkt wejścia (kontrakt): pobiera ścieżkę pliku, wyciąga tekst i zwraca gotowe chunki."""
    raw_text = extract_text(file_path)
    return chunk_text(raw_text, chunk_size=chunk_size, overlap=overlap)