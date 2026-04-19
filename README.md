# Gazprom Automation

Сервис для оцифровки PDF-паспортов оборудования:  
**PDF -> Vision LLM (Ollama/Qwen2.5-VL) -> структурированный JSON -> frontend-таблица/экспорт**.

## 1. Что внутри

- **Backend (FastAPI)**: принимает PDF, извлекает текст, вызывает LLM, валидирует схему.
- **Ollama**: хостит локальную Vision LLM-модель (`qwen2.5vl:7b` по умолчанию).
- **Frontend (React + Vite)**: загрузка PDF, просмотр карточек, экспорт в Excel.

---

## 2. Быстрый старт (рекомендуемый путь) — Docker Compose

### Требования

- Docker + Docker Compose

### Запуск

```bash
docker compose up -d --build
```

### Проверка, что сервисы поднялись

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
```

- `/health` -> backend жив
- `/health/ready` -> backend видит Ollama и нужную модель загруженной

> На **первом запуске** модель может скачиваться несколько минут.

### Остановка

```bash
docker compose down
```

### Важно про модель

Модель Ollama хранится в volume `ollama_data`, поэтому после перезапуска контейнеров она обычно **не скачивается заново**.

---

## 3. Локальный запуск backend (без Docker)

Из директории `backend`:

```bash
poetry install
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Если Ollama запущен локально на хосте:

```bash
export OLLAMA_HOST=http://localhost:11434
export OLLAMA_MODEL=qwen2.5vl:7b
```

---

## 4. Локальный запуск frontend

Из директории `frontend`:

```bash
npm install
npm run dev
```

По умолчанию frontend использует `VITE_UPLOAD_ENDPOINT=/api/passports/upload`.  
Для текущего backend endpoint нужно задать:

```bash
export VITE_API_URL=http://localhost:8000
export VITE_UPLOAD_ENDPOINT=/api/v1/passport
```

---

## 5. Переменные окружения

### Backend

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `OLLAMA_HOST` | `http://ollama:11434` | Адрес Ollama API |
| `OLLAMA_MODEL` | `qwen2.5vl:7b` | Имя visual-модели |
| `PDF_DPI` | `170` | DPI для рендера PDF перед анализом изображений (`100..300`) |

### Frontend

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `VITE_API_URL` | `""` | Базовый URL backend |
| `VITE_UPLOAD_ENDPOINT` | `/api/passports/upload` | Endpoint загрузки PDF (рекомендуется `/api/v1/passport`) |

---

## 6. API: как использовать

### POST `/api/v1/passport`

Принимает `multipart/form-data` с полем `file` (PDF).

Пример:

```bash
curl -X POST "http://localhost:8000/api/v1/passport" \
  -F "file=@/absolute/path/to/passport.pdf"
```

Типовые ответы:

- `200` — успешная оцифровка и валидный JSON
- `400` — загружен не-PDF
- `422` — ошибка извлечения/валидации данных

### GET `/health`

```bash
curl http://localhost:8000/health
```

### GET `/health/ready`

```bash
curl http://localhost:8000/health/ready
```

---

## 7. Тесты и базовые проверки

### Backend

```bash
cd backend
poetry run pytest -q
```

### Frontend

```bash
cd frontend
npm run lint
npm run build
```

---

## 8. Типовые сценарии использования

### Сценарий A: первый запуск проекта

1. `docker compose up -d --build`
2. Дождаться загрузки модели в Ollama (может занять время)
3. Проверить `/health/ready`
4. Отправить первый PDF на `/api/v1/passport`

### Сценарий B: повторная обработка PDF

1. Отправлять новые PDF на тот же endpoint
2. Повторные запросы обычно быстрее (после прогрева модели)

### Сценарий C: смена модели

1. Изменить `OLLAMA_MODEL` в `docker-compose.yaml` или env
2. Перезапустить backend:

```bash
docker compose up -d --build backend
```

3. Проверить `/health/ready`

### Сценарий D: запуск frontend + backend локально

1. Поднять backend/Ollama
2. Запустить frontend с `VITE_API_URL` и `VITE_UPLOAD_ENDPOINT=/api/v1/passport`
3. Загружать PDF через UI

---

## 9. Troubleshooting

### `could not open a new TTY: open /dev/tty`

Причина: запуск интерактивного launcher без TTY.  
Решение: запускать Ollama сервером (`ollama serve`) и/или через Docker Compose.

### `model '...' not found (404)`

Причина: модель не загружена.  
Решение: дождаться авто-pull на старте backend или вручную:

```bash
docker exec -it ollama_server ollama pull qwen2.5vl:7b
```

### Первый запрос очень долгий

Это нормально для первого прохода (скачивание/прогрев/загрузка в RAM).  
Проверьте логи `ollama_server`.

### `422` с ошибками валидации полей

Значит LLM вернула невалидные типы/поля.  
В проекте есть нормализация перед schema validation, но для сложных кейсов проверьте качество страниц PDF и промпт.

### `/health/ready` возвращает 503

Проверьте:
1. Доступен ли Ollama (`OLLAMA_HOST`)
2. Загружена ли модель (`OLLAMA_MODEL`)

---

## 10. Что не покрыто этим README

- CI/CD пайплайны
- Production deployment и инфраструктурные best practices
