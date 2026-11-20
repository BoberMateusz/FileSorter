import os
import re
from pathlib import Path
from pypdf import PdfReader
from rapidocr_onnxruntime import RapidOCR

_ocr_engine = None


def _get_ocr_engine() -> RapidOCR:
    global _ocr_engine
    if _ocr_engine is None:
        _ocr_engine = RapidOCR()
    return _ocr_engine


def extract_text(file_path: str) -> str:
    """Ekstrahuje surowy tekst z plików .txt, .md, .pdf oraz obrazów (.png, .jpg, .jpeg, .webp)."""
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return ""

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
    else:
        raise ValueError(f"Nieobsługiwany format pliku: {ext}")

    # Normalizacja białych znaków
    clean_text = re.sub(r"\s+", " ", extracted_text).strip()
    return clean_text


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """Dzieli tekst na nakładające się fragmenty (chunki) i odrzuca szum (< 30 znaków)."""
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text] if len(text) >= 20 else []

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


def process_file_for_embedding(
    file_path: str, chunk_size: int = 500, overlap: int = 100
) -> list[str]:
    """Zwraca listę samych tekstowych chunków."""
    raw_text = extract_text(file_path)
    return chunk_text(raw_text, chunk_size=chunk_size, overlap=overlap)


def process_file(
    file_path: str, chunk_size: int = 500, overlap: int = 100
) -> list[dict]:
    """Główny kontrakt dla Osoby 2 (indexer.py) — zwraca chunki z metadanymi."""
    chunks = process_file_for_embedding(file_path, chunk_size=chunk_size, overlap=overlap)
    filename = os.path.basename(file_path)

    return [
        {
            "text": f"[Plik: {filename}] {chunk}",
            "raw_snippet": chunk,
            "metadata": {
                "source": str(file_path),
                "filename": filename,
                "chunk_index": idx,
            },
        }
        for idx, chunk in enumerate(chunks)
    ]


# Bezpieczny blok testowy — uruchamia się TYLKO gdy odpalisz bezpośrednio extractors.py
if __name__ == "__main__":
    test_path = "C:/Users/Szymon/Downloads/NET.pdf"
    if os.path.exists(test_path):
        wynik = process_file(test_path)
        print(f"Wygenerowano {len(wynik)} chunków.")
        for item in wynik[:3]:
            print(f"--- Chunk {item['metadata']['chunk_index'] + 1} ---")
            print(item["raw_snippet"])