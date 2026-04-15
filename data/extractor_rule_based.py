#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except Exception:  # pragma: no cover
    Draft202012Validator = None

try:
    import pytesseract
    from pdf2image import convert_from_path
except Exception:  # pragma: no cover
    pytesseract = None
    convert_from_path = None


PASSPORT_RE = re.compile(
    r"\b[A-ZА-ЯЁ]{2,6}\.?\d{2,6}(?:\.\d{2,6})+(?:-\d{2})?\s*(?:ПС|1С|IС|IC)\b",
    re.IGNORECASE,
)
DOC_DOTTED_RE = re.compile(
    r"\b[A-ZА-ЯЁ]{1,8}\.?\d{2,6}(?:\.\d{2,6})+(?:-[A-ZА-Я0-9]{1,6})?(?:РЭ|ПС|ТУ)?\b",
    re.IGNORECASE,
)
DOC_COMPACT_RE = re.compile(r"\b[A-ZА-ЯЁ]\d{4,}[A-ZА-ЯЁ]{1,3}\b", re.IGNORECASE)
CABINET_CODE_RE = re.compile(r"\(([A-Z0-9\-]{6,})\)")
FACTORY_RE = re.compile(
    r"(?:зав\.?\s*№|заводской\s*номер)\s*[:\-]?\s*(б\/н|[A-ZА-Я0-9][A-ZА-Я0-9\-\/]{2,})",
    re.IGNORECASE,
)
ISSUE_DATE_RE = re.compile(r"(\d{2})[./-](\d{2})[./-](\d{2,4})")
DATE_LABEL_RE = re.compile(
    r"(?:дата\s*выпуска|дата\s*изготовления)\s*[:\-]?\s*([0-3]?\d[./-][01]?\d[./-]\d{2,4})",
    re.IGNORECASE,
)
ROW_START_RE = re.compile(r"^\s*(\d{1,3})\.\s*(.+)$")
ROW_BRACKET_RE = re.compile(r"^[\W_]*\[?\s*(\d{1,3})\s*[\]\)|\[]\s+(.+)$")
ROW_TABLE_ALT_RE = re.compile(r"^\s*.{0,12}\[\s*(\d{1,3})\b\s*(.+)$")
SECTION_NUM_RE = re.compile(r"^\s*\d{1,3}\.\d+\b")
PAGES_CERT_RE = re.compile(
    r"(б\/н|-|[A-ZА-Я0-9.\-]{3,})\s+(\d+)\s*(?:стр\.?|лист(?:ов)?)\s*([0-9\-]+)?\s*$",
    re.IGNORECASE,
)
PASSPORT_PHRASE_RE = re.compile(
    r"\bПаспорт\s+[A-ZА-ЯЁ0-9.\- ]{4,}",
    re.IGNORECASE,
)
SIMPLE_PS_RE = re.compile(
    r"\bПС\s*[-–—:]?\s*([A-ZА-ЯЁ0-9][A-ZА-ЯЁ0-9.\-\/]{2,})\b",
    re.IGNORECASE,
)
DOC_ID_CANDIDATE_RE = re.compile(r"\b([A-ZА-ЯЁ0-9][A-ZА-ЯЁ0-9.\-\/]{5,})\b", re.IGNORECASE)


MANUFACTURER_LEGAL_RE = re.compile(
    r"\b(?:АО|ООО|ПАО|ЗАО|ОАО)\s*[«\"]?[^,\n\"»]{2,100}[»\"]?",
    re.IGNORECASE,
)
MANUFACTURER_FULL_RE = re.compile(
    r"(?:Акционерное общество|Общество с ограниченной ответственностью)\s+[^\n,]{2,120}",
    re.IGNORECASE,
)
MANUFACTURER_LABEL_RE = re.compile(
    r"(?:предприятие\s*-\s*изготовитель|изготовитель)\s*[:\-]?\s*(.+)",
    re.IGNORECASE,
)


MIN_YEAR = 1990
MAX_YEAR = 2026
TABLE_HEADER_HINTS = [
    r"№\s*п/?п",
    r"наименование документа",
    r"заводск\w*\s*номер",
    r"страниц",
    r"сертификат",
    r"код позиции",
    r"кол-во",
    r"наличие паспорт",
    r"сертиф",
]
TABLE_STRUCTURE_HINTS = [
    r"код позиции",
    r"кол-во",
]
PRIMARY_TABLE_MARKERS = [
    r"№\s*п/?п",
    r"наименование документа",
    r"перечень документации",
    r"код позиции",
]


def norm_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def normalize_passport_number(value: str) -> str:
    token = norm_space(value).upper().replace(" ", "")
    # Частая OCR-ошибка: финальное "ПС" распознаётся как "1С"/"IC"/"IС".
    token = re.sub(r"(1С|IC|IС)$", "ПС", token)
    return token


def normalize_factory_number(value: str | None) -> str | None:
    if value is None:
        return None
    token = norm_space(value)
    if not token:
        return None
    low = token.lower()
    if low == "б/н":
        return "б/н"
    if "заводской" in low:
        return None
    if not any(ch.isdigit() for ch in token):
        return None
    return token


def _parse_date_token(token: str) -> date | None:
    m = ISSUE_DATE_RE.search(token)
    if not m:
        return None
    dd, mm, yy = m.groups()
    year = int(yy) if len(yy) == 4 else int(f"20{yy}")
    month = int(mm)
    day = int(dd)

    if year < MIN_YEAR or year > MAX_YEAR:
        return None
    try:
        return date(year, month, day)
    except ValueError:
        return None


def parse_issue_date(text: str) -> str | None:
    # Сначала берём даты рядом с явными маркерами "дата выпуска/изготовления".
    labeled = DATE_LABEL_RE.findall(text)
    for token in labeled:
        parsed = _parse_date_token(token)
        if parsed:
            return parsed.isoformat()

    # Без явного маркера дату не заполняем, чтобы не брать случайные даты из текста.
    return None


def find_pdf_for_txt(txt_path: Path, pdf_dirs: list[Path]) -> Path | None:
    pdf_name = txt_path.with_suffix(".pdf").name
    for directory in pdf_dirs:
        candidate = directory / pdf_name
        if candidate.exists():
            return candidate
    return None


def extract_layout_text_from_pdf(pdf_path: Path, lang: str = "rus+eng", dpi: int = 350) -> str | None:
    if pytesseract is None or convert_from_path is None:
        return None

    pages = convert_from_path(str(pdf_path), dpi=dpi)
    all_lines: list[str] = []

    for page in pages:
        data = pytesseract.image_to_data(
            page,
            lang=lang,
            output_type=pytesseract.Output.DICT,
            config="--oem 3 --psm 6",
        )
        words: list[tuple[float, int, str]] = []
        for i, token in enumerate(data.get("text", [])):
            text = norm_space(token)
            if not text:
                continue
            try:
                conf = float(data["conf"][i])
            except Exception:
                conf = -1
            if conf < 0:
                continue
            x = int(data["left"][i])
            y = int(data["top"][i])
            h = int(data["height"][i])
            y_center = y + h / 2
            words.append((y_center, x, text))

        words.sort(key=lambda w: (w[0], w[1]))
        rows: list[dict] = []
        y_tolerance = 10

        for y_center, x, text in words:
            placed = False
            for row in rows:
                if abs(y_center - row["y"]) <= y_tolerance:
                    row["words"].append((x, text))
                    row["y"] = (row["y"] * row["count"] + y_center) / (row["count"] + 1)
                    row["count"] += 1
                    placed = True
                    break
            if not placed:
                rows.append({"y": y_center, "count": 1, "words": [(x, text)]})

        rows.sort(key=lambda r: r["y"])
        for row in rows:
            row_words = sorted(row["words"], key=lambda t: t[0])
            line = norm_space(" ".join(word for _, word in row_words))
            if line:
                all_lines.append(line)

    return "\n".join(all_lines) if all_lines else None


def is_grouped_table_document(text: str, file_name: str) -> bool:
    low = text.lower()
    strong_markers = (
        "перечень документации" in low
        or "шкаф общего назначения" in low
        or "групповой паспорт" in low
        or "групповой паспорт" in file_name.lower()
    )
    table_hint_hits = sum(1 for patt in TABLE_HEADER_HINTS if re.search(patt, low, re.IGNORECASE))
    structure_hits = sum(1 for patt in TABLE_STRUCTURE_HINTS if re.search(patt, low, re.IGNORECASE))
    primary_hits = sum(1 for patt in PRIMARY_TABLE_MARKERS if re.search(patt, low, re.IGNORECASE))

    row_count = 0
    for line in text.splitlines():
        if SECTION_NUM_RE.match(line):
            continue
        if ROW_START_RE.match(line) or ROW_BRACKET_RE.match(line) or ROW_TABLE_ALT_RE.match(line):
            row_count += 1

    has_item_table_signature = (
        "код позиции" in low and "наименование" in low and ("кол-во" in low or "кол-во факту" in low)
    )

    return bool(
        strong_markers
        or has_item_table_signature
        or (primary_hits >= 1 and structure_hits >= 1 and table_hint_hits >= 2 and row_count >= 3)
    )


def extract_top_passport_number(text: str, grouped_table: bool) -> str:
    if grouped_table:
        m = CABINET_CODE_RE.search(text)
        if m:
            return m.group(1)
        passport_matches = PASSPORT_RE.findall(text)
        if passport_matches:
            return normalize_passport_number(passport_matches[0])
        simple_ps = SIMPLE_PS_RE.search(text)
        if simple_ps:
            return normalize_passport_number(simple_ps.group(1))
        for m_doc in DOC_DOTTED_RE.finditer(text):
            token = norm_space(m_doc.group(0)).upper()
            if token.endswith(("ПС", "РЭ")) and not token.startswith("ГОСТ"):
                return token
        for line in text.splitlines()[:80]:
            clean = norm_space(line)
            if not clean or clean.startswith("--- page"):
                continue
            candidate = DOC_ID_CANDIDATE_RE.search(clean)
            if not candidate:
                continue
            token = candidate.group(1).upper()
            if not any(ch.isalpha() for ch in token) or not any(ch.isdigit() for ch in token):
                continue
            return token
        return "UNKNOWN_PASSPORT"

    passport_matches = PASSPORT_RE.findall(text)
    if passport_matches:
        return normalize_passport_number(passport_matches[0])
    simple_ps = SIMPLE_PS_RE.search(text)
    if simple_ps:
        return normalize_passport_number(simple_ps.group(1))
    for m_doc in DOC_DOTTED_RE.finditer(text):
        token = norm_space(m_doc.group(0)).upper()
        if not token.startswith("ГОСТ"):
            return token
    for line in text.splitlines():
        m_compact = DOC_COMPACT_RE.search(line)
        if not m_compact:
            continue
        low = line.lower()
        if "паспорт" in low or "руководство" in low:
            return m_compact.group(0).upper()
    for line in text.splitlines()[:80]:
        clean = norm_space(line)
        if not clean or clean.startswith("--- page"):
            continue
        candidate = DOC_ID_CANDIDATE_RE.search(clean)
        if not candidate:
            continue
        token = candidate.group(1).upper()
        if not any(ch.isalpha() for ch in token) or not any(ch.isdigit() for ch in token):
            continue
        return token
    return "UNKNOWN_PASSPORT"


def extract_manufacturer(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    low_text = text.lower()

    # 0) Иногда в OCR есть полное название без аббревиатуры.
    m_full = MANUFACTURER_FULL_RE.search(text)
    if m_full:
        candidate = norm_space(m_full.group(0))
        if "гарантирует" not in candidate.lower():
            return candidate

    # 1) Типовой случай: в документе есть "АО/ООО/ПАО ...".
    m_legal = MANUFACTURER_LEGAL_RE.search(text)
    if m_legal:
        candidate = norm_space(m_legal.group(0))
        if candidate not in {":", "-"} and "гарантирует" not in candidate.lower():
            return candidate

    # 2) Линия с маркером "изготовитель".
    for ln in lines:
        m = MANUFACTURER_LABEL_RE.search(ln)
        if not m:
            continue
        candidate = norm_space(m.group(1))
        m_legal_local = MANUFACTURER_LEGAL_RE.search(candidate)
        if m_legal_local:
            return norm_space(m_legal_local.group(0))
        if candidate and candidate not in {":", "-"} and "гарантирует" not in candidate.lower():
            return candidate

    # 3) Вариант OCR без кавычек: "AO ТеконГруп" и т.п.
    if "текон" in low_text:
        return "АО «ТеконГруп»"
    if "кэаз" in low_text:
        return "АО «КЭАЗ»"
    if "трэи" in low_text:
        return "АО «ТРЭИ»"
    if "бнрд." in low_text:
        return "АО «ТеконГруп»"
    if "visprom" in low_text:
        return "VISPROM"

    # 4) Фолбэк на строку после маркера, даже если без юр. формы.
    for ln in lines:
        m = MANUFACTURER_LABEL_RE.search(ln)
        if m:
            fallback = norm_space(m.group(1))
            if fallback and fallback not in {":", "-"} and "гарантирует" not in fallback.lower():
                return fallback

    return "UNKNOWN_MANUFACTURER"


def extract_cabinet(text: str, grouped_table: bool) -> dict | None:
    if not grouped_table:
        return None
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    name = next((ln for ln in lines if "шкаф" in ln.lower()), None)
    if name is None:
        # Для групповых паспортов без слова "шкаф" собираем имя из верхнего заголовка.
        upper_lines = [
            ln
            for ln in lines[:40]
            if len(ln) > 8 and not re.search(r"\d{2,}", ln) and not ln.startswith("--- page")
        ]
        title_candidates = [ln for ln in upper_lines if ln.upper() == ln]
        if title_candidates:
            name = norm_space(" ".join(title_candidates[:2]))
        else:
            name = next(
                (
                    ln
                    for ln in lines[:30]
                    if "паспорт" not in ln.lower()
                    and not ln.startswith("--- page")
                    and "заведующ" not in ln.lower()
                    and "волкову" not in ln.lower()
                ),
                "UNKNOWN_CABINET",
            )
    m_fact = FACTORY_RE.search(text)
    factory_number = normalize_factory_number(m_fact.group(1)) if m_fact else None
    return {"name": norm_space(name or "UNKNOWN_CABINET"), "factory_number": factory_number}


def parse_cabinet_items(text: str, top_passport_number: str) -> list[dict]:
    raw_lines = [ln.rstrip() for ln in text.splitlines()]
    lines: list[str] = []
    for raw in raw_lines:
        # Разбиваем строки с несколькими вшитыми маркерами вида "[2 ... [3 ... [4 ...".
        parts = re.split(r"(?=\[\s*\d{1,3}\b)", raw)
        lines.extend([p for p in parts if p.strip()])
    blocks: list[tuple[int, list[str]]] = []
    current_num: int | None = None
    current_lines: list[str] = []

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if SECTION_NUM_RE.match(line):
            continue
        m_row = ROW_START_RE.match(line) or ROW_BRACKET_RE.match(line) or ROW_TABLE_ALT_RE.match(line)
        if m_row:
            row_num = int(m_row.group(1))
            # Игнорируем странные прыжки нумерации, характерные для не-табличных разделов.
            if current_num is not None and row_num > current_num + 5:
                continue
            if current_num is not None:
                blocks.append((current_num, current_lines))
            current_num = row_num
            current_lines = [m_row.group(2)]
        elif current_num is not None:
            current_lines.append(line)
    if current_num is not None:
        blocks.append((current_num, current_lines))

    items = []
    for num, block_lines in blocks:
        block_text = norm_space(" ".join(block_lines))
        pass_m = PASSPORT_RE.search(block_text)
        item_passport = normalize_passport_number(pass_m.group(0)) if pass_m else top_passport_number

        # Убираем фразу "Паспорт <номер>" как отдельный маркер, но не трогаем "(Паспорт)" в имени.
        without_passport = PASSPORT_PHRASE_RE.sub("", block_text)
        without_passport = norm_space(without_passport)

        tail_matches = list(PAGES_CERT_RE.finditer(without_passport))
        factory_number = None
        pages_count = None
        certificate_count = None
        if tail_matches:
            t = tail_matches[-1]
            factory_token, pages_token, cert_token = t.group(1), t.group(2), t.group(3)
            factory_number = normalize_factory_number(factory_token if factory_token != "-" else None)
            pages_count = int(pages_token)
            if cert_token is not None:
                certificate_count = 0 if cert_token == "-" else int(cert_token)
            without_passport = norm_space(without_passport[: t.start()])

        name = norm_space(without_passport)
        name = re.split(
            r"\b(Количество мест|Габариты груза|Общий вес|Упаковка|Дополнительная информация|Прилагаемые документы)\b",
            name,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]
        name = norm_space(name) or "UNPARSED_ITEM"

        items.append(
            {
                "line_number": num,
                "name": name,
                "passport_number": item_passport,
                "factory_number": factory_number,
                "pages_count": pages_count,
                "certificate_count": certificate_count,
            }
        )

    # Фильтруем очевидный мусор: дубли номера строки и сильно "пустые" записи.
    filtered_items = []
    seen_rows: set[int] = set()
    for item in items:
        ln = item["line_number"]
        if ln in seen_rows:
            continue
        seen_rows.add(ln)
        filtered_items.append(item)
    items = filtered_items

    if not items:
        items = [
            {
                "line_number": 1,
                "name": "UNPARSED_ITEM",
                "passport_number": top_passport_number,
                "factory_number": None,
                "pages_count": None,
                "certificate_count": None,
            }
        ]
    return items


def parse_equipment_item(text: str, top_passport_number: str) -> list[dict]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    name = "UNPARSED_ITEM"
    for ln in lines:
        if "наименование изделия" in ln.lower():
            name = norm_space(ln.split(":", 1)[-1])
            break
    if name == "UNPARSED_ITEM":
        for ln in lines:
            low = ln.lower()
            if re.search(r"(модуль|контроллер|шкаф|розетка)", low) and len(ln) <= 140:
                name = norm_space(ln)
                break
    if name == "UNPARSED_ITEM":
        for ln in lines:
            low = ln.lower()
            if (
                len(ln) > 10
                and not ln.startswith("--- page")
                and "заведующ" not in low
                and "служебная записка" not in low
                and "код позиции" not in low
            ):
                name = norm_space(ln)
                break

    m_fact = FACTORY_RE.search(text)
    factory_number = normalize_factory_number(m_fact.group(1)) if m_fact else None

    return [
        {
            "line_number": 1,
            "name": name,
            "passport_number": top_passport_number,
            "factory_number": factory_number,
            "pages_count": None,
            "certificate_count": None,
        }
    ]


def build_record(txt_path: Path, pdf_dirs: list[Path], use_layout_for_tables: bool) -> dict:
    text = txt_path.read_text(encoding="utf-8", errors="ignore")
    grouped_table = is_grouped_table_document(text, txt_path.name)
    parsing_text = text
    used_layout = False

    if use_layout_for_tables and grouped_table:
        pdf_path = find_pdf_for_txt(txt_path, pdf_dirs)
        if pdf_path is not None:
            layout_text = extract_layout_text_from_pdf(pdf_path)
            if layout_text:
                parsing_text = layout_text
                used_layout = True

    if grouped_table:
        has_table_markers = any(
            re.search(patt, text, re.IGNORECASE)
            for patt in [r"№\s*п/?п", r"наименование документа", r"код позиции", r"перечень документации"]
        )
        # Для табличных документов берём данные из layout-текста (чтение слева-направо, сверху-вниз).
        top_passport_number = extract_top_passport_number(parsing_text, grouped_table=True)
        if has_table_markers:
            items = parse_cabinet_items(parsing_text, top_passport_number)
        else:
            items = parse_equipment_item(text, top_passport_number)
        # Если layout/OCR дал слишком мало строк таблицы, откатываемся на plain text.
        if has_table_markers and len(items) < 3:
            fallback_top = extract_top_passport_number(text, grouped_table=True)
            fallback_items = parse_cabinet_items(text, fallback_top)
            if len(fallback_items) > len(items):
                parsing_text = text
                used_layout = False
                top_passport_number = fallback_top
                items = fallback_items
    else:
        top_passport_number = extract_top_passport_number(text, grouped_table=False)
        items = parse_equipment_item(text, top_passport_number)

    manufacturer = extract_manufacturer(parsing_text)
    page_count = max(1, text.count("--- page"))

    return {
        "doc_type": "equipment_passport",
        "passport_number": top_passport_number,
        "issue_date": parse_issue_date(text),
        "manufacturer": manufacturer,
        "cabinet": extract_cabinet(text, grouped_table),
        "barcode": None,
        "items": items,
        "source": {
            "file_name": txt_path.with_suffix(".pdf").name,
            "page_count": page_count,
            "ocr_engine": "pytesseract-layout" if used_layout else "pytesseract",
            "ocr_confidence": None,
        },
        "notes": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rule-based extractor: OCR TXT -> JSON labels according to schema."
    )
    parser.add_argument("--input-dir", default="data/ocr_text")
    parser.add_argument("--output-dir", default="data/labels")
    parser.add_argument("--schema", default="schemas/schema.json")
    parser.add_argument(
        "--pdf-dirs",
        default="data/raw,zadanie",
        help="CSV list of directories with source PDF files for layout-aware table parsing.",
    )
    parser.add_argument(
        "--table-layout-mode",
        choices=["on", "off"],
        default="on",
        help="Use coordinate-based OCR ordering for grouped/table documents.",
    )
    args = parser.parse_args()

    root = Path.cwd()
    input_dir = root / args.input_dir
    output_dir = root / args.output_dir
    schema_path = root / args.schema
    pdf_dirs = [root / p.strip() for p in args.pdf_dirs.split(",") if p.strip()]
    use_layout_for_tables = args.table_layout_mode == "on"

    txt_files = sorted(input_dir.glob("*.txt"))
    if not txt_files:
        print(f"TXT files not found in: {input_dir}")
        return

    if use_layout_for_tables and (pytesseract is None or convert_from_path is None):
        print("WARN: table-layout-mode is ON, but pytesseract/pdf2image not installed. Fallback to text mode.")

    schema = None
    validator = None
    if schema_path.exists() and Draft202012Validator is not None:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema)

    output_dir.mkdir(parents=True, exist_ok=True)
    ok_count = 0

    for txt in txt_files:
        record = build_record(txt, pdf_dirs=pdf_dirs, use_layout_for_tables=use_layout_for_tables)
        out_path = output_dir / f"{txt.stem}.json"
        out_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

        if validator is not None:
            errors = sorted(validator.iter_errors(record), key=lambda e: list(e.path))
            if errors:
                print(f"INVALID {out_path.name}: {errors[0].message}")
                continue

        ok_count += 1
        print(f"OK {out_path.name}")

    print(f"Done. Generated: {len(txt_files)}, valid: {ok_count}")


if __name__ == "__main__":
    main()
