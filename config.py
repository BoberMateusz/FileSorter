import os

# --- Model embeddingowy (nadpisz zmiennymi środowiskowymi, bez edycji pliku) ---
# Domyślnie fastembed + MiniLM, bo działa bez Ollamy.
# EmbeddingGemma:  EMBED_BACKEND=ollama MODEL_NAME=embeddinggemma python evaluate.py
EMBED_BACKEND = os.getenv("EMBED_BACKEND", "fastembed")   # "fastembed" | "ollama"
MODEL_NAME = os.getenv(
    "MODEL_NAME", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
DB_PATH = os.getenv("DB_PATH", "./chroma_db")

# --- Sorter: jedno miejsce z folderami i progiem (używają go sorter.py i evaluate.py) ---
# Próg pewności: poniżej niego plik trafia do "Do przejrzenia".
# Dobierz go na plikach spoza kategorii, bo zakresy wyników różnią się między modelami.
THRESHOLD = float(os.getenv("THRESHOLD", "0.30"))

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
