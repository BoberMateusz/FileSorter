import time
import config
from indexer import index_folder
from search import query_index, suggest_folder

t = time.time()
n = index_folder("./test_files")
print(f"Zaindeksowano {n} fragmentów w {time.time() - t:.1f} s  (model: {config.MODEL_NAME})")

for q in ["faktura", "notatki z wykładu", "umowa najmu"]:
    results, ms = query_index(q, top_k=3)
    print(f"\n'{q}' ({ms:.0f} ms)")
    for r in results:
        print(f"  {r['score']:.2f}  {r['filename']}  |  {r['text'][:80]}...")

print("\nsuggest_folder:", suggest_folder(
    "Sprzedawca: Orange Polska, kwota do zapłaty 79,99 zł", config.FOLDERS))
