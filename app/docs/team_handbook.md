# Командный handbook (hackathon)

## 1) Working agreements

### Ветки и PR
- Базовый поток: `feature/*` -> PR в `dev` -> стабилизация -> merge `dev` -> `main` перед демо.
- Именование веток: `feature/<role>-<short-task>`, `fix/<short-task>`.
- Один PR = одна цель (без смешивания extractor/backend/frontend изменений).
- Перед PR обязательно приложить: что изменено, как проверено, какие файлы данных затронуты.

### Коммиты
- Формат: `<area>: <action>` (например, `extractor: improve cabinet table parsing`).
- Коммит должен быть атомарным и воспроизводимым (код + связанные изменения схемы/гайда в том же PR).
- Если меняется контракт, обновлять одновременно `schemas/schema.json` и `data/LABELING_GUIDE.md`.

### Комментарии в issues/PR
- Минимум: **контекст -> решение -> проверка -> риски**.
- Для спорных OCR/разметочных кейсов прикладывать путь к документу (`data/raw/...pdf`) и целевой JSON (`data/labels/...json` или `data/gold/...json`).

## 2) Dataset workflow: raw -> ocr_text -> labels -> gold -> reports

1. **Raw**: входные PDF в `data/raw/` (референсные материалы также в `zadanie/`).
2. **OCR**: генерация TXT в `data/ocr_text/`:
   ```bash
   python data/ocr_pdf_pytesseract.py --input-dir data/raw --output-dir data/ocr_text
   ```
3. **Labels (auto)**: извлечение JSON в `data/labels/`:
   ```bash
   python data/extractor_rule_based.py --input-dir data/ocr_text --output-dir data/labels --schema schemas/schema.json --pdf-dirs data/raw,zadanie --table-layout-mode on
   ```
4. **Gold (manual verified)**: ручная проверка/правка по правилам `data/LABELING_GUIDE.md`, сохранение эталона в `data/gold/`.
5. **Reports**: сводки качества складывать в `data/reports/` (например, сравнение `labels` vs `gold`, список UNKNOWN/UNPARSED полей).

Контрольный минимум перед handoff: JSON соответствует `schemas/schema.json`, а спорные поля отмечены и прокомментированы.

## 3) Naming/format conventions (schema + guide)

- Обязательные верхние поля: `doc_type`, `passport_number`, `manufacturer`, `items`, `source`.
- `issue_date`: строго `YYYY-MM-DD` или `null` (не строка `"null"`).
- `б/н` хранить **как строку** `"б/н"`, не заменять на `null`.
- Политика `UNKNOWN_*` (из extractor): допустимы технические маркеры `UNKNOWN_PASSPORT`, `UNKNOWN_MANUFACTURER`, `UNKNOWN_CABINET` для triage; в `gold` по возможности заменять фактическими значениями.
- Для нераспознанного названия позиции extractor ставит `UNPARSED_ITEM`; это сигнал на ручную проверку.
- Не путать `passport_number` документа и `items[].passport_number` позиции.
- Числовые поля (`line_number`, `pages_count`, `certificate_count`, `source.page_count`) — только числа/`null` по схеме.
- `additionalProperties: false`: лишние поля запрещены почти везде.

## 4) Типовые сбои extractor + troubleshooting checklist

### Частые проблемы
- `UNKNOWN_PASSPORT` / `UNKNOWN_MANUFACTURER`: OCR-шум или нет явных маркеров в тексте.
- Неверный `doc_type` (шкаф распознан как equipment или наоборот).
- Плохой разбор таблиц группового паспорта (мало `items`, шумные строки).
- Пропуск layout-режима из-за зависимостей (`pytesseract/pdf2image` не установлены).

### Checklist
1. Проверить наличие TXT в `data/ocr_text/` и маркеров страниц `--- page N ---`.
2. Перезапустить OCR с адекватным DPI (`--dpi 300/350`) и `--lang rus+eng`.
3. Перезапустить extractor с `--table-layout-mode on`; если результат хуже — проверить `off`.
4. Проверить, что исходный PDF найден по имени в `data/raw` или `zadanie` (параметр `--pdf-dirs`).
5. Провалидировать структуру JSON относительно `schemas/schema.json`.
6. Все UNKNOWN/UNPARSED кейсы переносить в ручную проверку и фиксировать в `data/gold/`.

## 5) Docker-first локальный workflow

Состояние репозитория сейчас: Docker-конфиги отсутствуют (нет `Dockerfile` и `docker-compose*.yml`), а в `docs/feature_matrix.md` контейнеризация помечена как **Planned**.

Правило команды:
1. **Сначала Docker**: если в ветке появляется compose-стек, запускать через `docker compose up --build` как основной путь.
2. **Сейчас (временно)**: локальный Python-runner через venv:
   ```bash
   python data/ocr_pdf_pytesseract.py ...
   python data/extractor_rule_based.py ...
   ```
3. Конфигурация путей и режимов хранится в CLI-аргументах скриптов (`--input-dir`, `--output-dir`, `--schema`, `--pdf-dirs`, `--table-layout-mode`).
4. Опционально на текущем этапе: backend/frontend/1C сервисы и их контейнеры (эти слои пока planned).

## 6) Handoffs между ролями

### Extractor/OCR/1C -> Backend
Передать:
- валидные JSON-кандидаты (`data/labels/*.json`),
- проблемные кейсы + объяснение (`UNKNOWN_*`, `UNPARSED_ITEM`),
- актуальный контракт `schemas/schema.json`.

### Backend -> Frontend
Передать:
- стабильный API-контракт полей, полностью согласованный со схемой,
- статусы документов (raw/labels/gold/ready),
- ошибки валидации в читаемом виде.

### Frontend -> Extractor/OCR/1C
Передать:
- список полей с частыми ручными правками,
- примеры документов, где extraction системно ошибается,
- обратную связь по обязательности/удобству представления полей.

### Общий критерий handoff
- Артефакты лежат в ожидаемых путях, проходят schema-check и понятны следующей роли без устных пояснений.

## 7) Минимальный daily sync template

Использовать короткий формат:

- **Сделано:**
  - ...
- **Blockers:**
  - ...
- **Следующее:**
  - ...

Рекомендация: в `Blockers` всегда указывать конкретный файл/путь/документ (например, `data/raw/<file>.pdf`, `data/labels/<file>.json`).
