# Gazprom Automation

Сервис оцифровки PDF-паспортов оборудования: **PDF -> Ollama (Qwen) -> JSON -> UI**.

## 0. **ВИДЕО И ПРЕЗЕНТАЦИЯ НАХОДЯТСЯ В** ```/docs```

## 1. Запуск всего проекта (пошагово)

### Шаг 1. Запуск всего приложения (frontend + backend + Ollama)

Из корня репозитория:

```bash
docker compose up -d --build
```

Проверка backend:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
```

### Шаг 2. Открыть сайт сервиса

Открыть в браузере: **http://localhost:8081**

### Шаг 3. Остановка

```bash
docker compose down
```

---

## 2. Что внутри

- **Backend (FastAPI)**: `POST /api/v1/passport`
- **Ollama**: модель по умолчанию `qwen2.5vl:7b`
- **Frontend (React + Vite + Nginx)**: загрузка PDF и просмотр результата

---

## 3. Переменные окружения 

### Backend

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `OLLAMA_HOST` | `http://ollama:11434` | Адрес Ollama |
| `OLLAMA_MODEL` | `qwen2.5:7b` | Имя модели |
| `PDF_DPI` | `170` | DPI рендера PDF (`100..300`) |

### Frontend
 
 - VITE_API_URL (build-time)
   - Базовый URL API, используется в сборке Vite (доступен как `import.meta.env.VITE_API_URL`).
   - Если пустая строка — фронт будет обращаться по относительным путям (через nginx proxy).
   - Пример: VITE_API_URL="http://backend:8000"
 
 - VITE_UPLOAD_ENDPOINT (build-time)
   - Путь или полный URL эндпойнта загрузки файлов, например /api/v1/passport или http://backend:8000/api/v1/passport.
   - Встраивается в бандл во время vite build.
   - Пример: VITE_UPLOAD_ENDPOINT="/api/v1/passport"
 
 > Важно: переменные, начинающиеся с VITE_, читаются в коде на этапе сборки. Изменение переменных после сборки не поменяет поведение уже собранного фронта.
 
 - API_UPSTREAM (runtime, nginx)
   - Используется в nginx.conf.template внутри фронт-контейнера — nginx будет проксировать запросы /api/* на этот хост:порт.
   - Пример в docker-compose.yml:
     
     services:
       frontend:
         build:
           context: ./frontend
           args:
             VITE_API_URL: ""
             VITE_UPLOAD_ENDPOINT: /api/v1/passport
         environment:
           API_UPSTREAM: backend:8000
     
   - Задаётся как переменная окружения контейнера (runtime) — её значение влияет на nginx proxy, а не на скомпилированный JS.
 
 #### Примечания
 - Для локальной разработки с vite dev можно использовать .env / .env.local с теми же переменными (Vite подхватит их).
 - Если фронт развёрнут в Docker и nginx проксирует запросы на backend, оставляй VITE_API_URL пустым и используй API_UPSTREAM для привязки к сервису в docker-compose.

---

## 4. API

### POST `/api/v1/passport`

```bash
curl -X POST "http://localhost:8000/api/v1/passport" \
  -F "file=@/absolute/path/to/passport.pdf"
```

Коды ответа:
- `200` — успех
- `400` — не PDF
- `422` — ошибка извлечения/валидации

### Health endpoints

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
```

---

## 5. Локальный запуск без Docker (опционально)

### Backend

```bash
cd backend
poetry install
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 6. Тесты

```bash
cd backend
poetry run pytest -q
```

---

## 7. Частые проблемы

- **`model ... not found`**  
  Модель не скачана:
  ```bash
  docker exec -it ollama_server ollama pull qwen2.5vl:7b
  ```

- **Очень долгий первый запрос**  
  Нормально для первого запуска (скачивание/прогрев модели).

- **`/health/ready` = 503**  
  Проверьте `OLLAMA_HOST`, `OLLAMA_MODEL` и логи `ollama_server`.
