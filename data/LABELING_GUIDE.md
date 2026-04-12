# Инструкция разметки (под `schemas/schema.json`)

## 1. Общие правила
1. Один исходный PDF = один JSON-файл разметки.
2. JSON должен проходить валидацию схемы без дополнительных полей.
3. Если OCR и PDF конфликтуют — приоритет у PDF.
4. Лишние ключи запрещены (`additionalProperties: false` почти везде).

## 2. Обязательные поля верхнего уровня
В каждом JSON обязаны быть:

- `doc_type`
- `passport_number`
- `manufacturer`
- `items`
- `source`

Если любого из них нет — файл невалиден.

## 3. Как заполнять верхний уровень

### `doc_type`
- `equipment_passport` — одиночный паспорт.
- `cabinet_passport` — групповой паспорт шкафа.

### `passport_number` (верхний уровень)
- Это номер текущего паспорта/документа целиком.
- Не путать с `items[].passport_number` (номер паспорта конкретной позиции).

### `issue_date`
- Формат строго `YYYY-MM-DD`.
- Если даты нет/нечитаема — `null`.

### `manufacturer`
- Обязательная непустая строка.
- Должен быть заполнен всегда.

### `notes`
- Свободный комментарий или `null`.

## 4. Поле `cabinet`
- Для `cabinet_passport` поле `cabinet` обязательно.
- Для `equipment_passport` можно не указывать или ставить `null`.

Внутри `cabinet`:
- `name` — обязательно.
- `factory_number` — строка или `null`.
- Значение `"б/н"` допустимо как строка.

## 5. Поле `barcode` (если заполняете)
Если `barcode` не `null`, то обязательны:
- `type`: только `Code39`, `Code128`, `EAN-13`
- `value`: непустая строка

## 6. Разметка `items[]`
`items` — массив позиций, минимум 1 элемент.

Каждый элемент:
- `name` — обязательно
- `passport_number` — обязательно
- `line_number` — `integer >= 1` или `null`
- `factory_number` — строка или `null` (`"б/н"` допустимо)
- `pages_count` — `integer >= 1` или `null`
- `certificate_count` — `integer >= 0` или `null`

## 7. Условные правила схемы (`allOf`)
1. Если `doc_type = "equipment_passport"` → в `items` максимум 1 запись.
2. Если `doc_type = "cabinet_passport"` → `cabinet` обязателен.

## 8. Поле `source` (обязательно)
Внутри обязательно:
- `file_name` — имя исходного PDF
- `page_count` — целое число `>= 1`

Опционально:
- `ocr_engine` — строка или `null`
- `ocr_confidence` — число от `0` до `1` или `null`

## 9. Нормализация значений
1. Обрезать пробелы по краям строк.
2. `"б/н"` хранить строкой, не превращать в `null`.
3. Не менять структуру номеров (`-`, `.`, `/` сохранять).
4. Пустые строки для обязательных полей не допускаются.

## 10. Что считается ошибкой
- Нет обязательных полей.
- Перепутаны верхний `passport_number` и `items[].passport_number`.
- Для `equipment_passport` больше одной записи в `items`.
- Для `cabinet_passport` отсутствует `cabinet`.
- `page_count = 0`, `line_number = 0`, `pages_count = 0`, отрицательный `certificate_count`.
- Значение `barcode.type` вне (`Code39`, `Code128`, `EAN-13`).
