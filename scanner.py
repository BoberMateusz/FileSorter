# skanuje wybrany folder (domyslnie Pobrane) - pliki luzem sa wyswietlane z id, a ty wybierasz id do sortera
from pathlib import Path
from rich.console import Console
from rich.markup import escape
from rich.table import Table

console = Console()
DOWNLOADS = Path.home() / "Downloads"
SUPPORTED = {".txt", ".md", ".py", ".csv", ".log", ".pdf", ".png", ".jpg", ".jpeg", ".webp"}


def ask_folder() -> Path:
    while True:
        raw = input(f"Podaj ścieżkę bezwzględną do folderu, który chcesz posortować\n"
                    f"(Enter = {DOWNLOADS}): ").strip().strip('"')
        if not raw:
            return DOWNLOADS
        folder = Path(raw)
        if folder.is_absolute() and folder.is_dir():
            return folder
        print("To nie jest istniejący folder (albo ścieżka nie jest bezwzględna). Spróbuj jeszcze raz.\n")


def scan(folder: Path = DOWNLOADS) -> list[Path]:
    return [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED]


def choose(files: list[Path]) -> list[Path]:
    if not files:
        console.print("[yellow]Brak obsługiwanych plików w tym folderze.[/yellow]")
        return []

    table = Table(title="Pliki do posortowania")
    table.add_column("#", justify="right", style="dim")
    table.add_column("Plik")
    table.add_column("Typ", style="magenta")
    table.add_column("KB", justify="right")
    for i, f in enumerate(files, 1):
        table.add_row(str(i), escape(f.name), f.suffix.lower(), f"{f.stat().st_size / 1024:.0f}")
    console.print(table)

    picked = console.input("\nNumery plików do posortowania (np. 1 3 5): ").split()
    ids = dict.fromkeys(int(n) for n in picked if n.isdigit() and 1 <= int(n) <= len(files))
    return [files[i - 1] for i in ids]