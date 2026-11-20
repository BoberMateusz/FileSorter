# sorter.py
# Dla każdego pliku zwraca nazwę folderu, do którego powinien trafić.
#
# Użycie z terminala:
#   python sorter.py ./test_files             # tylko podgląd (nic nie przenosi)
#   python sorter.py ./test_files --move      # naprawdę przenosi pliki do podfolderów
#   python sorter.py ./test_files --threshold 0.5
#
# Użycie z kodu (np. dla UI):
#   from sorter import classify_file, classify_folder
#   folder, score, scores = classify_file("plik.pdf")
#   mapping = classify_folder("./Downloads")   # {"plik.pdf": ("Faktury i finanse", 0.74), ...}
#
# Foldery i próg są w config.py (FOLDERS, THRESHOLD).
import argparse
import os
import shutil

import config
from extractors import process_file_for_embedding as process_file
from search import suggest_folder

REVIEW = "Do przejrzenia"
FOLDERS = config.FOLDERS
THRESHOLD = config.THRESHOLD


def classify_file(path: str, folders: dict | None = None, threshold: float | None = None):
    """Zwraca (nazwa_folderu, wynik, wszystkie_wyniki).
    Gdy tekst jest pusty albo pewność za niska, folderem jest "Do przejrzenia"."""
    folders = folders or FOLDERS
    threshold = THRESHOLD if threshold is None else threshold

    text = " ".join(process_file(path))
    if not text.strip():
        return REVIEW, 0.0, {}

    folder, scores = suggest_folder(text, folders, threshold=threshold, return_scores=True)
    return folder, max(scores.values()), scores


def classify_folder(source_dir: str, folders: dict | None = None, threshold: float | None = None) -> dict:
    """Klasyfikuje pliki leżące bezpośrednio w source_dir (bez podfolderów).
    Zwraca {nazwa_pliku: (folder, wynik)}."""
    result = {}
    for name in sorted(os.listdir(source_dir)):
        path = os.path.join(source_dir, name)
        if name.startswith(".") or not os.path.isfile(path):
            continue
        folder, score, _ = classify_file(path, folders, threshold)
        result[name] = (folder, score)
    return result


def _free_path(path: str) -> str:
    """Nie nadpisuje istniejących plików: dodaje _1, _2, ... do nazwy."""
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    i = 1
    while os.path.exists(f"{base}_{i}{ext}"):
        i += 1
    return f"{base}_{i}{ext}"


def move_files(source_dir: str, mapping: dict, dest_root: str | None = None) -> None:
    dest_root = dest_root or source_dir
    for name, (folder, _) in mapping.items():
        target_dir = os.path.join(dest_root, folder)
        os.makedirs(target_dir, exist_ok=True)
        target = _free_path(os.path.join(target_dir, name))
        shutil.move(os.path.join(source_dir, name), target)


def main():
    ap = argparse.ArgumentParser(description="Podpowiada folder dla każdego pliku.")
    ap.add_argument("source", help="folder z plikami do posortowania")
    ap.add_argument("--move", action="store_true", help="przenieś pliki (domyślnie tylko podgląd)")
    ap.add_argument("--threshold", type=float, default=None, help=f"próg pewności (domyślnie {THRESHOLD})")
    ap.add_argument("--dest", default=None, help="folder docelowy (domyślnie ten sam co source)")
    args = ap.parse_args()

    mapping = classify_folder(args.source, threshold=args.threshold)
    if not mapping:
        print("Brak plików do sklasyfikowania.")
        return

    width = max(len(n) for n in mapping)
    for name, (folder, score) in mapping.items():
        print(f"{name:<{width}}  ->  {folder}   (wynik {score:.2f})")

    if args.move:
        move_files(args.source, mapping, args.dest)
        print(f"\nPrzeniesiono {len(mapping)} plików.")
    else:
        print("\nTryb podglądu: nic nie przeniesiono. Dodaj --move, żeby przenieść pliki.")


if __name__ == "__main__":
    main()
