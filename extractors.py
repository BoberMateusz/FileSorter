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

    try:
        if ext in {".txt", ".md", ".py", ".csv", ".log"}:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                extracted_text = f.read()

        elif ext == ".pdf":
            reader = PdfReader(path)
            pages_text = [page.extract_text() or "" for page in reader.pages]
            extracted_text = "\n".join(pages_text)

        elif ext in {".png", ".jpg", ".jpeg", ".webp"}:
            engine = _get_ocr_engine()
            result, _ = engine(str(path))
            if result:
                # Filtrujemy szum OCR o niskiej pewności (< 0.5)
                extracted_text = " ".join(
                    [line[1] for line in result if line[1] and line[2] > 0.5]
                )
        else:
            # Ignorujemy nieobsługiwane pliki (np. desktop.ini, .zip) bez wywalania programu
            return ""
    except Exception as e:
        print(f"[Extractor Error] Błąd dla pliku {file_path}: {e}")
        return ""

    return re.sub(r"\s+", " ", extracted_text).strip()


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