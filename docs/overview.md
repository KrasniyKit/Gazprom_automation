# Обзор проекта (hackathon)

## 1) Назначение и цель
Проект решает задачу автоматизации обработки паспортов оборудования:
- извлечение данных из PDF (OCR);
- выделение структурированных полей паспорта и штрихкодов;
- подготовка данных для backend/frontend и выгрузки в 1C.

Цель хакатона: собрать рабочий end-to-end контур **PDF -> JSON по схеме -> API/UI -> 1C** с контролируемым качеством извлечения.

## 2) Текущее состояние (сделано)
Реализовано и доступно в репозитории:
- `schemas/schema.json` — единая JSON Schema для `equipment_passport` и `cabinet_passport`.
- `data/ocr_pdf_pytesseract.py` — OCR-конвертация PDF в TXT (`data/ocr_text/`).
- `data/extractor_rule_based.py` — rule-based извлечение полей из OCR-текста в JSON (`data/labels/`) + валидация по схеме.
- `data/LABELING_GUIDE.md` — правила ручной разметки и нормализации значений.
- `data/raw/` и `zadanie/` — исходные PDF задачи и приложения.
- `samples/valid.json`, `samples/invalid.json` — примеры валидного/невалидного формата.

Подготовлены каталоги под датасетный цикл (`data/ocr_text/`, `data/labels/`, `data/gold/`, `data/reports/`), но их наполненность зависит от текущего запуска пайплайна.

## 3) Архитектура: текущая и целевая
### Текущая (уже есть)
1. OCR слой: PDF -> TXT (`ocr_pdf_pytesseract.py`).
2. Extraction слой: TXT -> JSON (`extractor_rule_based.py`).
3. Контроль структуры: JSON Schema (`schemas/schema.json`) + guide для ручной проверки.

### Целевая (план)
1. OCR + extractor формируют candidate JSON.
2. Разметка/валидация формируют gold-данные.
3. Backend (FastAPI, планируется) выдает API для:
   - загрузки документов/результатов;
   - просмотра и правки извлеченных полей;
   - выдачи данных для интеграции.
4. Frontend (планируется) предоставляет интерфейс проверки/корректировки.
5. Интеграционный слой в 1C (планируется) принимает финальный валидированный payload.

## 4) Поток данных
`PDF -> OCR(TXT) -> Extractor(JSON labels) -> Проверка/разметка (gold) -> Backend API -> Frontend review -> Export/интеграция в 1C`

Практически по текущим путям:
- вход: `data/raw/*.pdf` (или `zadanie/*.pdf`);
- OCR-выход: `data/ocr_text/*.txt`;
- extractor-выход: `data/labels/*.json`;
- эталон/ручная верификация: `data/gold/*.json` (по процессу команды);
- далее: backend/frontend/1C — как следующий этап реализации.

## 5) Карта структуры репозитория
- `data/` — операционный контур обработки документов.
  - `raw/` — исходные PDF.
  - `ocr_text/` — OCR TXT (промежуточный артефакт).
  - `labels/` — автоизвлеченные JSON.
  - `gold/` — проверенные/эталонные JSON.
  - `reports/` — отчеты по качеству/валидации.
  - `extractor_rule_based.py` — основная логика rule-based extraction.
  - `ocr_pdf_pytesseract.py` — OCR-скрипт.
  - `LABELING_GUIDE.md` — правила разметки.
- `schemas/`
  - `schema.json` — контракт данных между extraction/backend/1C.
- `samples/`
  - `valid.json`, `invalid.json` — примеры для быстрой проверки схемы.
  - `validate.py` — утилита проверки JSON на соответствие схеме.
- `docs/`
  - `overview.md` — этот обзор.
- `zadanie/` — постановка и приложения хакатона (референсные материалы).

## 6) Границы ролей и точки интеграции
### Роль 1: Extractor/OCR/1C integration
Зона ответственности:
- качество OCR;
- качество извлечения и нормализации полей;
- поддержка `schema.json` совместно с backend;
- формат и протокол передачи в 1C.

Интерфейсы с другими ролями:
- **в backend:** стабильный JSON-контракт + коды ошибок/статусы валидации;
- **во frontend:** структура данных для экрана проверки;
- **в 1C:** финальный payload, маппинг полей, правила обязательности.

### Роль 2: Backend (FastAPI)
Зона ответственности (план):
- API загрузки/получения документов и результатов extraction;
- API валидации/сохранения правок;
- API передачи финальных данных в интеграционный контур.

Интерфейсы:
- принимает JSON по `schemas/schema.json`;
- отдает frontend данные в удобном для review формате;
- передает в 1C только валидированные записи.

### Роль 3: Frontend (+ возможно dataset)
Зона ответственности (план):
- UI для просмотра OCR/JSON, правки и подтверждения;
- визуализация статусов (raw/labels/gold/ready_for_1c);
- при необходимости — помощь в разметке датасета.

Интерфейсы:
- backend API (CRUD по документам/извлечению);
- единый словарь полей из `schema.json`.

## 7) Что сделать первым после `git clone`
1. Перейти в корень репозитория.
2. Подготовить Python-окружение (venv).
3. Установить зависимости, используемые скриптами: минимум `pytesseract`, `pdf2image`, `jsonschema` (+ системные зависимости Tesseract/Poppler).
4. Проверить входные PDF в `data/raw/`.
5. Запустить OCR:
   - `python data/ocr_pdf_pytesseract.py --input-dir data/raw --output-dir data/ocr_text`
6. Запустить extractor:
   - `python data/extractor_rule_based.py --input-dir data/ocr_text --output-dir data/labels --schema schemas/schema.json`
7. Проверить, что JSON валидны по `schemas/schema.json`; спорные кейсы перенести в ручную проверку (`data/gold/`).
8. Синхронизировать с backend/frontend формат обмена (по факту текущего `schema.json`) и зафиксировать изменения контракта перед интеграцией с 1C.

---

Статус реализации по слоям:
- **Реализовано:** OCR скрипт, rule-based extractor, схема, гайд разметки, набор исходных PDF.
- **Планируется/в работе:** FastAPI backend, frontend review-интерфейс, production-контур интеграции с 1C.
