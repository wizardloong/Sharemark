FROM python:3.11-slim

WORKDIR /app

# Устанавливаем зависимости
COPY env/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn

# Копируем код приложения
COPY app/ /app
COPY env/ /env

# Запуск через gunicorn с uvicorn-воркером
CMD ["gunicorn", "-c", "/env/guvicorn.conf.py", "main:app", "-k", "uvicorn.workers.UvicornWorker"]
# CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "--wait-for-client", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]