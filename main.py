from collections import Counter

from scanner import scan, choose, DOWNLOADS
from extractors import process_file_for_embedding
from search import suggest_folder
from sorter import move_files   # <- sprawdź, w którym pliku jest move_files
from config import FOLDERS


def main():
    to_sort = choose(scan())
    results = {}  # plik -> {"chunks": [...], "folder": ...}

    for f in to_sort:
        try:
            chunki = process_file_for_embedding(str(f))
        except Exception as e:
            print(f"\n!!! {f.name}: {e} - pomijam.")
            results[f] = {"chunks": [], "folder": "Do przejrzenia"}
            continue

        print(f"\n=== {f.name}: {len(chunki)} chunków ===")

        if not chunki:
            print("Brak tekstu - pomijam.")
            results[f] = {"chunks": [], "folder": "Do przejrzenia"}
            continue

        votes = []
        for idx, chunk in enumerate(chunki):
            folder = suggest_folder(chunk, FOLDERS) or "Do przejrzenia"
            votes.append(folder)
            print(f"--- Chunk {idx + 1} -> {folder} ---")
            print(chunk[:100])

        best = Counter(votes).most_common(1)[0][0]
        results[f] = {"chunks": chunki, "folder": best}
        print(f">>> {f.name} -> {best}")

    return results


def confirm_and_move(results: dict) -> None:
    if not results:
        return

    print("\n=== Plan przeniesienia ===")
    for f, info in results.items():
        print(f"{f.name}  ->  {info['folder']}")

    if input("\nPrzenieść? (t/n): ").strip().lower() != "t":
        print("Anulowano.")
        return

    mapping = {f.name: (info["folder"], None) for f, info in results.items()}
    move_files(str(DOWNLOADS), mapping)
    print("Gotowe.")


if __name__ == "__main__":
    confirm_and_move(main())