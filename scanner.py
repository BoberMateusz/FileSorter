# skanuje pobrane - pliki ktore nie sa w zadnym folderze sa wyswietlane wraz z id, a ty wybierasz id do sortera
from pathlib import Path

DOWNLOADS = Path.home() / "Downloads"
SUPPORTED = {".txt", ".md", ".py", ".csv", ".log", ".pdf", ".png", ".jpg", ".jpeg", ".webp"}


def scan() -> list[Path]:
    return [p for p in DOWNLOADS.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED]


def choose(files: list[Path]) -> list[Path]:
    for i, f in enumerate(files, 1):
        print(f"{i}. {f.name}")

    picked = input("\nNumery plikow do posortowania (np. 1 3 5): ").split()
    ids = dict.fromkeys(int(n) for n in picked if n.isdigit() and 1 <= int(n) <= len(files))
    return [files[i - 1] for i in ids]