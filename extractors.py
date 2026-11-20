import os
import re
from pathlib import Path

from pypdf import PdfReader
from rapidocr_onnxruntime import RapidOCR

import config

TEXT_EXTS = {".txt", ".md", ".csv", ".log", ".py"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}

_ocr_engine = None


def _get_ocr_engine() -> RapidOCR:
    global _ocr_engine
    if _ocr_engine is None:
        _ocr_engine = RapidOCR()
    return _ocr_engine


def _read_text_file(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp1250"):   # cp1250 = polskie Windowsy
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def _read_docx(path: Path) -> str:
    from docx import Document
    doc = Document(str(path))
    parts = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            parts.append(" | ".join(c.text for c in row.cells))
    return "\n".join(parts)


def extract_text(file_path: str, max_pages: int | None = None) -> str:
    """Ekstrahuje surowy tekst z plików tekstowych, .pdf, .docx oraz obrazów (OCR).

    max_pages - dla PDF-ów: czytaj tylko N pierwszych stron (None = wszystkie).
    """
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return ""

    ext = path.suffix.lower()
    extracted_text = ""

    if ext in TEXT_EXTS:
        extracted_text = _read_text_file(path)

    elif ext == ".pdf":
        reader = PdfReader(path)
        pages_text = []
        for page in reader.pages[:max_pages]:
            t = page.extract_text()
            if t:
                pages_text.append(t)
        extracted_text = "\n".join(pages_text)

    elif ext in IMAGE_EXTS:
        engine = _get_ocr_engine()
        result, _ = engine(str(path))
        if result:
            extracted_lines = []
            for line in result:
                if not line or len(line) < 3:
                    continue
                text_val = line[1]
                try:
                    score = float(line[2])
                except (ValueError, TypeError):
                    score = 1.0
                if text_val and score > 0.5:
                    extracted_lines.append(str(text_val))
            extracted_text = " ".join(extracted_lines)

    elif ext == ".docx":
        extracted_text = _read_docx(path)
    else:
        raise ValueError(f"Nieobsługiwany format pliku: {ext}")

    # Normalizacja białych znaków
    return re.sub(r"\s+", " ", extracted_text).strip()


def chunk_text(text: str, chunk_size: int = config.CHUNK_SIZE,
               overlap: int = config.CHUNK_OVERLAP) -> list[str]:
    """Dzieli tekst na nakładające się fragmenty (chunki) i odrzuca szum (< 30 znaków)."""
    if overlap >= chunk_size:
        raise ValueError("overlap musi być mniejszy niż chunk_size")
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text] if len(text) >= 30 else []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end].strip()
        if len(chunk) >= 30:
            chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


def process_file_for_embedding(file_path: str, chunk_size: int = config.CHUNK_SIZE,
                               overlap: int = config.CHUNK_OVERLAP,
                               max_pages: int | None = None) -> list[str]:
    """Zwraca listę samych tekstowych chunków (kontrakt używany przez indexer)."""
    raw_text = extract_text(file_path, max_pages=max_pages)
    return chunk_text(raw_text, chunk_size=chunk_size, overlap=overlap)


def process_file(file_path: str, chunk_size: int = config.CHUNK_SIZE,
                 overlap: int = config.CHUNK_OVERLAP,
                 max_pages: int | None = None) -> list[dict]:
    """Wersja z metadanymi; "text" ma prefiks z nazwą pliku (używają jej main i evaluate)."""
    chunks = process_file_for_embedding(file_path, chunk_size=chunk_size, overlap=overlap,
                                        max_pages=max_pages)
    filename = os.path.basename(file_path)
    readable_name = Path(filename).stem.replace("_", " ")

    return [
        {
            "text": f"[Plik: {readable_name}] {chunk}",
            "raw_snippet": chunk,
            "metadata": {
                "source": str(file_path),
                "filename": filename,
                "chunk_index": idx,
            },
        }
        for idx, chunk in enumerate(chunks)
    ]


# Test ręczny:  python extractors.py ./test_files/document\(14\).pdf
if __name__ == "__main__":
    import sys
    for test_path in sys.argv[1:]:
        wynik = process_file(test_path)
        print(f"{test_path}: {len(wynik)} chunków.")
        for item in wynik[:3]:
            print(f"--- Chunk {item['metadata']['chunk_index'] + 1} ---")
            print(item["raw_snippet"])