#!/usr/bin/env python3
"""Wkleja paczke wygenerowana przez ModelEngine do zrodel naszej paczki zasobow.

ModelEngine buduje wlasna paczke i oczekuje, ze gracz ja dostanie - a gracz dostaje jedna,
nasza. Zamiast wysylac dwie (czego klient nie robi bez modow), jej zawartosc trafia do
resourcepack/pack/ i wychodzi razem z reszta przy najblizszym build-resourcepack.py.

Scalane, a nie kopiowane na zywca, bo trzy rzeczy w obu paczkach nosza te same nazwy:

  * pack.mcmeta - nasz opis zostaje, dochodza z niego wylacznie nakladki (overlays), bez
    ktorych modele nie renderuja sie na nowszych wersjach gry, oraz lista shaderow, ktore
    Sodium ma ignorowac.
  * atlasy - to listy zrodel tekstur; nadpisanie jednej druga gubi skrzydla albo modele.
    Wpisy sa laczone, powtorki wyrzucane.
  * katalogi nakladek modelengine_* - kopiowane w calosci, bo sa wylacznie jego.

Uruchamiac po kazdym /meg reload, ktory zmienil modele:

    scripts/merge-modelengine-pack.py <katalog "resource pack" ModelEngine>
    scripts/build-resourcepack.py
"""
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PACK = ROOT / "resourcepack" / "pack"


def merge_json(source: pathlib.Path, target: pathlib.Path) -> None:
    """Laczy dwa pliki JSON, o ile oba sa listami zrodel; inaczej bierze nowszy."""
    with source.open(encoding="utf-8") as handle:
        incoming = json.load(handle)

    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as handle:
            json.dump(incoming, handle, ensure_ascii=False, indent=2)
        return

    with target.open(encoding="utf-8") as handle:
        existing = json.load(handle)

    if isinstance(existing, dict) and isinstance(incoming, dict) \
            and "sources" in existing and "sources" in incoming:

        merged = existing["sources"] + [
            entry for entry in incoming["sources"] if entry not in existing["sources"]
        ]
        existing["sources"] = merged

        with target.open("w", encoding="utf-8") as handle:
            json.dump(existing, handle, ensure_ascii=False, indent=2)
        return

    with target.open("w", encoding="utf-8") as handle:
        json.dump(incoming, handle, ensure_ascii=False, indent=2)


def copy_tree(source: pathlib.Path, target: pathlib.Path) -> int:
    copied = 0

    for path in sorted(source.rglob("*")):
        if path.is_dir():
            continue

        destination = target / path.relative_to(source)

        if destination.exists() and path.suffix == ".json" and "atlases" in str(destination):
            merge_json(path, destination)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)

        copied += 1

    return copied


def merge_mcmeta(source: pathlib.Path) -> None:
    """Dokleja nakladki ModelEngine do naszego pack.mcmeta, zostawiajac nasz opis."""
    with (source / "pack.mcmeta").open(encoding="utf-8") as handle:
        theirs = json.load(handle)

    target = PACK / "pack.mcmeta"
    with target.open(encoding="utf-8") as handle:
        ours = json.load(handle)

    if "overlays" in theirs:
        ours["overlays"] = theirs["overlays"]
    if "sodium" in theirs:
        ours["sodium"] = theirs["sodium"]

    with target.open("w", encoding="utf-8") as handle:
        json.dump(ours, handle, ensure_ascii=False, indent=2)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2

    source = pathlib.Path(sys.argv[1])
    if not (source / "pack.mcmeta").exists():
        print(f"{source} nie wyglada na paczke ModelEngine", file=sys.stderr)
        return 1

    files = copy_tree(source / "assets", PACK / "assets")

    for overlay in sorted(source.glob("modelengine_*")):
        if overlay.is_dir():
            files += copy_tree(overlay, PACK / overlay.name)

    merge_mcmeta(source)

    print(f"Wklejono {files} plik(ow) z {source}")
    print("Teraz: scripts/build-resourcepack.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
