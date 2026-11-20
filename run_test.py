import time
from indexer import index_folder
from search import query_index, suggest_folder

t = time.time()
n = index_folder("./test_files")
print(f"Zaindeksowano {n} fragmentów w {time.time() - t:.1f} s")

for q in ["faktura", "notatki z wykładu", "umowa najmu"]:
    results, ms = query_index(q, top_k=3)
    print(f"\n'{q}' ({ms:.0f} ms)")
    for r in results:
        print(f"  {r['score']:.2f}  {r['filename']}  |  {r['text'][:80]}...")

print(suggest_folder("Sprzedawca: Orange Polska, kwota do zapłaty 79,99 zł", {
    "Faktury i finanse": "faktury, rachunki, płatności, paragony",
    "Studia": "notatki z wykładów, algorytmy, zadania",
    "Dokumenty urzędowe": "urząd, wniosek, decyzja, umowa",
}))