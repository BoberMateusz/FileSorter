import logging
import threading
import time
from pathlib import Path

from rich.console import Console
from rich.markup import escape
from rich.progress import track
from rich.table import Table

from scanner import ask_folder, scan, choose
from extractors import process_file, _get_ocr_engine
from search import suggest_folder, suggest_folder_for_file, REVIEW
from sorter import move_files
from config import FOLDERS, THRESHOLD, SORT_MAX_PAGES

logging.getLogger("pypdf").setLevel(logging.ERROR)   # ukrywa ostrzeżenia o uszkodzonych PDF-ach

MIN_MARGIN = 0.05   # mała różnica między 1. a 2. folderem = przypadek na granicy
console = Console()


def _warmup() -> None:
    """Ładuje model embeddingowy, wektory folderów i OCR - raz, w tle."""
    suggest_folder("rozgrzewka", FOLDERS)
    _get_ocr_engine()


def main():
    warmup = threading.Thread(target=_warmup, daemon=True)
    warmup.start()                  # modele ładują się, gdy user wybiera folder i pliki

    folder = ask_folder()
    to_sort = choose(scan(folder))
    warmup.join()                   # czeka tylko, jeśli ładowanie jeszcze trwa
    results = {}

    for f in track(to_sort, description="Analizuję pliki..."):
        t0 = time.perf_counter()
        try:
            chunks = [item["text"] for item in process_file(str(f), max_pages=SORT_MAX_PAGES)]
        except Exception as e:
            console.print(f"[red]![/red] {escape(f.name)}: {escape(str(e))}")
            chunks = []

        target, score, margin, _ = suggest_folder_for_file(chunks, FOLDERS, THRESHOLD)
        results[f] = {"chunks": chunks, "folder": target, "score": score, "margin": margin,
                      "time": time.perf_counter() - t0}

    return folder, results


def score_cell(score: float | None) -> str:
    if score is None:
        return "[dim]brak tekstu[/dim]"
    color = "green" if score >= 0.45 else "yellow" if score >= THRESHOLD else "red"
    return f"[{color}]{score:.3f}[/{color}]"


def show_plan(results: dict) -> None:
    table = Table(title="Plan przeniesienia")
    table.add_column("#", justify="right", style="dim")
    table.add_column("Plik")
    table.add_column("Folder", style="cyan")
    table.add_column("Podobieństwo", justify="right")
    table.add_column("Czas", justify="right", style="dim")
    table.add_column("Uwagi")

    for i, (f, info) in enumerate(results.items(), 1):
        note = ""
        if info["margin"] is not None and info["margin"] < MIN_MARGIN:
            note = "[yellow]⚠ na granicy[/yellow]"
        table.add_row(str(i), escape(f.name), info["folder"], score_cell(info["score"]),
                      f"{info['time']:.1f} s", note)

    console.print(table)


def confirm_and_move(folder: Path, results: dict) -> None:
    if not results:
        return

    show_plan(results)
    answer = console.input(
        "\n[bold]Co przenieść?[/bold]\n"
        "  [cyan]a[/cyan]       - wszystkie\n"
        "  [cyan]n[/cyan]       - nic\n"
        "  [cyan]1 3 5[/cyan]   - tylko pliki o tych numerach\n"
        "> "
    ).strip().lower()

    if answer == "n":
        console.print("[dim]Nic nie przeniesiono.[/dim]")
        return

    items = list(results.items())
    if answer == "a":
        selected = items
    else:
        ids = dict.fromkeys(int(n) for n in answer.split() if n.isdigit() and 1 <= int(n) <= len(items))
        selected = [items[i - 1] for i in ids]

    if not selected:
        console.print("[yellow]Nie rozpoznano wyboru - nic nie przeniesiono.[/yellow]")
        return

    mapping = {f.name: (info["folder"], None) for f, info in selected}
    move_files(str(folder), mapping)
    console.print(f"[green]✔ Przeniesiono {len(mapping)} plików.[/green]")


if __name__ == "__main__":
    folder, results = main()
    confirm_and_move(folder, results)