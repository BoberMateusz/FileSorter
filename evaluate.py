
# evaluate.py
# Mierzy trafność suggest_folder() na plikach z ./test_files.
# Wymaga wersji suggest_folder z search.py, która przyjmuje listy opisów
# i parametr return_scores=True.
import os
import time

import config
from file_processor import process_file
from search import suggest_folder

TEST_DIR = "./test_files"
THRESHOLD = 0.30     # poniżej tego wyniku plik trafia do "Do przejrzenia"
MIN_MARGIN = 0.05    # mały odstęp między 1. a 2. folderem = przypadek na granicy

FOLDERS = {
    "Faktury i finanse": [
        "faktura VAT, sprzedawca, nabywca, kwota do zapłaty, termin płatności",
        "paragon ze sklepu, zakupy, suma PLN, podatek PTU",
    ],
    "Studia": [
        "notatki z wykładu na uczelni, prowadzący, temat zajęć",
        "algorytmy i struktury danych, grafy, złożoność obliczeniowa, BFS, DFS",
        "kolokwium, laboratorium, zadania do zrobienia, egzamin",
    ],
    "Dokumenty urzędowe": [
        "wniosek do urzędu, zaświadczenie, decyzja administracyjna, pouczenie",
        "umowa najmu mieszkania, czynsz, kaucja, wynajmujący i najemca",
    ],
    "Błędy w kodzie": [
        "komunikat błędu kompilatora, error, warning, linker",
        "wyjątek w programie, access violation, stos wywołań, crash",
    ],
}

# plik -> oczekiwany folder
# (dla pliku, który nie pasuje do żadnego folderu, wpisz "Do przejrzenia")
EXPECTED = {
    "document(14).pdf": "Faktury i finanse",
    "paragon_1119.txt": "Faktury i finanse",
    "scan_0021.pdf": "Dokumenty urzędowe",
    "wniosek_final2.pdf": "Dokumenty urzędowe",
    "notatki_wyklad7.docx": "Studia",
    "output.txt": "Błędy w kodzie",
}


def main():
    print(f"Model: {config.MODEL_NAME}  (backend: {getattr(config, 'EMBED_BACKEND', 'fastembed')})")
    print(f"Próg pewności: {THRESHOLD}\n")

    ok = 0
    total = 0
    total_time = 0.0

    for name, expected in EXPECTED.items():
        path = os.path.join(TEST_DIR, name)
        if not os.path.exists(path):
            print(f"POMIJAM {name}: brak pliku w {TEST_DIR}")
            continue

        text = " ".join(process_file(path))
        if not text.strip():
            print(f"BŁĄD  {name}: pusty tekst (process_file nic nie wyciągnął)")
            total += 1
            continue

        t0 = time.perf_counter()
        pred, scores = suggest_folder(text, FOLDERS, threshold=THRESHOLD, return_scores=True)
        total_time += time.perf_counter() - t0

        ranked = sorted(scores.items(), key=lambda x: -x[1])
        best_score = ranked[0][1]
        margin = best_score - ranked[1][1] if len(ranked) > 1 else best_score
        correct = pred == expected
        ok += correct
        total += 1

        flag = "OK   " if correct else "BŁĄD "
        warn = "  [na granicy]" if margin < MIN_MARGIN else ""
        print(f"{flag}{name} -> {pred}   (wynik {best_score:.2f}, odstęp {margin:.2f}){warn}")
        if not correct:
            print(f"      oczekiwano: {expected}")
            print("      ranking:", [(n, round(s, 2)) for n, s in ranked])

    if total:
        print(f"\nTrafność: {ok}/{total} ({100 * ok / total:.0f}%)")
        print(f"Średni czas klasyfikacji: {1000 * total_time / total:.0f} ms/plik")


if __name__ == "__main__":
    main()
