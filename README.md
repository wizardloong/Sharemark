хелоу

это расширение для браузера которое позволит расшаривать папки с закладками

alembic revision --autogenerate -m "init shares table"


# Создать новую миграцию
alembic revision --autogenerate -m "описание изменений"

# Применить все новые миграции
alembic upgrade head

# Откатить на предыдущую версию
alembic downgrade -1

# Посмотреть текущую версию базы
alembic current

# Список всех миграций
alembic history


## Чтобы протестировать

```
git checkout test
git pull

# на всякий случай перебилдить всё
make build
make reup

# запуск тестов!
make test
```
