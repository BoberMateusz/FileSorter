# FileSorter

Lokalny sorter plików i wyszukiwarka semantyczna oparta na embeddingach.

## Instalacja
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Uruchomienie
```bash
python run_test.py                 # indeksowanie ./test_files + przykładowe zapytania
python evaluate.py                 # trafność klasyfikacji na plikach testowych
python sorter.py ./test_files      # podgląd, gdzie trafiłby każdy plik
python sorter.py ./kopia --move    # przeniesienie plików (najpierw zrób kopię folderu!)
```

## Zmiana modelu (bez edycji kodu)
```bash
EMBED_BACKEND=ollama MODEL_NAME=embeddinggemma python evaluate.py   # wymaga: ollama pull embeddinggemma
```
Foldery i próg pewności są w `config.py` (`FOLDERS`, `THRESHOLD`).

## Moduły
- `extractors.py` - wyciąganie tekstu (PDF, DOCX, tekst, obrazy przez OCR) i dzielenie na chunki
- `embedder.py` - jedno miejsce, które zna model embeddingowy
- `indexer.py` / `search.py` - ChromaDB: `query_index()` i `suggest_folder()`
- `sorter.py` - `classify_file()` zwraca folder docelowy dla pliku
