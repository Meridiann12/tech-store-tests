# Tech Store — микросервисы (Практическая работа №7)

Шесть микросервисов предметной области «Tech Store» (интернет-магазин техники):
**User Service, Catalog Service, Inventory Service, Order Service, Payment Service, Review Service**.

Каждый сервис — отдельное приложение **FastAPI** со своим `Dockerfile`, вся система
поднимается одной командой **Docker Compose** вместе с **PostgreSQL** и **RabbitMQ**.

Стек (строго по методичке): Python 3.10, FastAPI + Uvicorn, HTTP `requests`
(синхронное взаимодействие), RabbitMQ + `aio_pika` (асинхронные события),
PostgreSQL + SQLAlchemy (ORM), Docker + Docker Compose, Swagger UI (`/docs`).

## Тестирование (Практическая работа №8)

Реализованы два вида pre-deployment тестирования: **unit-тесты** и
**компонентные (e2e) тесты**. Инструменты: `pytest`, `requests`;
для unit-тестов Order Service — `unittest.mock`.

- **Unit-тесты** лежат внутри каждого сервиса (`<service>/tests/unit/`) и
  прогоняются отдельно — каждый сервис имеет собственный независимый набор
  тестов. Проверяются pydantic-модели и бизнес-логика; внешние зависимости
  подменяются: локальный (in-memory) репозиторий внедряется через конструктор
  (Dependency Injection), HTTP-вызов Catalog Service в Order Service заменён
  моком `requests.get`, репозиторий PostgreSQL — классом `FakeOrderRepo` с тем
  же интерфейсом.
- **Компонентные тесты** лежат в корне (`tests/component/`) и проверяют сервисы
  «снаружи», через внешний HTTP-контракт: фикстуры поднимают реальные процессы
  uvicorn (порты 8001–8006) и тесты общаются с ними через `requests`.
  Order Service тестируется в связке с реальным Catalog Service; для
  изолированного прогона `POSTGRES_URL` указывает на SQLite (репозиторий
  реализован поверх SQLAlchemy и не привязан к диалекту СУБД; в docker compose
  тот же код работает с PostgreSQL). RabbitMQ в прогоне не участвует —
  асинхронные события не доставляются, соответствующие ветки покрыты
  unit-тестами сервисов.

Запуск всех тестов: `./run_tests.sh` (Windows: `run_tests.bat`) или вручную:

```bash
pytest user_service/tests/unit -v        # unit-тесты User Service
pytest catalog_service/tests/unit -v     # ...и так для каждого сервиса
pytest tests/component -v                # компонентные (e2e) тесты
```

Требования для тестов: `pip install pytest` (остальные зависимости — как у сервисов:
`fastapi`, `uvicorn`, `pydantic-settings`, `aio-pika`, `sqlalchemy`, `requests`).

## Структура проекта

```
tech-store/
├── docker-compose.yaml          # оркестрация: 6 сервисов + PostgreSQL + RabbitMQ
├── pytest.ini                   # тесты по умолчанию: tests/component
├── run_tests.sh / run_tests.bat # запуск всех тестов (ПР №8)
├── user_service/                # пользователи (порты: 8001)
├── catalog_service/             # каталог товаров (8002)
├── inventory_service/           # склад: остатки и резервы (8003)
├── order_service/               # заказы: PostgreSQL + SQLAlchemy (8004)
├── payment_service/             # платежи (8005)
├── review_service/              # отзывы (8006)
├── <service>/tests/unit/        # unit-тесты каждого сервиса (ПР №8)
├── tests/component/             # компонентные (e2e) тесты системы (ПР №8)
└── <service>/app/               # слои каждого сервиса (как в методичке)
    ├── main.py                  # FastAPI + подключение consumer к startup
    ├── settings.py              # pydantic-settings (AMQP_URL, POSTGRES_URL...)
    ├── models/                  # анемичные pydantic-модели
    ├── repositories/            # хранение данных (память / SQLAlchemy)
    ├── services/                # бизнес-логика
    ├── endpoints/               # HTTP-контроллеры (роутеры)
    └── rabbitmq.py              # consumer + публикация событий
```

## Требования

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Docker + Compose v2) — обязательно.
- VS Code — по желанию (удобно смотреть код и Swagger).

## Быстрый запуск

В корне проекта (рядом с `docker-compose.yaml`):

```bash
docker compose up --build
```

Первый запуск скачает образы и соберёт контейнеры (2–5 минут). Готовность видно по строкам
в логах: `Started RabbitMQ consuming...` у всех сервисов и `[OK] Схема БД готова` у order_service.

Остановка: `Ctrl+C` или `docker compose down` (данные PostgreSQL сохраняются в volume;
`docker compose down -v` — удалить всё вместе с базой).

## Адреса сервисов

| Сервис | Swagger UI | Назначение |
| --- | --- | --- |
| User Service | http://localhost:8001/docs | регистрация и удаление пользователей |
| Catalog Service | http://localhost:8002/docs | товары каталога, рейтинги |
| Inventory Service | http://localhost:8003/docs | остатки, приёмка, резервы |
| Order Service | http://localhost:8004/docs | заказы (хранятся в PostgreSQL) |
| Payment Service | http://localhost:8005/docs | транзакции и оплата |
| Review Service | http://localhost:8006/docs | отзывы и модерация |
| RabbitMQ UI | http://localhost:15672 | логин `admin`, пароль `admin123` |
| PostgreSQL | localhost:5432 | `myuser` / `pgpwd`, база `orders_db` |

---

## Последовательность проверки (для скриншотов в отчёт)

Выполняйте шаги по порядку — каждое действие использует результат предыдущего.
Удобно делать через Swagger UI (`/docs`), но ниже приведены готовые curl-команды.

### Шаг 1. Пользователи (User Service, :8001)

```bash
curl -X POST http://localhost:8001/api/users \
  -H "Content-Type: application/json" \
  -d '{"email": "client@example.com", "full_name": "Иван Иванов"}'
```

В ответе — JSON пользователя, **сохраните `id`** (начинается с 42). Проверьте:
`GET http://localhost:8001/api/users/{id}`.
*Что снимаем:* ответ POST (создан пользователь), в логах контейнера user_service —
`[PUBLISHED] notifications :: ` и `users :: user.registered` (событие user.registered).

### Шаг 2. Каталог (Catalog Service, :8002)

```bash
curl -X POST http://localhost:8002/api/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Смартфон X", "category_id": 10, "price": 59990}'
```

Товар получит **id = 501**. Проверьте: `GET http://localhost:8002/api/products/501`.
Обновление цены: `PUT /api/products/501` с телом `{"price": 54990}` (событие product.updated).
*Что снимаем:* ответ POST с товаром; в inventory_service в этот момент создаётся
остаток с нулём — видно по следующему шагу.

### Шаг 3. Склад (Inventory Service, :8003)

```bash
curl http://localhost:8003/api/inventory/501        # quantity: 0 (создано по product.created)
curl -X POST http://localhost:8003/api/inventory/501/supply \
  -H "Content-Type: application/json" -d '{"amount": 10}'
```

*Бизнес-правило:* если после приёмки остаток ниже порога 5 (например `{"amount": 3}`),
Inventory публикует `inventory.low_stock` в fanout-обменник notifications.
*Что снимаем:* остаток до/после приёмки.

### Шаг 4. Заказ — ключевое требование (Order Service, :8004)

```bash
curl -X POST http://localhost:8004/api/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": 42, "items": [{"product_id": 501, "quantity": 2}]}'
```

В ответе `items` уже содержат `price: 59990` и `name` — эти данные **Order Service получил
синхронным HTTP-запросом к Catalog Service** (библиотека `requests`) — это требование
«вызов методов другого сервиса». Статус заказа: `CREATED`. Сохраните `id` заказа (начнётся с 1).

Через 1–2 секунды проверьте:

```bash
curl http://localhost:8004/api/orders/1       # статус уже READY_FOR_PAYMENT
curl http://localhost:8003/api/inventory/501  # reserved: 2
```

Статус сменился сам: Inventory обработал `order.created`, зарезервировал товар и
отправил `inventory.reserved`, Order обновил статус из очереди (RabbitMQ).
*Что снимаем:* ответ POST (CREATED) и повторный GET (READY_FOR_PAYMENT) — «до/после».

### Шаг 5. Оплата (Payment Service, :8005)

```bash
curl http://localhost:8005/api/payments/1     # транзакция PENDING (создана по order.created)
curl -X POST http://localhost:8005/api/payments/1/pay
curl http://localhost:8004/api/orders/1       # статус PAID (пришло payment.completed)
```

*Бизнес-правило:* платёж на сумму больше **200 000 руб.** отклоняется —
`payment.failed` (reason: insufficient_funds), заказ уйдёт в `CANCELLED`.
*Что снимаем:* GET платежа (PENDING), ответ POST pay (PAID), GET заказа (PAID).

### Шаг 6. Отзывы (Review Service, :8006)

```bash
curl -X POST http://localhost:8006/api/reviews \
  -H "Content-Type: application/json" \
  -d '{"product_id": 501, "user_id": 42, "rating": 5, "text": "Отличный телефон!"}'
curl http://localhost:8006/api/reviews/product/501
curl -X POST http://localhost:8006/api/reviews/9001/moderate \
  -H "Content-Type: application/json" -d '{"approve": true}'
curl http://localhost:8002/api/products/501   # rating: 5.0
```

Отзыв получит **id = 9001**. Рейтинг товара пересчитал Catalog Service —
он обработал событие `review.created` из очереди catalog_queue.
*Что снимаем:* создание отзыва, модерация, товар с обновлённым rating.

### Шаг 7. Отказоустойчивые сценарии (для полноты отчёта)

- **Недостаточно товара** (`inventory.failed`): создайте заказ с `quantity` больше остатка
  (например 50) — статус заказа станет `CANCELLED`, в логах inventory_service — missing_products.
- **Возврат средств** (`payment.refunded`): оплатите новый заказ, затем
  `POST http://localhost:8004/api/orders/{id}/cancel` — Payment вернёт средства,
  заказ получит статус `RETURNED`.
- **Анонимизация** (`user.deleted`): `DELETE http://localhost:8001/api/users/42` —
  Review Service обезличит отзывы (user_id → null), Order — заказы (user_id → 0).

### Шаг 8. RabbitMQ (для раздела про брокер)

Откройте http://localhost:15672 (`admin` / `admin123`):

- **Exchanges**: `orders`, `inventory`, `payments`, `catalog`, `reviews` (topic),
  `notifications` (fanout) — ровно как в описании сообщений из ПР №5.
- **Queues**: `inventory_queue`, `order_queue`, `payment_queue`, `review_queue` (durable),
  `catalog_queue` (auto-delete).
*Что снимаем:* список exchanges и список queues.

### Шаг 9. Проверка работы с БД (Order Service + PostgreSQL)

```bash
docker compose restart order_service
curl http://localhost:8004/api/orders/1   # заказ на месте - данные пережили перезапуск
```

Подключиться к базе напрямую: `localhost:5432`, пользователь `myuser`, пароль `pgpwd`,
база `orders_db`, таблица `orders` (удобно через DBeaver или расширение Database Client
в VS Code). *Что снимаем:* таблицу orders с сохранёнными заказами.

---

## Соответствие требованиям задания

| Требование | Где реализовано |
| --- | --- |
| Реализовать все описанные ранее микросервисы | 6 сервисов Tech Store (User, Catalog, Inventory, Order, Payment, Review) |
| 2–5 эндпоинтов в каждом сервисе | по 3 эндпоинта в каждом (см. Swagger `/docs`) |
| В одном сервисе эндпоинт вызывает методы другого сервиса | `POST /api/orders` (Order Service) вызывает `GET /api/products/{id}` (Catalog Service) по HTTP (`requests`) для получения цен |
| Хотя бы один сервис работает с БД | Order Service: PostgreSQL + SQLAlchemy (таблица orders), схема создаётся при старте |
| Упаковать каждый сервис в отдельный контейнер | свой `Dockerfile` у каждого сервиса (python:3.10, uvicorn) |
| Запуск через Docker Compose | `docker-compose.yaml`: 6 сервисов + PostgreSQL + RabbitMQ, команда `docker compose up --build` |

## Как устроен код (по методичке)

- **models** — анемичные модели (pydantic): только данные.
- **repositories** — управление хранением: скрывают источник данных от бизнес-логики
  (локальный список в памяти; в Order Service — SQLAlchemy + PostgreSQL).
- **services** — бизнес-логика и правила предметной области.
- **endpoints** — HTTP-контроллеры (синхронное взаимодействие).
- **rabbitmq.py** — consumer: обработчики сообщений из очередей (асинхронное
  взаимодействие) и публикация исходящих событий. Подключается к основному циклу
  в обработчике `startup`, как в методичке.
- `msg.ack()` подтверждает успешную обработку; при ошибке — `msg.nack()`,
  сообщение возвращается в очередь.

События, тела сообщений и настройки очередей соответствуют описанию из
Практической работы №5 («Описание сообщений межсервисного взаимодействия»):
topic-обменники `orders`, `inventory`, `payments`, `catalog`, `reviews`,
fanout `notifications`, durable-очереди `order_queue`, `inventory_queue`,
`payment_queue`, `review_queue`, auto-delete `catalog_queue`.

Для наглядности идентификаторы совпадают с примерами отчёта:
товары — с 501, платежи — с 555, отзывы — с 9001, пользователи — с 42.

## Запуск без Docker (по желанию, для отладки в VS Code)

```bash
cd <service_dir>
python -m venv venv
./venv/Scripts/Activate.ps1          # Windows (Linux/macOS: source venv/bin/activate)
pip install -r requirements.txt
uvicorn app.main:app --port 8001     # порт своего сервиса из таблицы выше
```

Если RabbitMQ/PostgreSQL не запущены, сервис всё равно поднимется и ответит по HTTP —
в логах появится `[WARN] RabbitMQ недоступен...` (асинхронные события не обрабатываются).
Для order_service дополнительно нужен PostgreSQL и запущенный catalog_service;
настройки можно задать файлом `.env` (пример — `order_service/.env.example`).
