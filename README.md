# Word Frequency Report API

FastAPI-сервис для частотного анализа текстовых файлов с экспортом результатов в Excel (xlsx).

## Архитектура: DDD (Domain-Driven Design)

```
app/
├── domain/                         # Бизнес-логика (ядро, без зависимостей)
│   ├── entities/
│   │   └── word_frequency.py       # Агрегат: WordFrequency
│   └── services/
│       ├── lemmatizer_port.py      # Port (ABC): ILemmatizer
│       └── frequency_analysis_service.py  # Domain-сервис
│
├── application/                    # Use-cases (оркестрация)
│   └── use_cases/
│       └── export_report.py        # ExportReportUseCase
│
├── infrastructure/                 # Адаптеры (реализации портов)
│   ├── nlp/
│   │   └── pymorphy3_lemmatizer.py # Адаптер: pymorphy3 → ILemmatizer
│   ├── excel/
│   │   └── excel_report_builder.py # Построитель xlsx
│   └── file_processing/
│       └── stream_reader.py        # Потоковое чтение файлов
│
└── api/                            # Транспортный слой (FastAPI)
    ├── routers/
    │   └── report_router.py        # POST /public/report/export
    ├── dependencies/
    │   └── executor.py             # Shared ProcessPoolExecutor
    └── main.py                     # Точка входа
```

## Ключевые архитектурные решения

### Обработка больших файлов
- **Потоковое чтение** (`iter_lines_async`): файл читается чанками по 64 KB, не загружаясь целиком в память.
- **Батчевая обработка**: строки группируются по 5 000 и отправляются в пул процессов порциями.

### Многопользовательская нагрузка
- **ProcessPoolExecutor**: тяжёлая CPU-работа (лемматизация) выполняется в отдельных процессах, не блокируя event loop uvicorn. Другие запросы продолжают обслуживаться.
- **Ограниченный пул**: `max_workers = min(4, cpu_count // 2)` — половина ядер остаётся для обработки входящих запросов.
- **Один uvicorn worker**: при горизонтальном масштабировании запускаются несколько контейнеров (или `--workers N` за nginx).

### Лемматизация
Используется `pymorphy3` — морфологический анализатор для русского языка. «Житель» и «жителем» приводятся к одной лемме `житель`.

## Запуск

### Локально
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Docker
```bash
docker-compose up --build
```

## Использование API

```
POST /public/report/export
Content-Type: multipart/form-data
Body: file=<текстовый файл>
```

### curl
```bash
curl -X POST "http://localhost:8000/public/report/export" \
  -F "file=@document.txt" \
  --output report.xlsx
```

### Python
```python
import requests

with open("document.txt", "rb") as f:
    r = requests.post(
        "http://localhost:8000/public/report/export",
        files={"file": ("document.txt", f, "text/plain")},
    )
r.raise_for_status()
with open("report.xlsx", "wb") as out:
    out.write(r.content)
```

## Формат выходного файла

| Словоформа (лемма) | Кол-во в документе | Кол-во по строкам |
|--------------------|-------------------|-------------------|
| житель             | 45                | 3,0,11,0,31       |
| город              | 30                | 1,5,0,24,0        |

- Строки отсортированы по убыванию частоты.
- Колонка «Кол-во по строкам» содержит счётчик для каждой строки документа через запятую.

## Тесты

```bash
python -m unittest tests/test_domain.py -v
```
