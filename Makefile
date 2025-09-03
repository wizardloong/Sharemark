# Путь к окружению и Dockerfile
ENV_DIR=env
DOCKER_COMPOSE=docker compose -f $(ENV_DIR)/docker-compose.yml
PROJECT_NAME=bookmarks-sync

# Билд окружения
build:
	$(DOCKER_COMPOSE) build

# Старт окружения
up:
	$(DOCKER_COMPOSE) up -d

# Остановка без удаления данных
stop:
	$(DOCKER_COMPOSE) stop

# Полная остановка и удаление контейнеров
down:
	$(DOCKER_COMPOSE) down

# Перезапуск
reup: down up

# Логи
logs:
	$(DOCKER_COMPOSE) logs -f

# Попасть в контейнер backend
sh:
	$(DOCKER_COMPOSE) exec backend bash

# Попасть в контейнер mysql
dbsh:
	$(DOCKER_COMPOSE) exec mysql bash

# Проверка статуса
ps:
	$(DOCKER_COMPOSE) ps

# Очистка всего (контейнеров, образов, томов)
prune:
	docker system prune -a --volumes --force

# ---- Миграции ----

# Применить все миграции
migrate:
	$(DOCKER_COMPOSE) exec backend bash -c "cd ../$(ENV_DIR) && alembic upgrade head"

# Создать новую миграцию (пример: make newmigrate name=init)
newmigrate:
	$(DOCKER_COMPOSE) exec backend bash -c "cd ../$(ENV_DIR) && alembic revision --autogenerate -m \"$(name)\""

# Откатить одну миграцию назад
backmigrate:
	$(DOCKER_COMPOSE) exec backend bash -c "cd ../$(ENV_DIR) && alembic downgrade -1"

# ---- Контейнеры ----

# Перезагрузить один контейнер (пример: make reload name=backend)
reload:
	$(DOCKER_COMPOSE) restart $(name)
