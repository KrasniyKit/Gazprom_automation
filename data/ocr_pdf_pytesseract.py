#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

import pytesseract
from PIL import ImageFilter, ImageOps
from pdf2image import convert_from_path


def text_quality_ok(text: str, min_chars: int, min_words: int) -> bool:
    cleaned = text.strip()
    if len(cleaned) < min_chars:
        return False
    words = re.findall(r"[A-Za-zА-Яа-яЁё0-9]{2,}", cleaned)
    return len(words) >= min_words


def extract_native_text_pages(pdf_path: Path) -> list[str] | None:
    result = subprocess.run(
        ["pdftotext", "-layout", "-enc", "UTF-8", str(pdf_path), "-"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None

    raw_text = result.stdout or ""
    if not raw_text.strip():
        return None

    pages = [part.strip() for part in raw_text.split("\f")]
    while pages and not pages[-1]:
        pages.pop()
    return pages or None


def preprocess_for_ocr(page):
    gray = ImageOps.grayscale(page)
    gray = ImageOps.autocontrast(gray)
    gray = gray.filter(ImageFilter.MedianFilter(size=3))
    return gray.point(lambda x: 255 if x > 170 else 0, mode="L")


def ocr_page_best(page, lang: str) -> str:
    base = pytesseract.image_to_string(page, lang=lang).strip()
    preprocessed = pytesseract.image_to_string(
        preprocess_for_ocr(page),
        lang=lang,
    ).strip()

    if text_quality_ok(preprocessed, min_chars=80, min_words=15) and (
        len(preprocessed) > len(base) * 1.15
    ):
        return preprocessed
    return base


def ocr_pdf(
    pdf_path: Path,
    out_txt_path: Path,
    lang: str,
    dpi: int,
    prefer_native_text: bool,
    native_min_chars: int,
    native_min_words: int,
) -> None:
    native_pages = extract_native_text_pages(pdf_path) if prefer_native_text else None
    text_blocks: list[str] = []
    rendered_pages = None

    page_count = len(native_pages) if native_pages else 0
    if page_count == 0:
        rendered_pages = convert_from_path(str(pdf_path), dpi=dpi)
        page_count = len(rendered_pages)

    for i in range(page_count):
        native_text = native_pages[i] if native_pages and i < len(native_pages) else ""
        if text_quality_ok(native_text, min_chars=native_min_chars, min_words=native_min_words):
            page_text = native_text
        else:
            if rendered_pages is None:
                rendered_pages = convert_from_path(str(pdf_path), dpi=dpi)
            page_text = ocr_page_best(rendered_pages[i], lang=lang)
        text_blocks.append(f"--- page {i + 1} ---\n{page_text.strip()}\n")

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
    parser.add_argument(
        "--prefer-native-text",
        choices=["on", "off"],
        default="on",
        help="Сначала пытаться извлекать встроенный текст через pdftotext (по умолчанию: on).",
    )
    parser.add_argument(
        "--native-min-chars",
        type=int,
        default=120,
        help="Минимум символов на странице, чтобы принять встроенный текст без OCR.",
    )
    parser.add_argument(
        "--native-min-words",
        type=int,
        default=20,
        help="Минимум слов на странице, чтобы принять встроенный текст без OCR.",
    )
    parser.add_argument(
        "--recursive",
        choices=["on", "off"],
        default="off",
        help="Искать PDF рекурсивно во вложенных папках input-dir (по умолчанию: off).",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    search_glob = "**/*.pdf" if args.recursive == "on" else "*.pdf"
    pdf_files = sorted(input_dir.glob(search_glob))

    if not pdf_files:
        print(f"PDF не найдены в: {input_dir}")
        return

    for pdf in pdf_files:
        if args.recursive == "on":
            rel = pdf.relative_to(input_dir).with_suffix("")
            safe_name = "__".join(rel.parts)
            out_file = output_dir / f"{safe_name}.txt"
        else:
            out_file = output_dir / f"{pdf.stem}.txt"
        print(f"OCR: {pdf} -> {out_file}")
        ocr_pdf(
            pdf,
            out_file,
            args.lang,
            args.dpi,
            prefer_native_text=(args.prefer_native_text == "on"),
            native_min_chars=args.native_min_chars,
            native_min_words=args.native_min_words,
        )

    print("Готово.")


if __name__ == "__main__":
    main()
