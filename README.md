# Ипотечный ассистент

Бэкенд ассистента ипотечного банка. Проект к воркшопам второго модуля профессии
«LLM-разработчик» на Хекслете.

Архитектура и решения: [docs/architecture.md](docs/architecture.md), [docs/adr/](docs/adr/).

## Эталон по встречам

После каждой встречи здесь появляется тег с решением домашнего задания: `workshop-1`,
`workshop-2` и так далее.

```sh
git clone https://github.com/Obolduy/mortgage-assistant.git
cd mortgage-assistant
git fetch --tags

# начать следующий шаг с эталона
git checkout -b my-work workshop-1

# сравнить свое решение с эталоном
git diff workshop-1 -- app/
```

## Что есть сейчас (`workshop-1`)

- Каркас на FastAPI: типизированные настройки, пул соединений, структурные логи.
- Postgres с pgvector и Temporal в Docker Compose.
- Миграции SQL-файлами и свой раннер.
- Проверки живости и готовности.
- Таблица кредитов с пятью тестовыми кредитами.
- Калькулятор в целых копейках: график, досрочное погашение (сократить срок или платеж), смена
  даты платежа.
- `GET /loans/{id}` и `GET /loans/{id}/schedule`.

## Запуск

Нужны Python 3.12, [uv](https://docs.astral.sh/uv/) и Docker.

```sh
cp .env.example .env   # порт 5434 занят? поменяйте PG_PORT и DATABASE_URL
make install           # зависимости из uv.lock
make infra             # Postgres с pgvector и Temporal
make migrate           # повторный запуск напишет «Новых миграций нет»
make api               # http://localhost:8000/docs
```

```sh
make lint
make test   # тестам API нужна поднятая база с миграциями
```

## Как проверить себя

- `make test` и `make lint` зеленые.
- Повторный `make migrate` ничего не применяет.
- `GET /health/ready` отвечает 200 и версией `vector`.
- `docker compose -p mortgage-assistant stop db`: `/health/live` – 200, `/health/ready` – 503.
- Без `DATABASE_URL` приложение не стартует.
- `GET /loans/1/schedule`: первый платеж 5 505 431 копейка (55 054,31 ₽).

## Деньги

Все суммы – целые копейки, ставка – базисные пункты: 12% годовых = `1200`. Почему так –
[ADR-0001](docs/adr/0001-agent-stack.md).
