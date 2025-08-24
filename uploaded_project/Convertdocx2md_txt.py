#!/usr/bin/env python3
import argparse
import pathlib
import sys
from typing import Iterable, List
import pypandoc

def find_inputs(input_path: pathlib.Path, recursive: bool) -> List[pathlib.Path]:
    if input_path.is_file():
        if input_path.suffix.lower() != ".docx":
            raise ValueError(f"Eingabedatei ist keine .docx: {input_path}")
        return [input_path]
    if not input_path.exists():
        raise FileNotFoundError(f"Pfad nicht gefunden: {input_path}")
    pattern = "**/*.docx" if recursive else "*.docx"
    return list(input_path.glob(pattern))

def convert_one(src: pathlib.Path, out_dir: pathlib.Path, fmt: str, overwrite: bool, wrap: str):
    out_dir.mkdir(parents=True, exist_ok=True)
    ext = ".md" if fmt == "md" else ".txt"
    dst = (out_dir / src.with_suffix(ext).name) if out_dir else src.with_suffix(ext)

    if dst.exists() and not overwrite:
        print(f"[Skip] Existiert bereits: {dst}")
        return

    extra_args = []
    if fmt == "md":
        # sauberes Markdown, keine harte Zeilenumbrüche
        extra_args = ["--standalone", "--wrap=none"]
    else:  # txt / plain
        # Plaintext ohne Umbrüche mitten im Satz
        extra_args = ["--wrap=" + wrap]

    try:
        pypandoc.convert_file(
            str(src),
            "markdown" if fmt == "md" else "plain",
            outputfile=str(dst),
            extra_args=extra_args
        )
        print(f"[OK] {src.name} -> {dst}")
    except OSError as e:
        # Häufig: Pandoc fehlt
        print(f"[Fehler] {src}: {e}")
        print("Tipp: Pandoc automatisch laden mit:\n  python -c \"import pypandoc; pypandoc.download_pandoc()\"")
    except Exception as e:
        print(f"[Fehler] {src}: {e}")

def main(argv: Iterable[str] = None) -> int:
    ap = argparse.ArgumentParser(description="DOCX -> Markdown oder TXT Konverter (Pandoc).")
    ap.add_argument("-i", "--input", required=True, help="Datei oder Ordner mit .docx")
    ap.add_argument("-o", "--output", default="", help="Ausgabe-Ordner (optional)")
    ap.add_argument("--format", choices=["md", "txt"], required=True, help="Ziel-Format")
    ap.add_argument("--recursive", action="store_true", help="Ordner rekursiv durchsuchen")
    ap.add_argument("--overwrite", action="store_true", help="Vorhandene Dateien überschreiben")
    ap.add_argument("--wrap", default="none", choices=["auto", "none", "preserve"],
                    help="Zeilenumbruch-Verhalten für txt/plain (default: none)")
    args = ap.parse_args(list(argv) if argv is not None else None)

    in_path = pathlib.Path(args.input)
    out_dir = pathlib.Path(args.output) if args.output else pathlib.Path.cwd()

    files = find_inputs(in_path, args.recursive)
    if not files:
        print("Keine .docx-Dateien gefunden.")
        return 1

    for f in files:
        convert_one(f, out_dir, args.format, args.overwrite, args.wrap)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
