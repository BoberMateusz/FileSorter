# evaluate.py
# Mierzy trafność klasyfikacji folderów na plikach z ./test_files.
# Używa DOKŁADNIE tej samej ścieżki co main.py: process_file -> suggest_folder_for_file,
# a foldery, próg i rozmiar chunków bierze z config.py.
#
# Porównanie modeli:
#   python evaluate.py
#   EMBED_BACKEND=ollama MODEL_NAME=embeddinggemma python evaluate.py
import logging
import os
import time

import config
from extractors import process_file
from search import suggest_folder_for_file

logging.getLogger("pypdf").setLevel(logging.ERROR)

TEST_DIR = "./test_files"
MIN_MARGIN = 0.05    # mały odstęp między 1. a 2. folderem = przypadek na granicy

# plik -> oczekiwany folder (nazwy muszą zgadzać się z config.FOLDERS)
# dla pliku, który nie pasuje do żadnego folderu, wpisz "Do przejrzenia"
EXPECTED = {
    "document(14).pdf": "Faktury i finanse",
    "paragon_1119.txt": "Faktury i finanse",
    "scan_0021.pdf": "Dokumenty i umowy",
    "wniosek_final2.pdf": "Dokumenty i umowy",
    "notatki_wyklad7.docx": "Szkoła i studia",
    "output.txt": "Do przejrzenia",   # log błędów - nie ma już kategorii "Błędy w kodzie"
}


def main():
    print(f"Model: {config.MODEL_NAME}  (backend: {config.EMBED_BACKEND})")
    print(f"Próg: {config.THRESHOLD}   chunk: {config.CHUNK_SIZE}/{config.CHUNK_OVERLAP}\n")

    unknown = {f for f in EXPECTED.values() if f != "Do przejrzenia" and f not in config.FOLDERS}
    if unknown:
        print(f"UWAGA: w EXPECTED są foldery, których nie ma w config.FOLDERS: {unknown}\n")

    ok = 0
    total = 0
    total_time = 0.0

    for name, expected in EXPECTED.items():
        path = os.path.join(TEST_DIR, name)
        if not os.path.exists(path):
            print(f"POMIJAM {name}: brak pliku w {TEST_DIR}")
            continue

        try:
            chunks = [item["text"] for item in process_file(path)]
        except Exception as e:
            print(f"BŁĄD  {name}: extractor - {e}")
            total += 1
            continue

        if not chunks:
            print(f"BŁĄD  {name}: pusty tekst (extractor nic nie wyciągnął)")
            total += 1
            continue

        t0 = time.perf_counter()
        pred, score, margin, ranked = suggest_folder_for_file(chunks, config.FOLDERS,
                                                              threshold=config.THRESHOLD)
        total_time += time.perf_counter() - t0

        correct = pred == expected
        ok += correct
        total += 1

        flag = "OK   " if correct else "BŁĄD "
        warn = "  [na granicy]" if margin < MIN_MARGIN else ""
        print(f"{flag}{name} -> {pred}   (wynik {score:.3f}, odstęp {margin:.3f}){warn}")
        if not correct:
            print(f"      oczekiwano: {expected}")
            print("      ranking:", [(n, round(s, 3)) for n, s in ranked])

    if total:
        print(f"\nTrafność: {ok}/{total} ({100 * ok / total:.0f}%)")
        print(f"Średni czas klasyfikacji: {1000 * total_time / total:.0f} ms/plik")


if __name__ == "__main__":
    main()
