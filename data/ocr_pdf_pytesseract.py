#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pytesseract
from pdf2image import convert_from_path


def ocr_pdf(pdf_path: Path, out_txt_path: Path, lang: str, dpi: int) -> None:
    pages = convert_from_path(str(pdf_path), dpi=dpi)
    text_blocks: list[str] = []

    for i, page in enumerate(pages, start=1):
        page_text = pytesseract.image_to_string(page, lang=lang)
        text_blocks.append(f"--- page {i} ---\n{page_text.strip()}\n")

    out_txt_path.parent.mkdir(parents=True, exist_ok=True)
    out_txt_path.write_text("\n".join(text_blocks), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Простейший OCR PDF -> TXT с использованием pytesseract."
    )
    parser.add_argument(
        "--input-dir",
        default="data/raw",
        help="Папка с PDF файлами (по умолчанию: data/raw).",
    )
    parser.add_argument(
        "--output-dir",
        default="data/ocr_text",
        help="Папка для .txt файлов (по умолчанию: data/ocr_text).",
    )
    parser.add_argument(
        "--lang",
        default="rus+eng",
        help="Языки Tesseract (по умолчанию: rus+eng).",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="DPI при рендере страниц PDF (по умолчанию: 300).",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    pdf_files = sorted(input_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"PDF не найдены в: {input_dir}")
        return

    for pdf in pdf_files:
        out_file = output_dir / f"{pdf.stem}.txt"
        print(f"OCR: {pdf.name} -> {out_file}")
        ocr_pdf(pdf, out_file, args.lang, args.dpi)

    print("Готово.")


if __name__ == "__main__":
    main()
