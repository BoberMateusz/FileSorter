import os

# --- Model embeddingowy (nadpisz zmiennymi środowiskowymi, bez edycji pliku) ---
# Domyślnie fastembed + MiniLM, bo działa bez Ollamy.
# EmbeddingGemma:  EMBED_BACKEND=ollama MODEL_NAME=embeddinggemma python evaluate.py
EMBED_BACKEND = os.getenv("EMBED_BACKEND", "fastembed")   # "fastembed" | "ollama"
MODEL_NAME = os.getenv(
    "MODEL_NAME", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
DB_PATH = os.getenv("DB_PATH", "./chroma_db")

# --- Chunki (wspólne dla indexera, sortera i evaluate) ---
# MiniLM ucina wejście po 128 tokenach (~350-450 znaków polskiego tekstu),
# więc dłuższe chunki tracą końcówkę. Po zmianie przeindeksuj chroma_db.
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "350"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "70"))

# Sorter czyta tylko początek PDF-a - rodzaj dokumentu widać po pierwszych stronach.
# (Indexer dalej czyta całość.)  None = wszystkie strony.
SORT_MAX_PAGES = 10

# --- Sorter: jedno miejsce z folderami i progiem (używają go main.py i evaluate.py) ---
# Próg pewności: poniżej niego plik trafia do "Do przejrzenia".
# Dobierz go na plikach spoza kategorii, bo zakresy wyników różnią się między modelami.
THRESHOLD = float(os.getenv("THRESHOLD", "0.30"))

FOLDERS = {
    "Szkoła i studia": [
        "notatki z wykładu, prowadzący, temat zajęć, slajdy z prezentacji",
        "zadania do rozwiązania, karta pracy, sprawdzian, kolokwium, egzamin",
        "podręcznik, zbiór zadań, rozdział, definicja, twierdzenie, przykład",
        "ściągawka, infografika, wzory, powtórka materiału",
        "laboratorium z programowania, kod źródłowy, funkcja, pętla, algorytm",
        "system operacyjny, Linux, terminal, sieci komputerowe, baza danych, SQL",
        "lecture notes, exercises, homework, exam, university course, programming lab",
    ],
    "Prace pisemne": [
        "rozprawka, wstęp, teza, argumenty, zakończenie, wnioski",
        "esej, wypracowanie, referat, interpretacja utworu literackiego",
        "sprawozdanie z laboratorium, cel ćwiczenia, przebieg, wyniki, bibliografia",
        "essay, report, introduction, conclusion, references",
    ],
    "Faktury i finanse": [
        "faktura VAT, sprzedawca, nabywca, NIP, kwota do zapłaty, termin płatności",
        "paragon, zakupy, suma PLN, podatek PTU",
        "wyciąg z konta bankowego, przelew, saldo, potwierdzenie płatności",
        "invoice, receipt, payment, total amount, bank statement",
    ],
    "Bilety i podróże": [
        "bilet kolejowy, pociąg, stacja odjazdu, stacja przyjazdu, wagon, miejsce",
        "bilet lotniczy, karta pokładowa, lot, bramka, bagaż, odprawa",
        "bilet autobusowy, przewoźnik, przesiadka, data i godzina odjazdu",
        "rezerwacja hotelu, zameldowanie, wymeldowanie, potwierdzenie rezerwacji",
        "train ticket, boarding pass, departure, arrival, booking confirmation",
    ],
    "Dokumenty i umowy": [
        "wniosek do urzędu, zaświadczenie, decyzja administracyjna, pouczenie",
        "oświadczenie, podpis, PESEL, legitymacja, dowód osobisty",
        "umowa, strony umowy, przedmiot umowy, paragraf, zobowiązania",
        "umowa najmu, umowa o pracę, umowa zlecenie, wynagrodzenie, czynsz",
        "official document, certificate, contract, agreement, signature",
    ],
    "Praca i CV": [
        "curriculum vitae, doświadczenie zawodowe, wykształcenie, umiejętności",
        "list motywacyjny, oferta pracy, rekrutacja, stanowisko",
        "certyfikat ukończenia kursu, szkolenie, zaświadczenie o kwalifikacjach",
        "resume, work experience, skills, cover letter, job offer",
    ],
}