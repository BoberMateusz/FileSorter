# skanuje pobrane - pliki ktore nie sa w zadnym folderze sa wyswietlane wraz z jakims id a ty wybierasz id ktore maja byc przeslane do sortera
from pathlib import Path
DOWNLOADS = Path.home() / "Downloads"


def scan() -> list[Path]:
    return [p for p in DOWNLOADS.iterdir() if p.is_file()]


def choose(files: list[Path]) -> list[Path]:
    for i, f in enumerate(files, 1):
        print(f"{i}. {f.name}")

    picked = input("\nNumery plikow do posortowania (np. 1 3 5): ").split()
    return [files[int(n) - 1] for n in picked if n.isdigit() and 1 <= int(n) <= len(files)]


if __name__ == "__main__":
    to_sort = choose(scan())
    print("Do sortera:", [f.name for f in to_sort])
